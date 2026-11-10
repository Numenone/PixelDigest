"""Janela principal (pygame-ce): cenário animado + abas + barra de navegação.

Abas (barra fixa embaixo, na horizontal e na vertical):
- Início:       relógio, clima com previsão, próximo compromisso e contadores do dia;
- Resumo do dia: tudo que chegou das empresas (Slack, ClickUp, e-mails...), com Limpar;
- E-mails:      resumo dos e-mails com IA, uma aba por conta;
- Agenda:       compromissos de hoje e amanhã (Google, Zoom, Outlook) e o agendador;
- Configurar:   abre a tela de Configurações.

Tamanho: o app desenha numa tela lógica (1280x720 na horizontal, 720x1280 na
vertical) e ela é ajustada à janela de qualquer resolução (ui/tela.py). Cada aba
calcula as posições a partir do retângulo de conteúdo, então funciona nas duas.

A tela nunca chama APIs diretamente: ela manda comandos para o Motor e
desenha os eventos que ele devolve (fila). Assim a animação não trava.
"""
import os
import queue
import webbrowser
from datetime import datetime, timedelta

import pygame

from .. import config
from ..config import cor_rgb
from ..meetings import interpretar, rotulo
from ..models import ALTA, URGENTE
from . import effects, font, icons, tela
from .effects import Agendado, Alarme, BomDia, FimDia, Toast
from .scene import PRESETS, Cena
from .settings import TelaConfig

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]
NOMES_SERVICO = {"slack": "Slack", "clickup": "ClickUp", "gmail": "Gmail", "microsoft": "Outlook/Teams",
                 "zoom": "Zoom", "google_agenda": "Google", "outlook": "Outlook"}
COR_PRIO = {URGENTE: (255, 84, 84), ALTA: (255, 176, 60)}
BRANCO, CINZA, AMARELO, VERDE, VERMELHO, AZUL = (240, 242, 248), (150, 156, 178), (255, 205, 80), (90, 200, 110), (255, 95, 95), (90, 170, 255)
SOMBRA = (8, 10, 18)
EXEMPLO = "reunião com Ana amanhã 30min"
ABAS = [("inicio", "Início", "casa"), ("resumo", "Resumo", "lista"), ("emails", "E-mails", "email"),
        ("agenda", "Agenda", "evento"), ("config", "Configurar", "engrenagem")]


_paineis = {}


def painel(superficie, rect, alpha=170, borda=None):
    """Fundo escuro semitransparente. A Surface é reaproveitada (não cria uma nova a cada quadro)."""
    chave = (rect.w, rect.h, alpha)
    caixa = _paineis.get(chave)
    if caixa is None:
        if len(_paineis) > 60:
            _paineis.clear()
        caixa = _paineis[chave] = pygame.Surface(rect.size, pygame.SRCALPHA)
        caixa.fill((10, 12, 22, alpha))
    superficie.blit(caixa, rect.topleft)
    if borda:
        pygame.draw.rect(superficie, borda, rect, 2)


def erro_amigavel(texto):
    """'Minha Empresa / slack: falta a chave PD_...' -> ('Minha Empresa · Slack', 'falta configurar a chave')."""
    origem, _, motivo = texto.partition(": ")
    if " / " in origem:
        empresa, _, tipo = origem.partition(" / ")
        origem = f"{empresa} · {NOMES_SERVICO.get(tipo.split()[0], tipo)}"
    m = motivo.lower()
    if "falta fazer o login" in m:
        motivo = "falta fazer o login"
    elif "falta" in m:
        motivo = "falta configurar a chave"
    elif "acesso negado" in m or "recusad" in m or "invalid_auth" in m:
        motivo = "a chave foi recusada"
    elif "sem resposta" in m or "http 5" in m:
        motivo = "serviço fora do ar ou sem internet"
    return origem, motivo or texto


class App:
    def __init__(self, cfg, motor, janela=None, demo_forcado=False):
        self.cfg = cfg
        self.motor = motor
        self.demo = cfg["demo"]
        self.demo_forcado = demo_forcado      # veio do --demo na linha de comando
        self.nome = cfg["usuario"]["nome"]
        self.janela_fixa = janela is not None  # imagens do README usam uma janela fixa
        self.janela = janela or self._criar_janela()
        pygame.display.set_caption("PixelDigest" + (" (demonstração)" if self.demo else ""))
        self.relogio = pygame.time.Clock()
        self.orientacao = None
        self.cena = None
        self.aplicar_layout()
        self.pagina = "inicio"
        self.efeitos, self.toasts = [], []
        self.resumo, self.cores, self.clima = None, {}, None
        self.proposta = None
        self.texto, self.status = "", ""
        self.preset = None            # demo: clima forçado (F6)
        self.desloc_horas = 0         # demo: adianta o relógio (F7)
        self.rolagem = {"resumo": 0, "emails": 0, "agenda": 0}
        self.alvos = []               # (retângulo, ação) clicáveis deste quadro
        self.dica = None              # texto completo do item embaixo do mouse
        self.config_tela = None       # tela de Configurações, quando aberta
        self.atualizado = None
        self.confirmar_limpar = -99999  # momento do 1º clique em "Limpar" (precisa clicar 2 vezes)
        self.resumos_email = {}       # conta -> {"resumo", "pontos", "gerado", "fonte"}
        self.conta_email = None       # aba escolhida no resumo dos e-mails
        self.rodando = True

    # ---------- janela, orientação e layout (as "media queries") ----------
    def _criar_janela(self):
        t = self.cfg.get("tela", {})
        tamanho = tela.tamanho(t.get("resolucao", "1280x720"))
        if t.get("tela_cheia"):
            return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        return pygame.display.set_mode(tamanho, pygame.RESIZABLE)

    def aplicar_layout(self):
        """Escolhe horizontal/vertical pela configuração (ou pelo formato da janela) e monta as áreas."""
        nova = tela.orientacao(self.cfg.get("tela", {}), self.janela.get_size())
        if nova == self.orientacao:
            return
        self.orientacao = nova
        lw, lh = tela.LOGICO[nova]
        self.tela = pygame.Surface((lw, lh))
        vertical = nova == "vertical"
        self.nav_h = 116 if vertical else 84
        self.topo_h = 64 if vertical else 60
        m = 16 if vertical else 20
        self.r_nav = pygame.Rect(0, lh - self.nav_h, lw, self.nav_h)
        self.r_conteudo = pygame.Rect(m, self.topo_h + 12, lw - 2 * m, lh - self.topo_h - 12 - self.nav_h - 12)
        antigo = self.cena
        self.cena = Cena(lw // 4, lh // 4)
        if antigo is not None:                           # mantém o clima que já estava na tela
            self.cena.vis, self.cena.alvo = antigo.vis, antigo.alvo
            self.cena.nascer, self.cena.por = antigo.nascer, antigo.por
        effects.CX, effects.LARGURA_TELA = lw // 2, lw
        effects.BANNER_Y = 520 if vertical else 250
        Toast.topo_base = self.r_conteudo.y + 6

    def redimensionou(self):
        self.janela = pygame.display.get_surface()
        self.aplicar_layout()

    # ---------- configurações ----------
    def abrir_config(self, primeira_vez=False, aba=0):
        self.config_tela = TelaConfig(self, primeira_vez, self.orientacao)
        self.config_tela.aba = aba

    def recarregar(self):
        """Depois de salvar: lê a configuração nova, ajusta a janela e reinicia o Motor."""
        from ..core import Motor
        tela_antes = dict(self.cfg.get("tela", {}))
        self.motor.encerrar()
        self.cfg = config.carregar(demo=self.demo_forcado)
        self.demo, self.nome = self.cfg["demo"], self.cfg["usuario"]["nome"]
        if not self.janela_fixa and self.cfg.get("tela") != tela_antes:
            self.janela = self._criar_janela()
        self.orientacao = None
        self.aplicar_layout()
        pygame.display.set_caption("PixelDigest" + (" (demonstração)" if self.demo else ""))
        self.resumo, self.clima, self.proposta, self.preset = None, None, None, None
        self.motor = Motor(self.cfg)
        self.motor.start()
        self.toasts.append(Toast("Configurações salvas", "carregando as informações…", VERDE))

    # ---------- eventos que vêm do Motor ----------
    def receber(self):
        while True:
            try:
                tipo, d = self.motor.eventos.get_nowait()
            except queue.Empty:
                return
            if tipo == "clima":
                self.clima = d["clima"]
                if not self.preset:
                    self.cena.definir_clima(clima=self.clima)
            elif tipo == "resumo":
                self.resumo, self.cores = d["resumo"], d["cores"]
                self.atualizado = datetime.now()
                self.status = ""
            elif tipo == "bom_dia":
                self.efeitos.append(BomDia(self.nome, len(d["resumo"].itens)))
            elif tipo == "fim_do_dia":
                self.cena.acender_janelas()
                self.efeitos.append(FimDia())
            elif tipo == "toast":
                self.toasts.append(Toast(d["titulo"], d["texto"], cor_rgb(d.get("cor") or "#ff5050")))
            elif tipo == "proposta":
                self.proposta = d["proposta"]
                self.pagina = "agenda"
                self.status = ""
                if d["proposta"].get("origem") == "teams":
                    self.toasts.append(Toast("Pedido de reunião no Teams", d["proposta"]["pessoa"], (122, 214, 122)))
            elif tipo == "agendado":
                self.proposta = None
                self.status = ""
                self.efeitos.append(Agendado(d["pessoa"].split()[0], rotulo(d["horario"]), d["assunto"]))
            elif tipo == "emails":
                self.resumos_email = d["resumos"]
                if self.conta_email not in self.resumos_email:
                    self.conta_email = next(iter(self.resumos_email), None)
            elif tipo == "alarme":
                self.efeitos.append(Alarme(d["titulo"], d["texto"]))
            elif tipo == "erro":
                self.status = ""
                self.toasts.append(Toast("Não deu certo", d["texto"], VERMELHO))

    # ---------- teclado e mouse ----------
    def tratar(self, ev):
        alarme = next((e for e in self.efeitos if isinstance(e, Alarme)), None)
        if ev.type == pygame.QUIT:
            self.rodando = False
        elif self.config_tela:
            self.config_tela.evento(ev)           # com as Configurações abertas, o teclado é delas
            if not self.config_tela.aberta:
                self.config_tela = None
        elif alarme and ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            alarme.fechar()                       # qualquer tecla desliga o alarme
        elif ev.type == pygame.TEXTINPUT:
            if self.pagina != "agenda" or not self.motor.agendador:
                return                            # só a Agenda tem campo de texto
            if self.proposta and not self.texto and ev.text in "123":
                return                            # 1-3 escolhe horário (tratado no KEYDOWN)
            self.texto = (self.texto + ev.text)[:90]
        elif ev.type == pygame.MOUSEWHEEL and self.r_conteudo.collidepoint(tela.mouse_pos()):
            if self.pagina in self.rolagem:
                self.rolagem[self.pagina] = max(0, self.rolagem[self.pagina] - ev.y * 40)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for rect, acao in reversed(self.alvos):   # o que foi desenhado por último está por cima
                if rect.collidepoint(ev.pos):
                    acao()
                    break
        elif ev.type == pygame.KEYDOWN:
            self.tecla(ev)

    def ir(self, pagina):
        if pagina == "config":
            self.abrir_config()
        else:
            self.pagina = pagina

    def tecla(self, ev):
        k = ev.key
        digitando = self.pagina == "agenda" and self.texto
        if k == pygame.K_ESCAPE:
            self.proposta, self.texto = None, ""
        elif k == pygame.K_BACKSPACE and digitando:
            self.texto = self.texto[:-1]
        elif k == pygame.K_v and ev.mod & pygame.KMOD_CTRL and self.pagina == "agenda":
            from .widgets import area_de_transferencia
            self.texto = (self.texto + area_de_transferencia().strip())[:90]
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER) and digitando:
            self.motor.comandos.put(("reuniao", {"texto": self.texto.strip()}))
            self.status = "procurando horários livres…"
            self.texto = ""
        elif self.proposta and not self.texto and pygame.K_1 <= k <= pygame.K_3:
            i = k - pygame.K_1
            if i < len(self.proposta["horarios"]):
                self.confirmar(self.proposta["horarios"][i])
        elif k in (pygame.K_LEFT, pygame.K_RIGHT) and not digitando:
            abas = [a for a, _, _ in ABAS if a != "config"]
            i = abas.index(self.pagina) + (1 if k == pygame.K_RIGHT else -1)
            self.pagina = abas[i % len(abas)]
        elif k == pygame.K_F10:
            self.abrir_config()
        elif k == pygame.K_F5:
            self.atualizar()
        elif self.demo:
            acoes = {pygame.K_F1: "bom_dia", pygame.K_F2: "fim_do_dia", pygame.K_F3: "pedido", pygame.K_F4: "alarme"}
            if k in acoes:
                self.motor.comandos.put(("demo", {"acao": acoes[k]}))
            elif k == pygame.K_F6:
                nomes = list(PRESETS) + [None]
                self.preset = nomes[(nomes.index(self.preset) + 1) % len(nomes)]
                self.cena.definir_clima(clima=self.clima, preset=self.preset)
                self.toasts.append(Toast("Clima da demonstração", self.preset or "clima real", AZUL))
            elif k == pygame.K_F7:
                self.desloc_horas = (self.desloc_horas + 3) % 24

    def limpar_tudo(self):
        if pygame.time.get_ticks() - self.confirmar_limpar < 4000:
            self.motor.comandos.put(("limpar", {}))
            self.confirmar_limpar = -99999
            self.rolagem["resumo"] = 0
            self.toasts.append(Toast("Resumo limpo", "os itens novos continuam aparecendo aqui", VERDE))
        else:
            self.confirmar_limpar = pygame.time.get_ticks()

    def dispensar(self, item):
        self.motor.comandos.put(("limpar", {"chaves": [item.chave()]}))
        if self.resumo:
            self.resumo.itens = [i for i in self.resumo.itens if i is not item]   # some na hora

    def atualizar(self):
        self.motor.comandos.put(("atualizar", {}))
        self.status = "atualizando…"

    def confirmar(self, horario):
        self.motor.comandos.put(("confirmar", {"proposta": self.proposta, "horario": horario}))
        self.status = "agendando…"

    # ---------- utilidades de desenho ----------
    def agora(self):
        return datetime.now().astimezone() + timedelta(hours=self.desloc_horas)

    def escrever(self, texto, x, y, escala=2, cor=BRANCO, familia="texto", sombra=SOMBRA):
        surf = font.render(texto, escala, cor, shadow=sombra, familia=familia)
        self.tela.blit(surf, (x, y))
        return surf.get_width()

    def centralizado(self, texto, cx, y, escala=2, cor=BRANCO, familia="texto", sombra=SOMBRA):
        surf = font.render(texto, escala, cor, shadow=sombra, familia=familia)
        self.tela.blit(surf, (cx - surf.get_width() // 2, y))

    def botao(self, rect, texto, cor, acao, cheio=False):
        sobre = rect.collidepoint(tela.mouse_pos())
        painel(self.tela, rect, 235 if sobre else 190, cor)
        if sobre or cheio:
            pygame.draw.rect(self.tela, cor, rect.inflate(-6, -6))
        t = font.render(texto, 2, (12, 14, 24) if (sobre or cheio) else cor)
        self.tela.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))
        self.alvos.append((rect, acao))

    def botao_pequeno(self, rect, texto, cor, acao):
        sobre = rect.collidepoint(tela.mouse_pos())
        pygame.draw.rect(self.tela, cor if sobre else (24, 28, 44), rect)
        pygame.draw.rect(self.tela, cor, rect, 1)
        t = font.render(texto, 1, (12, 14, 24) if sobre else cor)
        self.tela.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))
        self.alvos.append((rect, acao))

    def paragrafo(self, texto, x, y, largura, escala=2, cor=(220, 224, 236), max_linhas=99):
        linhas = font.wrap(texto, largura, escala)
        if len(linhas) > max_linhas:
            linhas = linhas[:max_linhas - 1] + [font.cortar(" ".join(linhas[max_linhas - 1:]), largura, escala)]
        for linha in linhas:
            self.escrever(linha, x, y, escala, cor, sombra=None)
            y += font.altura(escala)
        return y

    def cabecalho_painel(self, area, titulo, direita=""):
        """Título da aba dentro do painel + texto à direita. Devolve o y onde começa o conteúdo."""
        painel(self.tela, area, 175 + int(55 * self.cena.escuro))
        self.escrever(titulo, area.x + 16, area.y + 14, 2, BRANCO, "titulo", sombra=None)
        if direita:
            t = font.render(direita, 1, CINZA)
            self.tela.blit(t, (area.right - t.get_width() - 16, area.y + 16))
        return area.y + 48

    def noite(self, agora):
        c = self.clima
        if c and c.nascer and c.por_do_sol:
            hora = agora.replace(tzinfo=None)
            return not (c.nascer <= hora <= c.por_do_sol)
        return agora.hour < 6 or agora.hour >= 18

    def codigo_clima(self):
        if self.preset:
            return {"sol": 0, "nublado": 3, "chuva": 63, "tempestade": 95}[self.preset]
        return self.clima.codigo if self.clima else 0

    def data_extenso(self, agora):
        return f"{DIAS[agora.weekday()].capitalize()}, {agora.day} de {MESES[agora.month - 1]}"

    # ---------- topo (abas internas) ----------
    def desenhar_topo(self, agora):
        lw = self.tela.get_width()
        painel(self.tela, pygame.Rect(0, 0, lw, self.topo_h), 185)
        pygame.draw.line(self.tela, (60, 70, 100), (0, self.topo_h), (lw, self.topo_h), 2)
        w = self.escrever(f"{agora:%H:%M}", 18, 10, 4, BRANCO, "titulo")
        self.escrever(self.data_extenso(agora), 26 + w, 20 if self.orientacao == "horizontal" else 14, 1, (200, 206, 222))
        x = lw - 18
        if self.clima or self.preset:
            temp = f"{self.clima.temperatura:.0f}°" if self.clima and not self.preset else ""
            t = font.render(temp, 3, BRANCO, familia="titulo")
            x -= t.get_width()
            self.tela.blit(t, (x, 16))
            x -= 46
            self.tela.blit(icons.clima(self.codigo_clima(), self.noite(agora), 40), (x, 10))
        if self.status:
            s = font.render(self.status, 1, AMARELO)
            self.tela.blit(s, (x - s.get_width() - 16, 22))

    # ---------- aba Início ----------
    def proximo_evento(self, agora):
        if not self.resumo:
            return None
        futuros = [i for i in self.resumo.itens if i.tipo == "evento" and i.quando and i.quando > agora
                   and i.quando.date() == agora.date()]
        return min(futuros, key=lambda i: i.quando, default=None)

    def contadores(self, agora):
        itens = self.resumo.itens if self.resumo else []
        urgentes = sum(1 for i in itens if i.prioridade >= URGENTE)
        eventos = sum(1 for i in itens if i.tipo == "evento" and i.quando and i.quando.date() == agora.date())
        tarefas = sum(1 for i in itens if i.tipo == "tarefa")
        importantes = sum(1 for r in self.resumos_email.values() for p in r.get("pontos", []) if p.get("prioridade") == "alta")
        return [("Urgentes", urgentes, VERMELHO, "resumo"), ("E-mails importantes", importantes, AMARELO, "emails"),
                ("Compromissos hoje", eventos, AZUL, "agenda"), ("Tarefas abertas", tarefas, VERDE, "resumo")]

    def pagina_inicio(self, agora):
        c = self.r_conteudo
        vertical = self.orientacao == "vertical"
        if vertical:
            cx = c.centerx
            heroi = pygame.Rect(c.x, c.y, c.w, 420)
            painel(self.tela, heroi, 120)
            self.centralizado(f"{agora:%H:%M}", cx, heroi.y + 24, 10, BRANCO, "titulo")
            self.centralizado(self.data_extenso(agora), cx, heroi.y + 134, 3, (220, 224, 236))
            self.bloco_clima(pygame.Rect(c.x + 20, heroi.y + 190, c.w - 40, 220), agora, previsao=4)
            y = heroi.bottom + 14
            y = self.cartao_proximo(pygame.Rect(c.x, y, c.w, 92), agora) + 14
            self.blocos_contadores(pygame.Rect(c.x, y, c.w, 250), agora, 2)
            self.linha_status(pygame.Rect(c.x, y + 264, c.w, 56))
        else:
            esquerda = pygame.Rect(c.x, c.y, 640, c.h)
            painel(self.tela, esquerda, 120)
            self.escrever(f"{agora:%H:%M}", esquerda.x + 30, esquerda.y + 24, 10, BRANCO, "titulo")
            self.escrever(self.data_extenso(agora), esquerda.x + 36, esquerda.y + 134, 3, (220, 224, 236))
            self.bloco_clima(pygame.Rect(esquerda.x + 30, esquerda.y + 196, esquerda.w - 60, 300), agora, previsao=6)
            direita = pygame.Rect(c.x + 660, c.y, c.w - 660, c.h)
            y = self.cartao_proximo(pygame.Rect(direita.x, direita.y, direita.w, 92), agora) + 14
            self.blocos_contadores(pygame.Rect(direita.x, y, direita.w, 260), agora, 2)
            self.linha_status(pygame.Rect(direita.x, y + 276, direita.w, 56))
        if self.demo:
            dica = "DEMO · F1 bom dia · F2 18h · F3 pedido · F4 alarme · F6 clima · F7 +3h · setas trocam de aba"
            self.centralizado(font.cortar(dica, c.w - 20, 1), c.centerx, c.bottom - 22, 1, BRANCO)

    def bloco_clima(self, r, agora, previsao):
        if self.preset:
            self.tela.blit(icons.clima(self.codigo_clima(), self.noite(agora), 80), (r.x, r.y))
            self.escrever(self.preset.capitalize(), r.x + 96, r.y + 14, 5, BRANCO, "titulo")
            self.escrever("clima da demonstração (F6 troca)", r.x + 98, r.y + 66, 1, CINZA)
            return
        if not self.clima:
            self.escrever("buscando o clima…", r.x, r.y + 20, 2, CINZA)
            return
        cl = self.clima
        self.tela.blit(icons.clima(cl.codigo, self.noite(agora), 80), (r.x, r.y))
        w = self.escrever(f"{cl.temperatura:.0f}°", r.x + 96, r.y + 6, 7, BRANCO, "titulo")
        self.escrever(font.cortar(cl.descricao.capitalize(), r.w - 120 - w, 3), r.x + 112 + w, r.y + 14, 3)
        self.escrever(f"mín {cl.minima:.0f}° · máx {cl.maxima:.0f}° · chuva {cl.prob_chuva}%", r.x + 112 + w, r.y + 50, 1, (205, 210, 226))
        self.escrever(font.cortar(cl.cidade, r.w - 100, 1), r.x + 98, r.y + 76, 1, CINZA)
        y = r.y + 112
        n = min(previsao, len(cl.proximas))
        if not n:
            return
        passo = r.w // n
        for i, (hora, temp, cod, prob) in enumerate(cl.proximas[:n]):
            cx = r.x + i * passo + passo // 2
            self.centralizado(hora, cx, y, 1, CINZA, sombra=None)
            hora_n = int(hora[:2])
            self.tela.blit(icons.clima(cod, hora_n < 6 or hora_n >= 19, 40), (cx - 20, y + 22))
            if temp is not None:
                self.centralizado(f"{temp:.0f}°", cx, y + 66, 2, BRANCO, sombra=None)
            self.centralizado(f"{prob}%", cx, y + 92, 1, AZUL if prob >= 30 else CINZA, sombra=None)

    def cartao_proximo(self, r, agora):
        painel(self.tela, r, 190)
        prox = self.proximo_evento(agora)
        self.tela.blit(icons.item("evento", 36), (r.x + 16, r.y + 16))
        self.escrever("Próximo compromisso", r.x + 64, r.y + 12, 1, CINZA, sombra=None)
        if not prox:
            self.escrever("Nada mais na agenda hoje", r.x + 64, r.y + 44, 2, BRANCO, sombra=None)
        else:
            falta = int((prox.quando - agora).total_seconds() // 60)
            cor = VERMELHO if falta <= 15 else (AMARELO if falta <= 60 else VERDE)
            pygame.draw.rect(self.tela, cor, r, 2)
            quando = f"em {falta} min" if falta < 60 else f"às {prox.quando:%H:%M}"
            t = font.render(quando, 3, cor)
            self.tela.blit(t, (r.right - t.get_width() - 16, r.y + 38))
            self.escrever(font.cortar(prox.titulo, r.w - t.get_width() - 100, 2), r.x + 64, r.y + 44, 2, BRANCO, sombra=None)
            self.alvos.append((r, lambda: self.ir("agenda")))
        return r.bottom

    def blocos_contadores(self, r, agora, colunas):
        dados = self.contadores(agora)
        linhas = (len(dados) + colunas - 1) // colunas
        w = (r.w - (colunas - 1) * 14) // colunas
        h = (r.h - (linhas - 1) * 14) // linhas
        mouse = tela.mouse_pos()
        for i, (rot, n, cor, destino) in enumerate(dados):
            b = pygame.Rect(r.x + (i % colunas) * (w + 14), r.y + (i // colunas) * (h + 14), w, h)
            painel(self.tela, b, 215 if b.collidepoint(mouse) else 185)
            pygame.draw.rect(self.tela, cor, (b.x, b.y, 6, b.h))
            self.escrever(str(n), b.x + 24, b.y + 14, 6, cor if n else CINZA, "titulo", sombra=None)
            self.escrever(font.cortar(rot, b.w - 40, 2), b.x + 24, b.bottom - 36, 2, BRANCO, sombra=None)
            self.alvos.append((b, lambda d=destino: self.ir(d)))

    def linha_status(self, r):
        n = self.cfg["notificacoes"]
        canais = [("Discord", n["discord"] and bool(os.getenv("DISCORD_WEBHOOK_URL"))),
                  ("Celular", n["celular"] and bool(os.getenv("NTFY_TOPIC"))),
                  ("Alarme", n["ouvir_alarme"] and getattr(self.motor.alarme, "conectado", False))]
        x = r.x + 4
        for nome, ligado in canais:
            pygame.draw.rect(self.tela, VERDE if ligado else (90, 94, 110), (x, r.y + 8, 10, 10))
            x += 16 + self.escrever(nome, x + 16, r.y + 2, 1, BRANCO if ligado else CINZA) + 18
        info = "demonstração" if self.demo else (f"atualizado às {self.atualizado:%H:%M}" if self.atualizado else "carregando…")
        self.escrever(self.status or info, r.x + 4, r.y + 30, 1, AMARELO if self.status else CINZA)
        self.botao(pygame.Rect(r.right - 150, r.y, 150, 46), "Atualizar", AZUL, self.atualizar)

    # ---------- aba Resumo do dia ----------
    def pagina_resumo(self, agora):
        area = self.r_conteudo
        itens = self.resumo.itens if self.resumo else []
        urg = sum(1 for i in itens if i.prioridade >= URGENTE)
        y = self.cabecalho_painel(area, "RESUMO DO DIA")
        if self.resumo and itens:
            confirmando = pygame.time.get_ticks() - self.confirmar_limpar < 4000
            rot = "Confirmar?" if confirmando else "Limpar tudo"
            w = font.largura(rot, 1) + 24
            self.botao_pequeno(pygame.Rect(area.right - w - 14, area.y + 10, w, 28), rot,
                               VERMELHO if confirmando else CINZA, self.limpar_tudo)
            t = font.render(f"{len(itens)} itens" + (f" · {urg} urgentes" if urg else ""), 1, VERMELHO if urg else CINZA)
            self.tela.blit(t, (area.right - w - 28 - t.get_width(), area.y + 16))
        if not self.resumo:
            self.escrever("carregando…", area.x + 16, y, 2, CINZA)
            return
        if not self.cfg["empresas"] and not self.demo:
            y = self.paragrafo("Nenhuma empresa configurada ainda. Adicione as suas e cole as chaves de API "
                               "nas Configurações.", area.x + 16, y + 6, area.w - 32)
            self.botao(pygame.Rect(area.x + 16, y + 14, 280, 44), "Abrir configurações", AMARELO, lambda: self.abrir_config(aba=4))
            return
        erros = self.resumo.erros
        rodape = (44 + 22 * min(3, len(erros))) if erros else 0
        self.desenhar_lista(pygame.Rect(area.x, y, area.w, area.bottom - y - rodape - 6), agora)
        if erros:
            self.desenhar_erros(pygame.Rect(area.x, area.bottom - rodape, area.w, rodape), erros)

    def desenhar_lista(self, lista, agora):
        """Itens agrupados por empresa, com ícone, horário e rolagem."""
        x = lista.x + 16
        linhas = []
        for empresa, itens in self.resumo.por_empresa().items():
            linhas.append(("empresa", empresa, itens))
            linhas += [("item", empresa, it) for it in itens]
        if not linhas:
            self.paragrafo("Nada por aqui agora. Quando chegar algo das suas empresas, aparece nesta lista.",
                           x, lista.y + 8, lista.w - 32, 2, CINZA)
            return
        altura_total = sum(36 if t == "empresa" else 32 for t, _, _ in linhas)
        self.rolagem["resumo"] = max(0, min(self.rolagem["resumo"], altura_total - lista.h))
        self.tela.set_clip(lista)
        y = lista.y - self.rolagem["resumo"]
        mouse = tela.mouse_pos()
        for tipo, empresa, dado in linhas:
            if y > lista.bottom:
                break
            cor = cor_rgb(self.cores.get(empresa, "#5ab0ff"))
            if tipo == "empresa":
                if y + 36 >= lista.y:
                    pygame.draw.rect(self.tela, cor, (x - 6, y + 2, lista.w - 26, 28))
                    self.escrever(f"{empresa} · {len(dado)}", x + 2, y + 5, 2, (12, 14, 24), sombra=None)
                y += 36
                continue
            it = dado
            if y + 32 < lista.y:
                y += 32
                continue
            linha = pygame.Rect(x - 6, y, lista.w - 26, 30)
            q = self.quando_curto(it, agora)
            largura_txt = linha.w - 48 - (font.largura(q, 1) + 14 if q else 0)
            if linha.collidepoint(mouse) and lista.collidepoint(mouse):
                pygame.draw.rect(self.tela, (40, 48, 72), linha)
                if it.url:
                    self.alvos.append((linha.clip(lista), lambda u=it.url: webbrowser.open(u)))
                if font.cortar(it.titulo, largura_txt, 2) != it.titulo or it.detalhe:
                    self.dica = (it.titulo + (f"  ·  {it.detalhe}" if it.detalhe else ""), mouse)
                fechar = pygame.Rect(linha.right - 26, y + 4, 22, 22).clip(lista)
                q = ""
                pygame.draw.rect(self.tela, (70, 40, 50), fechar)
                self.escrever("×", fechar.x + 6, fechar.y + 1, 2, VERMELHO, sombra=None)
                self.alvos.append((fechar, lambda i=it: self.dispensar(i)))
            pygame.draw.rect(self.tela, COR_PRIO.get(it.prioridade, (70, 74, 92)), (x - 6, y + 3, 4, 24))
            self.tela.blit(icons.item(it.tipo, 22), (x + 2, y + 4))
            self.escrever(font.cortar(it.titulo, largura_txt, 2), x + 30, y + 4, 2, BRANCO, sombra=None)
            if q:
                t = font.render(q, 1, VERMELHO if q == "atrasado" else CINZA)
                self.tela.blit(t, (linha.right - t.get_width() - 6, y + 8))
            y += 32
        self.tela.set_clip(None)
        self.barra_rolagem(lista, altura_total, self.rolagem["resumo"])

    def barra_rolagem(self, area, altura_total, rolagem):
        if altura_total > area.h:
            prop = area.h / altura_total
            pygame.draw.rect(self.tela, (90, 100, 130),
                             (area.right - 8, area.y + int(rolagem * prop), 4, max(20, int(area.h * prop))))

    @staticmethod
    def quando_curto(it, agora):
        """Horário curto do item: 14:30, amanhã, 12/11 ou atrasado."""
        if not it.quando:
            return ""
        dias = (it.quando.date() - agora.date()).days
        if dias == 0:
            return it.quando.strftime("%H:%M")
        if dias < 0:
            return "atrasado" if it.tipo == "tarefa" else it.quando.strftime("%d/%m")
        return "amanhã" if dias == 1 else it.quando.strftime("%d/%m")

    def desenhar_erros(self, rect, erros):
        pygame.draw.line(self.tela, (80, 60, 50), (rect.x + 12, rect.y), (rect.right - 12, rect.y), 1)
        x = rect.x + 16
        self.escrever(f"{len(erros)} fonte(s) com problema", x, rect.y + 10, 1, AMARELO, sombra=None)
        for i, e in enumerate(erros[:3]):
            origem, motivo = erro_amigavel(e)
            self.escrever(font.cortar(f"{origem}: {motivo}", rect.w - 32, 1), x, rect.y + 38 + i * 22, 1, (255, 200, 150), sombra=None)
        self.botao(pygame.Rect(rect.right - 130, rect.y + 6, 114, 34), "Resolver", AMARELO, lambda: self.abrir_config(aba=5))

    # ---------- aba E-mails ----------
    def pagina_emails(self, agora):
        area = self.r_conteudo
        y = self.cabecalho_painel(area, "RESUMO DOS E-MAILS")
        x = area.x + 16
        if not self.resumos_email:
            y = self.paragrafo("Os e-mails aparecem aqui depois que você conecta uma conta Gmail "
                               "(Configurações > Chaves de API > Fazer login).", x, y + 6, area.w - 32, 2, CINZA)
            self.botao(pygame.Rect(x, y + 14, 280, 44), "Abrir configurações", AMARELO, lambda: self.abrir_config(aba=5))
            return
        # uma "aba" por conta de e-mail (quebra linha se não couber)
        bx, by = x, y
        for conta in self.resumos_email:
            rot = font.cortar(conta, area.w - 60, 1)
            w = font.largura(rot, 1) + 26
            if bx + w > area.right - 16:
                bx, by = x, by + 36
            self.botao_pequeno(pygame.Rect(bx, by, w, 30), rot, AZUL if conta == self.conta_email else CINZA,
                               lambda c=conta: (setattr(self, "conta_email", c), self.rolagem.__setitem__("emails", 0)))
            bx += w + 8
        y = by + 44
        r = self.resumos_email.get(self.conta_email) or next(iter(self.resumos_email.values()))
        fonte = "resumo com IA" if r.get("fonte") == "ia" else "resumo simples (sem IA)"
        y = self.paragrafo(f"{r.get('resumo', '')}  ·  {fonte} às {r.get('gerado', '--:--')}", x, y, area.w - 32, 1, (200, 206, 222), 3) + 10
        lista = pygame.Rect(area.x, y, area.w, area.bottom - y - 8)
        cores = {"alta": VERMELHO, "media": AMARELO, "baixa": CINZA}
        self.tela.set_clip(lista)
        yy = lista.y - self.rolagem["emails"]
        inicio = yy
        for p in r.get("pontos", []):
            pygame.draw.rect(self.tela, cores.get(p.get("prioridade"), CINZA), (x, yy + 6, 10, 10))
            self.escrever(font.cortar(p.get("titulo", ""), area.w - 64, 2), x + 22, yy, 2, BRANCO, sombra=None)
            yy = self.paragrafo(p.get("detalhe", ""), x + 22, yy + 28, area.w - 64, 1, (205, 210, 226), 2)
            if p.get("acao"):
                self.escrever(font.cortar("→ " + p["acao"], area.w - 64, 1), x + 22, yy + 2, 1, AMARELO, sombra=None)
                yy += 22
            yy += 14
            pygame.draw.line(self.tela, (50, 56, 78), (x, yy - 7), (area.right - 16, yy - 7), 1)
        self.tela.set_clip(None)
        total = yy - inicio
        self.rolagem["emails"] = max(0, min(self.rolagem["emails"], max(0, total - lista.h)))
        self.barra_rolagem(lista, total, self.rolagem["emails"])

    # ---------- aba Agenda ----------
    def pagina_agenda(self, agora):
        area = self.r_conteudo
        y = self.cabecalho_painel(area, "AGENDA", "hoje e amanhã")
        x = area.x + 16
        tem_agendador = bool(self.motor.agendador)
        barra_h = 96 if tem_agendador else 0
        eventos = sorted([i for i in (self.resumo.itens if self.resumo else []) if i.tipo == "evento" and i.quando],
                         key=lambda i: i.quando)
        lista = pygame.Rect(area.x, y, area.w, area.bottom - y - barra_h - 8)
        self.tela.set_clip(lista)
        yy = lista.y - self.rolagem["agenda"]
        inicio = yy
        mouse = tela.mouse_pos()
        if not eventos:
            yy = self.paragrafo("Nenhum compromisso hoje nem amanhã. Conecte o Google Agenda ou o Zoom nas Configurações.",
                                x, yy + 6, area.w - 32, 2, CINZA)
        dia_atual = None
        for ev in eventos:
            dias = (ev.quando.date() - agora.date()).days
            if dias != dia_atual:
                dia_atual = dias
                rot = "HOJE" if dias == 0 else ("AMANHÃ" if dias == 1 else ev.quando.strftime("%d/%m"))
                self.escrever(rot, x, yy + 6, 2, AZUL, "titulo", sombra=None)
                yy += 36
            linha = pygame.Rect(x - 6, yy, area.w - 26, 52)
            passou = ev.quando < agora
            if linha.collidepoint(mouse) and lista.collidepoint(mouse):
                pygame.draw.rect(self.tela, (40, 48, 72), linha)
                if ev.url:
                    self.alvos.append((linha.clip(lista), lambda u=ev.url: webbrowser.open(u)))
            self.escrever(ev.quando.strftime("%H:%M"), x + 4, yy + 12, 3, CINZA if passou else BRANCO, "titulo", sombra=None)
            self.tela.blit(icons.item("evento", 26), (x + 104, yy + 12))
            fonte = NOMES_SERVICO.get(ev.fonte, ev.fonte) + (f" · {ev.detalhe}" if ev.detalhe and ev.detalhe not in ("Zoom",) else "")
            falta = int((ev.quando - agora).total_seconds() // 60)
            marca = f"em {falta} min" if 0 <= falta < 120 else ""
            larg = linha.w - 160 - (font.largura(marca, 2) + 16 if marca else 0)
            self.escrever(font.cortar(ev.titulo, larg, 2), x + 142, yy + 6, 2, CINZA if passou else BRANCO, sombra=None)
            self.escrever(font.cortar(f"{ev.empresa} · {fonte}", larg, 1), x + 142, yy + 30, 1, CINZA, sombra=None)
            if marca:
                t = font.render(marca, 2, VERMELHO if falta <= 15 else AMARELO)
                self.tela.blit(t, (linha.right - t.get_width() - 8, yy + 14))
            yy += 58
        self.tela.set_clip(None)
        total = yy - inicio
        self.rolagem["agenda"] = max(0, min(self.rolagem["agenda"], max(0, total - lista.h)))
        self.barra_rolagem(lista, total, self.rolagem["agenda"])
        if tem_agendador:
            self.desenhar_barra(pygame.Rect(area.x + 12, area.bottom - 60, area.w - 24, 50))
        if self.proposta:
            self.desenhar_proposta()

    def desenhar_proposta(self):
        p = self.proposta
        c = self.r_conteudo
        largura = min(c.w - 40, 760)
        area = pygame.Rect(c.centerx - largura // 2, c.y + 70, largura, 330 if self.orientacao == "vertical" else 250)
        painel(self.tela, area, 235, (122, 214, 122))
        x, y = area.x + 20, area.y + 16
        if p.get("origem") == "teams":
            self.tela.blit(icons.item("mensagem", 30), (x, y))
            self.escrever(font.cortar(f"{p['pessoa']} pediu uma reunião", area.w - 80, 3), x + 40, y, 3, (122, 214, 122), sombra=None)
            y = self.paragrafo(f"“{p.get('texto', '')}”", x, y + 40, area.w - 40, 1, max_linhas=2)
        else:
            self.tela.blit(icons.item("evento", 30), (x, y))
            self.escrever(font.cortar(p["assunto"], area.w - 80, 3), x + 40, y, 3, (122, 214, 122), sombra=None)
            self.escrever(font.cortar(f"com {p['pessoa']} ({p['email']}) · {p.get('duracao', 30)} min", area.w - 40, 1),
                          x, y + 40, 1, (220, 224, 236), sombra=None)
            y += 62
        self.escrever("Horários livres para vocês dois:", x, y + 8, 2, (200, 206, 222), sombra=None)
        y += 40
        colunas = 1 if self.orientacao == "vertical" else 3
        w = (area.w - 40 - (colunas - 1) * 12) // colunas
        for i, h in enumerate(p["horarios"][:3]):
            r = pygame.Rect(x + (i % colunas) * (w + 12), y + (i // colunas) * 58, w, 52)
            sobre = r.collidepoint(tela.mouse_pos())
            pygame.draw.rect(self.tela, (70, 150, 80) if sobre else (30, 64, 40), r)
            pygame.draw.rect(self.tela, (122, 214, 122), r, 2)
            self.escrever(f"{i + 1}", r.x + 12, r.y + 12, 3, AMARELO, "titulo", sombra=None)
            self.escrever(rotulo(h), r.x + 44, r.y + 6, 2, BRANCO, sombra=None)
            self.escrever(f"até {h.fim:%H:%M}", r.x + 44, r.y + 30, 1, CINZA, sombra=None)
            self.alvos.append((r, lambda h=h: self.confirmar(h)))
        self.escrever("1, 2 ou 3 (ou clique) para agendar · Esc ignora", x, area.bottom - 26, 1, CINZA, sombra=None)

    def desenhar_barra(self, r):
        """Campo 'reunião com …' + prévia do que o programa entendeu."""
        painel(self.tela, r, 215, AZUL)
        self.escrever(">", r.x + 12, r.y + 10, 3, AZUL, "titulo", sombra=None)
        if self.texto:
            t = font.cauda(self.texto, r.w - 70, 2)
            w = self.escrever(t, r.x + 42, r.y + 14, 2, BRANCO, sombra=None)
            if pygame.time.get_ticks() // 450 % 2:
                pygame.draw.rect(self.tela, AZUL, (r.x + 46 + w, r.y + 12, 3, r.h - 24))
        else:
            self.escrever(EXEMPLO, r.x + 42, r.y + 14, 2, (100, 110, 140), sombra=None)
        acima = r.y - 26
        if self.texto:
            p = interpretar(self.texto, self.agora().date(), self.cfg["reunioes"]["duracao_padrao"])
            if p:
                partes = [p["pessoa"], f"{p['dia']:%d/%m}" if p["dia"] else "próximos dias", f"{p['duracao']} min"]
                if p["hora"]:
                    partes.insert(2, f"{p['hora']:%H:%M}")
                texto = "  ·  ".join(partes) + "  (Enter busca horários)"
                self.escrever(font.cortar(texto, r.w, 1), r.x + 4, acima, 1, VERDE, sombra=None)
            else:
                self.escrever(font.cortar("Comece com: reunião com <pessoa> [amanhã | sexta] [às 14h] [45min]", r.w, 1),
                              r.x + 4, acima, 1, CINZA, sombra=None)

    # ---------- barra de navegação ----------
    def desenhar_nav(self):
        r = self.r_nav
        painel(self.tela, r, 235)
        pygame.draw.line(self.tela, (60, 70, 100), (0, r.y), (r.right, r.y), 2)
        w = r.w / len(ABAS)
        vertical = self.orientacao == "vertical"
        itens = self.resumo.itens if self.resumo else []
        selos = {"resumo": sum(1 for i in itens if i.prioridade >= URGENTE),
                 "emails": sum(1 for x in self.resumos_email.values() for p in x.get("pontos", []) if p.get("prioridade") == "alta")}
        mouse = tela.mouse_pos()
        for i, (chave, rot, icone) in enumerate(ABAS):
            b = pygame.Rect(int(r.x + i * w), r.y + 2, int(w), r.h - 2)
            ativa = chave == self.pagina
            if ativa or b.collidepoint(mouse):
                pygame.draw.rect(self.tela, (34, 42, 66) if ativa else (26, 30, 48), b)
            if ativa:
                pygame.draw.rect(self.tela, AZUL, (b.x + 10, b.y, b.w - 20, 4))
            tam = 64 if vertical else 48
            self.tela.blit(icons.item(icone, tam), (b.centerx - tam // 2, b.y + (4 if vertical else 0)))
            cor = BRANCO if ativa else CINZA
            self.centralizado(rot, b.centerx, b.bottom - (36 if vertical else 26), 2 if vertical else 1, cor, sombra=None)
            n = selos.get(chave, 0)
            if n:
                sx, sy = b.centerx + tam // 3, b.y + 4
                pygame.draw.circle(self.tela, VERMELHO, (sx, sy + 8), 11)
                self.centralizado(str(min(n, 99)), sx, sy, 1, BRANCO, sombra=None)
            self.alvos.append((b, lambda c=chave: self.ir(c)))

    def desenhar_dica(self):
        """Caixinha com o título inteiro do item embaixo do mouse."""
        if not self.dica:
            return
        texto, (mx, my) = self.dica
        lw = self.tela.get_width()
        linhas = font.wrap(texto, min(420, lw - 60), 1)[:4]
        w = max(font.largura(linha, 1) for linha in linhas) + 20
        h = len(linhas) * font.altura(1) + 14
        x = max(10, min(mx - w - 12, lw - w - 10))
        y = my + 14
        painel(self.tela, pygame.Rect(x, y, w, h), 240, (120, 130, 160))
        for i, linha in enumerate(linhas):
            self.escrever(linha, x + 10, y + 7 + i * font.altura(1), 1, BRANCO, sombra=None)

    # ---------- quadro ----------
    def quadro(self, dt):
        agora = self.agora()
        self.alvos, self.dica = [], None
        self.cena.update(dt, agora)
        baixa = self.cena.draw(agora)
        for e in self.efeitos:
            e.draw_baixa(baixa)
        pygame.transform.scale(baixa, self.tela.get_size(), self.tela)
        if self.config_tela:
            self.config_tela.desenhar(baixa)       # Configurações têm a própria tela
            if not self.config_tela.aberta:        # clicou em Salvar ou Cancelar
                self.config_tela = None
        else:
            if self.pagina != "inicio":
                self.desenhar_topo(agora)
            {"inicio": self.pagina_inicio, "resumo": self.pagina_resumo,
             "emails": self.pagina_emails, "agenda": self.pagina_agenda}[self.pagina](agora)
            self.desenhar_nav()
            self.desenhar_dica()
        for e in self.efeitos + self.toasts:
            e.update(dt)
        alvo = self.config_tela.superficie if self.config_tela else self.tela
        for e in self.efeitos:
            e.draw(alvo)
        for i, t in enumerate(self.toasts[-3:]):
            t.draw(alvo, i)
        self.efeitos = [e for e in self.efeitos if e.vivo]
        self.toasts = [t for t in self.toasts if t.vivo]
        tela.VIEW.apresentar(alvo, self.janela)

    def rodar(self):
        pygame.key.start_text_input()
        while self.rodando:
            dt = self.relogio.tick(30) / 1000
            for ev in pygame.event.get():
                if ev.type in (pygame.VIDEORESIZE, pygame.WINDOWSIZECHANGED):
                    self.redimensionou()
                    continue
                self.tratar(tela.converter(ev))
            self.receber()
            self.quadro(dt)
            pygame.display.flip()
        self.motor.encerrar()
