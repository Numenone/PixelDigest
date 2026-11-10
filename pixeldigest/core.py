"""O motor: roda em segundo plano, liga os gatilhos às ações.

    gatilho (horário, novidade numa fonte, alarme, comando na tela)
        -> processamento (coletar, ordenar, resumir e-mails, achar horário livre)
            -> saída (evento para a tela + Discord + celular + arquivo JSON)

Para não repetir requisições à toa:
- ao abrir, mostra na hora o último resumo salvo e faz UMA busca completa;
- depois, cada fonte tem o seu ritmo (INTERVALOS) e só baixa de novo quando tem
  novidade (o Gmail confere com uma chamada barata; o Slack só pega mensagens novas);
- trocar de tela, abrir as Configurações ou voltar para o resumo não busca nada;
- o botão Atualizar força uma busca completa.

A tela (ui/app.py) e o modo sem tela (--headless) recebem os mesmos eventos pela
fila `eventos`, como tuplas (tipo, dados).
"""
import json
import logging
import os
import queue
import threading
import time
from datetime import datetime

from . import connectors, digest, net, resumo_email
from .config import DATA, ConfigError
from .connectors import weather
from .connectors.demo import pedido_demo
from .meetings import Agendador, eh_pedido, rotulo
from .notify import Notificador
from .phone import OuvinteAlarme
from .scheduler import Agenda, Diario, Intervalo

log = logging.getLogger(__name__)

# De quanto em quanto tempo (segundos) cada tipo de fonte é conferido
INTERVALOS = {"gmail": 120, "slack": 600, "clickup": 900, "zoom": 1800, "microsoft": 900}


class Fonte:
    """Um conector + o que ele trouxe da última vez + quando conferir de novo."""

    def __init__(self, conector):
        self.conector = conector
        self.intervalo = INTERVALOS.get(conector.tipo, 900)
        self.proxima = time.time() + self.intervalo
        self.itens = None          # None = ainda não buscou
        self.erro = None


class Motor(threading.Thread):
    def __init__(self, cfg):
        super().__init__(daemon=True, name="motor")
        self.cfg = cfg
        self.eventos = queue.Queue()      # motor -> tela
        self.comandos = queue.Queue()     # tela -> motor
        self.parar = threading.Event()
        self.nome = cfg["usuario"]["nome"]
        self.conectores, self.erros_config = connectors.montar(cfg)
        self.fontes = [Fonte(c) for c in self.conectores]
        self.cores = {e["nome"]: e.get("cor", "#5ab0ff") for e in cfg["empresas"]}
        self.notificador = Notificador(cfg)
        self.vistos = digest.Vistos()
        self.limpos = self._ler_limpos()      # itens que o usuário tirou do resumo
        self.clima = None
        self.resumo = None
        self.resumos_email = {}               # conta -> resumo dos e-mails (IA)
        self.agendador = self._montar_agendador()
        self.ultima_checagem_teams = datetime.now().astimezone()
        self.alarme = OuvinteAlarme(self._alarme_tocou)

        self.agenda = Agenda()
        h = cfg["horarios"]
        self.agenda.adicionar(Diario("bom_dia", h["inicio_dia"], self.bom_dia))
        self.agenda.adicionar(Diario("fim_do_dia", h["fim_dia"], self.fim_do_dia))
        self.agenda.adicionar(Intervalo("clima", 30 * 60, self.atualizar_clima))
        self.agenda.adicionar(Intervalo("fontes", 30, self.conferir_fontes))
        self.agenda.adicionar(Intervalo("pendentes", 5 * 60, self.notificador.reenviar_pendentes))
        if self.agendador and not cfg["demo"]:
            self.agenda.adicionar(Intervalo("teams", 60, self.checar_teams))

    # ---------- montagem ----------
    def _montar_agendador(self):
        for c in self.conectores:
            if c.tipo == "microsoft" and getattr(c, "usar", {}).get("agendador"):
                return Agendador(self.cfg, c)
        return None

    @staticmethod
    def _ler_limpos():
        try:
            return set(json.loads((DATA / "limpos.json").read_text(encoding="utf-8")))
        except (OSError, ValueError):
            return set()

    def _salvar_limpos(self):
        (DATA / "limpos.json").write_text(json.dumps(sorted(self.limpos)[-3000:]), encoding="utf-8")

    def limpar(self, chaves=None):
        """Tira itens do resumo (todos, ou só as chaves passadas). Novidades continuam chegando."""
        if not self.resumo:
            return
        chaves = set(chaves) if chaves else {i.chave() for i in self.resumo.itens}
        self.limpos |= chaves
        self._salvar_limpos()
        self.resumo.itens = [i for i in self.resumo.itens if i.chave() not in self.limpos]
        self.emitir("resumo", resumo=self.resumo, cores=self.cores)

    def emitir(self, tipo, **dados):
        self.eventos.put((tipo, dados))

    def avisar(self, titulo, texto, cor="#5ab0ff", **kw):
        """Notifica no Discord e no celular sem travar o motor."""
        if self.notificador.ativo():
            threading.Thread(target=self.notificador.enviar, args=(titulo, texto, cor),
                             kwargs=kw, daemon=True).start()

    # ---------- fontes ----------
    def atualizar_fonte(self, fonte, forcar=False):
        """Busca uma fonte. Sem 'forcar', pergunta antes se há novidade. Devolve True se mudou algo."""
        c = fonte.conector
        try:
            if not forcar and fonte.itens is not None and hasattr(c, "tem_novidade") and not c.tem_novidade():
                return False
            fonte.itens, fonte.erro = c.coletar(), None
        except (net.ApiError, ConfigError) as exc:
            fonte.erro = f"{c.nome}: {exc}"
            log.warning("fonte com erro: %s", fonte.erro)
            return True
        except Exception as exc:           # nunca deixa uma fonte derrubar o resto
            log.exception("erro inesperado em %s", c.nome)
            fonte.erro = f"{c.nome}: erro inesperado ({exc})"
            return True
        if c.tipo == "gmail" and c.opcoes.get("resumo_ia", True):
            self.resumir_emails(c)
        return True

    def montar_resumo(self, avisar_urgentes=True):
        """Junta o que cada fonte já tem (sem buscar nada) e manda para a tela."""
        itens = [i for f in self.fontes for i in (f.itens or []) if i.chave() not in self.limpos]
        erros = self.erros_config + [f.erro for f in self.fontes if f.erro]
        self.resumo = digest.Digest(gerado_em=datetime.now(), itens=digest.ordenar(itens), clima=self.clima, erros=erros)
        digest.salvar(self.resumo)
        self.emitir("resumo", resumo=self.resumo, cores=self.cores)
        if avisar_urgentes:
            novos = self.vistos.novos(self.resumo.itens)
            if novos:   # um aviso só com todos os urgentes novos (evita limite do Discord)
                agora = datetime.now().astimezone()
                texto = "\n".join(digest.linha(i, agora) for i in novos[:8])
                self.avisar(f"‼️ {len(novos)} novidade(s) urgente(s)", texto, "#ff5050", tags=["warning"], prioridade=4)
                for item in novos[:3]:
                    self.emitir("toast", titulo=item.empresa, texto=item.titulo, cor=self.cores.get(item.empresa))
        return self.resumo

    def atualizar_resumo(self, avisar_urgentes=True, forcar=True):
        """Busca completa em todas as fontes (ao abrir, no botão Atualizar e no bom dia)."""
        for f in self.fontes:
            self.atualizar_fonte(f, forcar)
            f.proxima = time.time() + f.intervalo
        return self.montar_resumo(avisar_urgentes)

    def conferir_fontes(self):
        """A cada 30 s: confere só as fontes cujo tempo chegou e só remonta se algo mudou."""
        agora, mudou = time.time(), False
        for f in self.fontes:
            if agora >= f.proxima:
                f.proxima = agora + f.intervalo
                mudou |= self.atualizar_fonte(f)
        if mudou:
            self.montar_resumo()

    def resumir_emails(self, conector):
        """Resumo com IA dos e-mails de uma conta, em segundo plano (a chamada demora alguns segundos)."""
        conta = conector.email or conector.empresa
        mensagens = list(conector.mensagens)

        def trabalho():
            r = resumo_email.resumir(conta, mensagens, os.getenv("ANTHROPIC_API_KEY", "").strip(),
                                     self.cfg["ia"]["modelo"])
            r["empresa"] = conector.empresa
            self.resumos_email[conta] = r
            self.emitir("emails", resumos=dict(self.resumos_email))
        threading.Thread(target=trabalho, daemon=True).start()

    # ---------- tarefas ----------
    def atualizar_clima(self):
        try:
            self.clima = weather.buscar(self.cfg["clima"], self.cfg["usuario"]["fuso"])
            self.emitir("clima", clima=self.clima)
        except net.ApiError as exc:
            self.emitir("erro", texto=str(exc))

    def bom_dia(self):
        self.atualizar_clima()
        r = self.atualizar_resumo(avisar_urgentes=False)
        self.vistos.novos(r.itens)       # o que já está no resumo não precisa de aviso separado
        titulo, texto, campos = digest.texto_resumo(r, self.nome)
        self.avisar(titulo, texto, "#ffcc4d", campos=campos, tags=["sunny"])
        self.emitir("bom_dia", resumo=r)

    def fim_do_dia(self):
        r = self.resumo or self.atualizar_resumo(avisar_urgentes=False)
        titulo, texto = digest.texto_fim(r, self.nome)
        self.avisar(titulo, texto, "#6b5bd6", tags=["crescent_moon"])
        self.emitir("fim_do_dia")

    def checar_teams(self):
        desde, self.ultima_checagem_teams = self.ultima_checagem_teams, datetime.now().astimezone()
        try:
            mensagens = self.agendador.conector.mensagens_novas(desde)
        except net.ApiError as exc:
            self.ultima_checagem_teams = desde       # tenta o mesmo intervalo na próxima
            self.emitir("erro", texto=str(exc))
            return
        for msg in mensagens:
            if eh_pedido(msg["texto"], self.cfg["reunioes"]["palavras"]):
                self.tratar_pedido(msg)

    def tratar_pedido(self, msg):
        try:
            pedido = self.agendador.de_mensagem(msg)
        except (net.ApiError, ValueError) as exc:
            self.emitir("erro", texto=f"pedido de reunião de {msg['nome']}: {exc}")
            return
        opcoes = "\n".join(f"• {rotulo(h)}" for h in pedido.horarios)
        self.avisar(f"📅 {pedido.pessoa} pediu reunião", f"\"{pedido.texto[:150]}\"\n\nHorários livres para vocês dois:\n{opcoes}",
                    self.cores.get(pedido.empresa, "#7ad67a"), tags=["calendar"], prioridade=4)
        self.emitir("proposta", proposta={"pessoa": pedido.pessoa, "email": pedido.email,
                                          "assunto": f"Reunião com {pedido.pessoa}", "horarios": pedido.horarios,
                                          "chat_id": pedido.chat_id, "origem": "teams", "texto": pedido.texto})

    def _alarme_tocou(self, titulo, mensagem):
        self.emitir("alarme", titulo=titulo, texto=mensagem)

    # ---------- comandos vindos da tela ----------
    def _comando(self, tipo, dados):
        if tipo == "reuniao":
            if not self.agendador:
                self.emitir("erro", texto="o agendador precisa de uma empresa com Outlook + Teams ativa")
                return
            try:
                proposta = self.agendador.de_comando(dados["texto"])
            except (net.ApiError, ValueError) as exc:
                self.emitir("erro", texto=str(exc))
                return
            proposta["origem"] = "comando"
            self.emitir("proposta", proposta=proposta)
        elif tipo == "confirmar":
            p, h = dados["proposta"], dados["horario"]
            try:
                link = self.agendador.confirmar(p["email"], p["pessoa"], h, p["assunto"])
            except net.ApiError as exc:
                self.emitir("erro", texto=str(exc))
                return
            self.emitir("agendado", pessoa=p["pessoa"], horario=h, assunto=p["assunto"])
            self.avisar("✅ Reunião agendada", f"{p['assunto']}\n{rotulo(h)} com {p['pessoa']}",
                        "#7ad67a", tags=["white_check_mark"], url=link)
        elif tipo == "limpar":
            self.limpar(dados.get("chaves"))
        elif tipo == "atualizar":
            self.atualizar_clima()
            self.atualizar_resumo()
        elif tipo == "demo":
            self._demo(dados["acao"])

    def _demo(self, acao):
        """Atalhos da apresentação: disparam os mesmos caminhos do uso real."""
        if acao == "bom_dia":
            self.bom_dia()
        elif acao == "fim_do_dia":
            self.fim_do_dia()
        elif acao == "pedido" and self.agendador:
            self.tratar_pedido(pedido_demo(datetime.now()))
        elif acao == "alarme":
            self._alarme_tocou("Alarme", "Hora de acordar! (simulado)")

    def encerrar(self):
        """Para o motor e o ouvinte do alarme (usado ao salvar novas configurações)."""
        self.parar.set()
        self.alarme.parar.set()

    # ---------- laço principal ----------
    def run(self):
        if self.cfg["notificacoes"]["ouvir_alarme"] and self.alarme.configurado():
            self.alarme.start()
        anterior = digest.carregar_hoje()          # mostra na hora o último resumo de hoje
        if anterior:
            anterior.itens = [i for i in anterior.itens if i.chave() not in self.limpos]
            self.resumo = anterior
            self.emitir("resumo", resumo=anterior, cores=self.cores)
        self.atualizar_clima()
        self.atualizar_resumo(avisar_urgentes=False)   # a única busca completa (ao abrir)
        while not self.parar.is_set():
            self.agenda.tick(datetime.now().astimezone())
            try:
                tipo, dados = self.comandos.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                self._comando(tipo, dados)
            except Exception as exc:
                log.exception("comando %s falhou", tipo)
                self.emitir("erro", texto=f"erro inesperado: {exc}")
