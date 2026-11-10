"""Tela de Configurações: tudo o que o programa precisa, sem editar arquivo nenhum.

Abas: Início, Clima, Horários, Notificações, Empresas, Chaves de API, Reuniões.

A tela trabalha numa CÓPIA da configuração (self.cfg) e das chaves (self.chaves).
Nada é gravado até clicar em "Salvar e aplicar": aí config.salvar() escreve o
config.yaml (sem segredos) e o .env (com as chaves), e o app reinicia o Motor.

Botões que usam a internet (buscar endereço, conectar, testar, login) rodam em
segundo plano; o resultado volta por uma fila e aparece embaixo do botão.
"""
import copy
import json
import os
import queue
import shutil
import sys
import threading
import webbrowser

import pygame

from .. import assistente, config, net
from ..config import nome_segredo
from ..connectors import weather
from . import font
from .widgets import AMARELO, BRANCO, CINZA, PALETA, VERDE, VERMELHO, Form, copiar

ABAS = ["Início", "Clima", "Horários", "Notificações", "Empresas", "Chaves de API", "Reuniões"]
FUSOS = [("America/Sao_Paulo", "Brasília"), ("America/Manaus", "Manaus"), ("America/Cuiaba", "Cuiabá"),
         ("America/Fortaleza", "Fortaleza"), ("America/Recife", "Recife"), ("America/Bahia", "Salvador"),
         ("America/Belem", "Belém"), ("America/Rio_Branco", "Rio Branco"), ("America/Noronha", "Noronha")]
SERVICOS = [("slack", "Slack"), ("clickup", "ClickUp"), ("gmail", "Gmail + Agenda"), ("zoom", "Zoom (reuniões)"),
            ("microsoft", "Outlook + Teams")]
GLOBAIS = ["DISCORD_WEBHOOK_URL", "NTFY_TOPIC", "NTFY_TOPIC_ALARME", "NTFY_SERVER", "NTFY_TOKEN", "ANTHROPIC_API_KEY"]
LARGURA = 900          # largura útil do conteúdo


def servico_novo(tipo, empresa):
    """Opções iniciais de um serviço recém-ligado. Segredos apontam para uma variável do .env."""
    base = {"tipo": tipo}
    if tipo == "slack":
        base.update(token_env=nome_segredo(empresa, "slack", "token"), meu_id="", canais=[], incluir_dms=False)
    elif tipo == "clickup":
        base.update(token_env=nome_segredo(empresa, "clickup", "token"), equipe_id="")
    elif tipo == "gmail":
        base.update(credenciais="", conta=nome_segredo(empresa).lower()[3:], agenda=True, resumo_ia=True)
    elif tipo == "zoom":
        base.update(account_id="", client_id="", client_secret_env=nome_segredo(empresa, "zoom", "secret"), email="")
    elif tipo == "microsoft":
        base.update(client_id="", tenant="organizations", email=True, agenda=True, teams=True, agendador=False)
    return base


class TelaConfig:
    def __init__(self, app, primeira_vez=False, orientacao="horizontal"):
        self.app = app
        self.primeira_vez = primeira_vez
        # as Configurações têm a própria tela: 1280x720 (abas na lateral) ou 960x1280 (abas em cima)
        self.vertical = orientacao == "vertical"
        self.superficie = pygame.Surface((960, 1280) if self.vertical else (1280, 720))
        self.form = Form(self.superficie)
        self.cfg = config.carregar_bruto()
        self.chaves = {n: os.getenv(n, "") for n in GLOBAIS}
        for emp in self.cfg["empresas"]:
            for con in emp["conectores"]:
                if con.get("token_env"):
                    self.chaves[con["token_env"]] = os.getenv(con["token_env"], "")
        self.chaves["NTFY_SERVER"] = self.chaves["NTFY_SERVER"] or "https://ntfy.sh"
        self._migrar()
        self.iniciar_windows = assistente.inicia_com_windows()
        self.original = None           # foto tirada depois do 1º quadro (os campos completam padrões)
        self.aba = 0
        self.mensagens = {}            # id do botão -> (texto, cor)
        self.dados = {}                # resultados guardados (canais do Slack, workspaces, endereços...)
        self.codigos = {}              # login Microsoft: id -> (site, código)
        self.fila = queue.Queue()
        self.busca = ""
        self.confirmar_remover = None
        self.aberta = True
        self.erro_salvar = ""

    # ---------- utilidades ----------
    def _migrar(self):
        """Configs antigas guardavam campos comuns (ID, tenant, arquivo) no .env.

        A tela edita esses campos direto no config.yaml; só tokens continuam no .env.
        """
        for emp in self.cfg["empresas"]:
            for con in emp["conectores"]:
                for campo in ("meu_id", "equipe_id", "credenciais", "client_id", "tenant"):
                    if f"{campo}_env" in con:
                        con[campo] = os.getenv(con.pop(f"{campo}_env"), "")

    def _foto(self):
        return json.dumps([self.cfg, self.chaves, self.iniciar_windows], sort_keys=True, default=str)

    def mudou(self):
        return self.original is not None and self._foto() != self.original

    def rodar(self, id_, funcao, *args, depois=None, aguarde="aguarde..."):
        """Roda funcao(*args) em segundo plano e mostra o resultado embaixo do botão."""
        self.mensagens[id_] = (aguarde, AMARELO)

        def trabalho():
            try:
                self.fila.put((id_, True, funcao(*args), depois))
            except (net.ApiError, config.ConfigError, ValueError) as exc:
                self.fila.put((id_, False, str(exc), None))
            except Exception as exc:  # erro inesperado: mostra em vez de quebrar
                self.fila.put((id_, False, f"erro: {exc}", None))
        threading.Thread(target=trabalho, daemon=True).start()

    def _resultados(self):
        while True:
            try:
                id_, ok, resultado, depois = self.fila.get_nowait()
            except queue.Empty:
                return
            if ok and depois:
                texto = depois(resultado)
                self.mensagens[id_] = (texto or "pronto!", VERDE)
            elif ok:
                self.mensagens[id_] = (str(resultado), VERDE)
            else:
                self.mensagens[id_] = (resultado, VERMELHO)

    def _aplicar_chaves_no_ambiente(self):
        """Antes de testar, deixa as chaves digitadas visíveis para os conectores (sem gravar)."""
        for nome, valor in self.chaves.items():
            if valor:
                os.environ[nome] = valor.strip()

    def _cfg_pronto(self):
        self._aplicar_chaves_no_ambiente()
        return config.preparar(self.cfg)

    # ---------- eventos ----------
    def evento(self, ev):
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE and not self.form.foco:
            self.fechar()
            return
        self.form.evento(ev)

    def fechar(self):
        self.aberta = False

    def salvar(self):
        try:
            config.preparar(self.cfg)          # valida antes de gravar
        except config.ConfigError as exc:
            self.erro_salvar = str(exc)
            return
        config.salvar(self.cfg, self.chaves)
        assistente.definir_inicio_com_windows(self.iniciar_windows)
        self.original = self._foto()
        self.erro_salvar = ""
        self.aberta = False
        self.app.recarregar()

    # ---------- desenho ----------
    def desenhar(self, fundo):
        """Desenha tudo na própria superfície; o app ajusta ela ao tamanho da janela."""
        self._resultados()
        tela = self.superficie
        largura, altura = tela.get_size()
        pygame.transform.scale(fundo, (largura, altura), tela)      # o cenário aparece atrás
        if not hasattr(self, "_escuro"):          # criado uma vez só (economiza memória)
            self._escuro = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
            self._escuro.fill((6, 8, 16, 215))
        tela.blit(self._escuro, (0, 0))
        # cabeçalho: mesma barra do topo da tela principal
        topo = pygame.Surface((tela.get_width(), 76), pygame.SRCALPHA)
        topo.fill((10, 12, 22, 235))
        tela.blit(topo, (0, 0))
        pygame.draw.line(tela, (60, 70, 100), (0, 76), (tela.get_width(), 76), 2)
        tela.blit(font.render("CONFIGURAÇÕES", 4, BRANCO, shadow=(0, 0, 0), familia="titulo"), (40, 20))
        if not self.vertical:
            sub = "Tudo do PixelDigest se ajusta aqui. Nada é gravado até você clicar em Salvar."
            tela.blit(font.render(sub, 1, CINZA), (largura - font.largura(sub, 1) - 40, 30))

        f = self.form
        f.comecar(pygame.Rect(0, 0, largura, altura))
        if self.vertical:
            # abas em duas linhas no topo
            for i, nome in enumerate(ABAS):
                if f.botao(f"aba{i}", 20 + (i % 4) * 232, 92 + (i // 4) * 48, 220, nome,
                           VERDE if i == self.aba else (110, 116, 140), h=40):
                    self.aba, f.rolagem, f.foco = i, 0, None
            area = pygame.Rect(20, 200, 930, altura - 200 - 110)
        else:
            # abas na lateral (fora da área com rolagem)
            for i, nome in enumerate(ABAS):
                if f.botao(f"aba{i}", 40, 96 + i * 50, 210, nome, VERDE if i == self.aba else (110, 116, 140), h=40):
                    self.aba, f.rolagem, f.foco = i, 0, None
            if self.mudou():
                f.paragrafo(40, 470, "Você tem alterações que ainda não foram salvas.", 210, AMARELO)
            area = pygame.Rect(280, 90, 960, 540)
        f.terminar()

        # conteúdo da aba, com rolagem
        f.comecar(area, rolar=True)
        x, y = area.x + 10, area.y + 6
        desenhar_aba = [self.aba_inicio, self.aba_clima, self.aba_horarios, self.aba_notificacoes,
                        self.aba_empresas, self.aba_chaves, self.aba_reunioes][self.aba]
        fim = desenhar_aba(x, y)
        f.terminar(fim - area.y + 20)
        if f.altura > area.h:      # barrinha de rolagem
            prop = area.h / f.altura
            barra = pygame.Rect(area.right + 8, area.y + int(f.rolagem * prop), 6, int(area.h * prop))
            pygame.draw.rect(tela, (90, 100, 130), barra)

        # rodapé
        f.comecar(pygame.Rect(0, 0, largura, altura))
        rodape = altura - 70
        if f.botao("salvar", largura - 280, rodape, 240, "Salvar e aplicar", VERDE, h=44):
            self.salvar()
        if f.botao("cancelar", largura - 450, rodape, 160, "Cancelar", (160, 160, 180), h=44):
            self.fechar()
        texto_w = largura - 520
        if self.erro_salvar:
            f.paragrafo(40, rodape + 6, self.erro_salvar, texto_w, VERMELHO)
        elif self.vertical and self.mudou():
            f.paragrafo(40, rodape + 12, "Alterações ainda não salvas.", texto_w, AMARELO)
        else:
            f.paragrafo(40, rodape + 12, "Esc fecha. Ctrl+V cola. Tab vai para o próximo campo.", texto_w, CINZA)
        f.terminar()
        f.fim_do_quadro()
        if self.original is None:
            self.original = self._foto()

    # ---------- abas ----------
    def aba_inicio(self, x, y):
        f = self.form
        if self.primeira_vez:
            y = f.secao(x, y, "Bem-vindo ao PixelDigest!", LARGURA)
            y = f.paragrafo(x, y, "Vamos deixar tudo pronto em poucos passos. Siga as abas da esquerda de cima para baixo: "
                                  "Clima, Horários, Notificações, Empresas e Chaves de API. Cada aba tem um botão para testar. "
                                  "No fim, clique em Salvar e aplicar.", LARGURA, BRANCO) + 16
            y = f.paragrafo(x, y, "Só quer ver funcionando? Ligue o Modo demonstração abaixo e salve.", LARGURA, AMARELO) + 20
        y = f.secao(x, y, "Você", LARGURA)
        f.texto(x, y, "Seu nome (aparece no bom dia)")
        self.cfg["usuario"]["nome"] = f.campo("nome", x, y + 22, 420, self.cfg["usuario"]["nome"], dica="ex.: Felipe")
        y += 80
        self.cfg["demo"] = f.alternar("demo", x, y, self.cfg["demo"], "Modo demonstração (empresas de exemplo, sem contas reais)")
        y += 40
        if sys.platform == "win32":
            self.iniciar_windows = f.alternar("win", x, y, self.iniciar_windows, "Abrir sozinho quando o Windows ligar")
            y += 40
        y = self._tela(x, y)
        y = f.secao(x, y + 10, "Fuso horário", LARGURA)
        y = f.paragrafo(x, y, "Ajustado sozinho quando você escolhe o local do clima. Mude aqui se precisar.", LARGURA)
        self.cfg["usuario"]["fuso"] = f.opcoes("fuso", x, y + 6, self.cfg["usuario"]["fuso"], FUSOS, 200, 4)
        return y + 6 + 42 * 3

    def _tela(self, x, y):
        """Orientação, resolução e tela cheia (o layout se ajusta como uma media query)."""
        from .tela import ORIENTACOES, RESOLUCOES
        f, t = self.form, self.cfg["tela"]
        y = f.secao(x, y + 10, "Tela", LARGURA)
        y = f.paragrafo(x, y, "Automática: o layout fica vertical quando a janela é mais alta que larga, e horizontal "
                              "no contrário. Dá para redimensionar a janela arrastando a borda.", LARGURA)
        t["orientacao"] = f.opcoes("orient", x, y + 6, t["orientacao"], ORIENTACOES, 200, 4)
        y += 56
        f.texto(x, y, "Tamanho da janela ao abrir")
        lista = RESOLUCOES["vertical" if t["orientacao"] == "vertical" else "horizontal"]
        if t["orientacao"] == "automatica":
            lista = RESOLUCOES["horizontal"] + RESOLUCOES["vertical"]
        escolhas = [(r, r.replace("x", " x ")) for r in lista]
        if t["resolucao"] not in lista:
            t["resolucao"] = lista[1]
        t["resolucao"] = f.opcoes("resol", x, y + 26, t["resolucao"], escolhas, 200, 4)
        y += 26 + 42 * ((len(escolhas) + 3) // 4) + 8
        t["tela_cheia"] = f.alternar("cheia", x, y, t["tela_cheia"], "Tela cheia (ocupa o monitor inteiro)")
        return y + 40

    def aba_clima(self, x, y):
        f = self.form
        y = f.secao(x, y, "Local do clima e tempo", LARGURA)
        y = f.paragrafo(x, y, "Digite um endereço, bairro ou cidade e clique em Buscar. Depois escolha o resultado certo.", LARGURA)
        self.busca = f.campo("busca", x, y + 8, 520, self.busca, dica="ex.: Av. Paulista 1000, São Paulo")
        if f.botao("buscar", x + 532, y + 8, 120, "Buscar"):
            self.rodar("buscar", assistente.buscar_endereco, self.busca,
                       depois=lambda r: self.dados.__setitem__("enderecos", r) or f"{len(r)} resultado(s). Clique no certo:")
        if f.botao("aqui", x + 664, y + 8, 236, "Minha localização"):
            self.rodar("buscar", assistente.minha_localizacao,
                       depois=lambda r: self.dados.__setitem__("enderecos", [r]) or "Achei pela internet. Confirme clicando:")
        y = f.status(x, y + 52, self.mensagens.get("buscar")) + 6
        for i, r in enumerate(self.dados.get("enderecos", [])):
            rotulo = font.cortar(r["local"], LARGURA - 30)
            if f.botao(f"end{i}", x, y, LARGURA, rotulo, (120, 200, 255)):
                self.escolher_local(r)
            y += 42
        y = f.secao(x, y + 14, "Escolhido", LARGURA)
        c = self.cfg["clima"]
        y = f.paragrafo(x, y, c.get("local") or "nenhum", LARGURA, BRANCO)
        if c.get("lat") is not None:
            y = f.paragrafo(x, y, f"coordenadas {c['lat']}, {c['lon']}  |  fuso {self.cfg['usuario']['fuso']}", LARGURA)
        if f.botao("climaagora", x, y + 10, 220, "Ver o clima agora"):
            def ver():
                k = weather.buscar(self.cfg["clima"], self.cfg["usuario"]["fuso"])
                return f"Agora em {k.cidade}: {k.temperatura:.0f}°, {k.descricao}, chuva {k.prob_chuva}%"
            self.rodar("climaagora", ver)
        return f.status(x, y + 56, self.mensagens.get("climaagora"))

    def escolher_local(self, r):
        self.cfg["clima"] = {"local": r["local"], "cidade": r.get("cidade") or r["local"].split(",")[0],
                             "lat": r["lat"], "lon": r["lon"]}
        self.dados["enderecos"] = []
        if r.get("fuso"):
            self.cfg["usuario"]["fuso"] = r["fuso"]
            self.mensagens["buscar"] = ("Local escolhido!", VERDE)
        else:
            def ajustar(fuso):
                if fuso:
                    self.cfg["usuario"]["fuso"] = fuso
                return f"Local escolhido! Fuso: {fuso}"
            self.rodar("buscar", assistente.fuso_do_local, r["lat"], r["lon"], depois=ajustar)

    def aba_horarios(self, x, y):
        f = self.form
        h = self.cfg["horarios"]
        y = f.secao(x, y, "Animações e resumos do dia", LARGURA)
        f.texto(x, y + 10, "Bom dia (resumo da manhã)")
        h["inicio_dia"] = f.hora("ini", x + 420, y, h["inicio_dia"])
        f.texto(x, y + 60, "Fim do expediente")
        h["fim_dia"] = f.hora("fim", x + 420, y + 50, h["fim_dia"])
        y = f.secao(x, y + 110, "Horário de trabalho", LARGURA)
        y = f.paragrafo(x, y, "O agendador só sugere reuniões dentro deste horário, de segunda a sexta.", LARGURA)
        f.texto(x, y + 18, "Das")
        h["expediente"][0] = f.hora("exp0", x + 60, y + 8, h["expediente"][0])
        f.texto(x + 240, y + 18, "até")
        h["expediente"][1] = f.hora("exp1", x + 300, y + 8, h["expediente"][1])
        return y + 60

    def aba_notificacoes(self, x, y):
        f, n, ch = self.form, self.cfg["notificacoes"], self.chaves
        y = f.secao(x, y, "Discord", LARGURA)
        n["discord"] = f.alternar("ndisc", x, y, n["discord"], "Mandar os avisos para um canal do Discord")
        y += 40
        if n["discord"]:
            y = self._discord(x, y)
        y = f.secao(x, y + 10, "Celular (app ntfy, grátis)", LARGURA)
        n["celular"] = f.alternar("ncel", x, y, n["celular"], "Mandar os avisos para o celular")
        y += 40
        if n["celular"]:
            topo = y
            y = f.paragrafo(x, y, "1. Instale o app ntfy (Play Store).  2. Toque em + e digite o tópico abaixo, "
                                  "ou leia o QR code com a câmera.  3. Clique em Testar.", 560)
            f.texto(x, y + 8, "Tópico (funciona como senha, não divulgue)")
            ch["NTFY_TOPIC"] = f.campo("topico", x, y + 30, 420, ch["NTFY_TOPIC"], dica="clique em Gerar")
            if f.botao("gertop", x + 430, y + 30, 120, "Gerar"):
                ch["NTFY_TOPIC"] = assistente.novo_topico()
            if f.botao("testcel", x, y + 76, 220, "Testar celular"):
                self.rodar("testcel", assistente.testar_ntfy, ch["NTFY_SERVER"], ch["NTFY_TOPIC"], ch["NTFY_TOKEN"])
            y = f.status(x, y + 120, self.mensagens.get("testcel"))
            if ch["NTFY_TOPIC"]:
                lado = f.qrcode(x + 640, topo, f"{ch['NTFY_SERVER'].rstrip('/')}/{ch['NTFY_TOPIC']}", 5) or 0
                y = max(y, topo + lado + 10)
        y = f.secao(x, y + 10, "Alarme do celular", LARGURA)
        n["ouvir_alarme"] = f.alternar("nalarm", x, y, n["ouvir_alarme"], "Mostrar na tela quando o alarme do celular tocar")
        y += 40
        if n["ouvir_alarme"]:
            if not ch["NTFY_TOPIC_ALARME"]:
                ch["NTFY_TOPIC_ALARME"] = assistente.novo_topico("pixeldigest-alarme")
            url = assistente.endereco_alarme(ch["NTFY_SERVER"], ch["NTFY_TOPIC_ALARME"])
            topo = y
            y = f.paragrafo(x, y, "No celular, abra o MacroDroid e crie uma macro:", 600, BRANCO)
            y = f.paragrafo(x, y, "1. Gatilho: Notificação recebida, app Relógio, texto contém \"Alarme\".", 600)
            y = f.paragrafo(x, y, "2. Ação: Requisição HTTP (GET ou POST, tanto faz) no endereço abaixo. "
                                  "Para não digitar errado, aponte a câmera para o QR code, copie e cole.", 600)
            y = f.paragrafo(x, y + 4, url, 600, AMARELO, 1)
            if f.botao("copiaalarm", x, y + 8, 170, "Copiar endereço"):
                copiar(url)
                self.mensagens["testalarm"] = ("endereço copiado", VERDE)
            if f.botao("testalarm", x + 180, y + 8, 200, "Testar alarme agora"):
                self.rodar("testalarm", assistente.testar_ntfy, ch["NTFY_SERVER"], ch["NTFY_TOPIC_ALARME"],
                           ch["NTFY_TOKEN"], "Alarme", "Teste do alarme",
                           depois=lambda r: "enviado pelo PC! Se já salvou, o despertador aparece na tela")
            if f.botao("chegou", x, y + 50, 380, "Ver o que chegou do celular"):
                self.rodar("testalarm", assistente.ultimas_mensagens, ch["NTFY_SERVER"], ch["NTFY_TOPIC_ALARME"],
                           ch["NTFY_TOKEN"], aguarde="consultando o ntfy...")
            ouvinte = getattr(self.app.motor, "alarme", None)
            if ouvinte is not None and getattr(ouvinte, "conectado", False):
                estado = "O PC está escutando o celular agora." + (f" Último alarme: {ouvinte.ultima[0]}" if ouvinte.ultima else "")
                f.texto(x, y + 96, estado, VERDE, 1)
            else:
                f.texto(x, y + 96, "O PC ainda não está escutando (salve as configurações).", AMARELO, 1)
            y = f.status(x, y + 122, self.mensagens.get("testalarm"))
            lado = f.qrcode(x + 640, topo, url, 3) or 0
            y = max(y, topo + lado + 10)
        y = f.secao(x, y + 10, "Avançado (opcional)", LARGURA)
        f.texto(x, y, "Servidor ntfy")
        ch["NTFY_SERVER"] = f.campo("ntfysrv", x, y + 22, 420, ch["NTFY_SERVER"])
        f.texto(x + 470, y, "Token do ntfy")
        ch["NTFY_TOKEN"] = f.campo("ntfytok", x + 470, y + 22, 420, ch["NTFY_TOKEN"], secreto=True, dica="vazio no ntfy.sh")
        return y + 70

    def _discord(self, x, y):
        f = self.form
        y = f.paragrafo(x, y, "No Discord: editar canal > Integrações > Webhooks > Novo webhook > Copiar URL. Cole aqui:", LARGURA)
        self.chaves["DISCORD_WEBHOOK_URL"] = f.campo("webhook", x, y + 8, 760, self.chaves["DISCORD_WEBHOOK_URL"],
                                                    secreto=True, dica="https://discord.com/api/webhooks/...")
        if f.botao("testdisc", x, y + 52, 220, "Testar Discord"):
            self.rodar("testdisc", assistente.testar_discord, self.chaves["DISCORD_WEBHOOK_URL"].strip())
        return f.status(x, y + 96, self.mensagens.get("testdisc")) + 6

    def aba_empresas(self, x, y):
        f = self.form
        y = f.paragrafo(x, y, "Adicione as empresas em que você trabalha e ligue os serviços que cada uma usa. "
                              "As chaves de cada serviço ficam na aba Chaves de API.", LARGURA) + 10
        for i, emp in enumerate(list(self.cfg["empresas"])):
            topo = y
            pygame.draw.rect(f.tela, config.cor_rgb(emp.get("cor", "#5ab0ff")), f.r(x - 10, topo, 4, 10))
            f.texto(x, y, "Nome da empresa")
            novo_nome = f.campo(f"emp{i}nome", x, y + 22, 420, emp["nome"], dica="ex.: Minha Empresa")
            emp["nome"] = novo_nome
            f.texto(x + 470, y, "Cor")
            emp["cor"] = f.cores(f"emp{i}cor", x + 470, y + 24, emp.get("cor", PALETA[0]))
            y += 72
            emp["ativa"] = f.alternar(f"emp{i}ativa", x, y, emp.get("ativa", True),
                                      "Empresa ativa" if emp.get("ativa", True) else "Desligada: nada desta empresa é buscado")
            y += 40
            f.texto(x, y, "Serviços que essa empresa usa:")
            y += 24
            ligados = {c["tipo"] for c in emp["conectores"]}
            for j, (tipo, rotulo) in enumerate(SERVICOS):
                marcado, _ = f.chip(f"emp{i}{tipo}", x + (j % 3) * 300, y + (j // 3) * 38, rotulo, tipo in ligados)
                if marcado and tipo not in ligados:
                    emp["conectores"].append(servico_novo(tipo, emp["nome"] or f"empresa{i}"))
                elif not marcado and tipo in ligados:
                    emp["conectores"] = [c for c in emp["conectores"] if c["tipo"] != tipo]
            y += 38 * ((len(SERVICOS) + 2) // 3) + 8
            ms = next((c for c in emp["conectores"] if c["tipo"] == "microsoft"), None)
            if ms:
                f.texto(x, y, "No Outlook + Teams, usar:")
                y += 26
                for k, (chave, rotulo) in enumerate([("email", "E-mails"), ("agenda", "Agenda"), ("teams", "Chats do Teams"),
                                                     ("agendador", "Agendador de reuniões")]):
                    ms[chave], _ = f.chip(f"emp{i}ms{chave}", x + (k % 2) * 300, y + (k // 2) * 38, rotulo, ms.get(chave, True))
                y += 84
            rotulo = "Clique de novo para confirmar" if self.confirmar_remover == i else "Remover empresa"
            if f.botao(f"emp{i}rem", x, y, 300, rotulo, VERMELHO):
                if self.confirmar_remover == i:
                    self.cfg["empresas"].pop(i)
                    self.confirmar_remover = None
                    return y
                self.confirmar_remover = i
            pygame.draw.rect(f.tela, config.cor_rgb(emp.get("cor", "#5ab0ff")), f.r(x - 10, topo, 4, y + 34 - topo))
            y += 60
        if f.botao("addemp", x, y, 300, "+ Adicionar empresa", VERDE, h=40):
            n = len(self.cfg["empresas"])
            self.cfg["empresas"].append({"nome": "", "cor": PALETA[n % len(PALETA)], "conectores": []})
            self.mensagens.pop("addemp", None)
        return y + 50

    def aba_chaves(self, x, y):
        f = self.form
        y = f.paragrafo(x, y, "Todas as chaves de API ficam aqui. Elas são gravadas só no arquivo .env do seu "
                              "computador (nunca no GitHub). Use os botões Conectar e Testar para conferir.", LARGURA) + 8
        y = f.secao(x, y, "Discord", LARGURA)
        y = self._discord(x, y)
        y = f.secao(x, y + 6, "Celular (ntfy)", LARGURA)
        f.texto(x, y, "Tópico das notificações")
        self.chaves["NTFY_TOPIC"] = f.campo("topico2", x, y + 22, 420, self.chaves["NTFY_TOPIC"], dica="gere na aba Notificações")
        f.texto(x + 470, y, "Token do ntfy (opcional)")
        self.chaves["NTFY_TOKEN"] = f.campo("ntfytok2", x + 470, y + 22, 420, self.chaves["NTFY_TOKEN"], secreto=True)
        y += 76
        y = self._chaves_claude(x, y)
        if not self.cfg["empresas"]:
            return f.paragrafo(x, y + 10, "Nenhuma empresa ainda. Adicione na aba Empresas.", LARGURA, AMARELO)
        for i, emp in enumerate(self.cfg["empresas"]):
            if not emp.get("ativa", True):
                y = f.secao(x, y + 10, f"{emp['nome']}: desligada", LARGURA)
                y = f.paragrafo(x, y, "Ligue a empresa na aba Empresas para configurar as chaves dela.", LARGURA) + 6
                continue
            for con in emp["conectores"]:
                titulo = f"{emp['nome'] or 'Empresa sem nome'}: {dict(SERVICOS)[con['tipo']]}"
                y = f.secao(x, y + 10, titulo, LARGURA)
                y = getattr(self, f"_chaves_{con['tipo']}")(f"{i}{con['tipo']}", emp, con, x, y)
                if f.botao(f"t{i}{con['tipo']}", x, y, 260, "Testar este serviço"):
                    self.rodar(f"t{i}{con['tipo']}", lambda e=emp, c=con: assistente.testar_servico(
                        c["tipo"], e["nome"], copy.deepcopy(c), self._cfg_pronto()))
                y = f.status(x, y + 44, self.mensagens.get(f"t{i}{con['tipo']}")) + 4
        return y

    def _segredo(self, id_, con, campo, x, y, w, rotulo, dica):
        """Campo de chave secreta: o valor vai para self.chaves[nome da variável]."""
        nome = con.setdefault(f"{campo}_env", nome_segredo(id_, campo))
        self.form.texto(x, y, rotulo)
        self.chaves[nome] = self.form.campo(id_ + campo, x, y + 22, w, self.chaves.get(nome, os.getenv(nome, "")),
                                            secreto=True, dica=dica)
        return self.chaves[nome]

    def _chaves_slack(self, id_, emp, con, x, y):
        f = self.form
        y = f.paragrafo(x, y, "Use o token de USUÁRIO (xoxp-): ele lê como você, então aparecem seus canais privados "
                              "e suas DMs. No app em api.slack.com/apps, em OAuth & Permissions > User Token Scopes, "
                              "adicione channels:history, channels:read, groups:history, groups:read, im:history, "
                              "im:read, mpim:history, mpim:read e users:read. Reinstale e copie o User OAuth Token.", LARGURA)
        if f.botao(id_ + "guia", x, y + 6, 240, "Abrir api.slack.com"):
            webbrowser.open("https://api.slack.com/apps")
        y += 50
        token = self._segredo(id_, con, "token", x, y, 700, "Token do Slack (de usuário, começa com xoxp-)", "xoxp-...")
        if f.botao(id_ + "con", x + 710, y + 22, 180, "Conectar"):
            def pronto(r, c=con, k=id_):
                texto, canais, usuario = r
                self.dados[k + "canais"] = canais
                if usuario:                      # token de usuário: o ID de membro é o do próprio token
                    c["meu_id"] = usuario
                # tira da seleção canais que não existem mais (ou que este token não enxerga)
                existentes = {cid for cid, _ in canais}
                sumidos = [cid for cid in c.get("canais", []) if cid not in existentes]
                c["canais"] = [cid for cid in c.get("canais", []) if cid in existentes]
                if sumidos:
                    texto += f". Removi {len(sumidos)} canal(is) que não existem mais"
                return f"{texto}. Marque os canais que quer acompanhar:"
            self.rodar(id_ + "con", assistente.slack_conectar, token.strip(), depois=pronto)
        y = f.status(x, y + 66, self.mensagens.get(id_ + "con"))
        canais = self.dados.get(id_ + "canais")
        escolhidos = set(con.get("canais", []))
        if canais:
            cx, cy = x, y + 4
            for cid, nome in canais:
                w = Form.largura_chip("#" + nome)
                if cx + w > x + LARGURA:
                    cx, cy = x, cy + 38
                marcado, w = f.chip(id_ + cid, cx, cy, "#" + nome, cid in escolhidos)
                if marcado:
                    escolhidos.add(cid)
                else:
                    escolhidos.discard(cid)
                cx += w + 8
            con["canais"] = sorted(escolhidos)
            y = cy + 44
        elif escolhidos:
            y = f.paragrafo(x, y + 4, f"{len(escolhidos)} canal(is) escolhido(s). Clique em Conectar para mudar.", LARGURA) + 6
        f.texto(x, y + 4, "Seu ID de membro no Slack (para saber quando te marcam)")
        con["meu_id"] = f.campo(id_ + "meuid", x, y + 26, 420, con.get("meu_id", ""), dica="U0123... (perfil > Copiar ID)")
        con["incluir_dms"] = f.alternar(id_ + "dms", x + 450, y + 30, con.get("incluir_dms", False),
                                        "Ler DMs e grupos")
        return y + 76

    def _chaves_clickup(self, id_, emp, con, x, y):
        f = self.form
        y = f.paragrafo(x, y, "No ClickUp: avatar > Configurações > Apps > API Token > Gerar. Cole abaixo e clique em Conectar.", LARGURA)
        y += 8
        token = self._segredo(id_, con, "token", x, y, 700, "Token pessoal do ClickUp", "pk_...")
        if f.botao(id_ + "con", x + 710, y + 22, 180, "Conectar"):
            def pronto(lista, k=id_, c=con):
                self.dados[k + "ws"] = lista
                if len(lista) == 1:
                    c["equipe_id"] = lista[0][0]
                    return f"conectado ao workspace {lista[0][1]}"
                return "escolha o workspace:"
            self.rodar(id_ + "con", assistente.clickup_workspaces, token.strip(), depois=pronto)
        y = f.status(x, y + 66, self.mensagens.get(id_ + "con"))
        lista = self.dados.get(id_ + "ws", [])
        if len(lista) > 1:
            con["equipe_id"] = f.opcoes(id_ + "ws", x, y + 4, con.get("equipe_id"), lista, 290, 3)
            y += 4 + 42 * ((len(lista) + 2) // 3)
        f.texto(x, y + 4, f"Workspace escolhido: {con.get('equipe_id') or 'nenhum'}", CINZA)
        return y + 34

    def _chaves_claude(self, x, y):
        """Chave do Claude para o resumo dos e-mails com IA."""
        f = self.form
        y = f.secao(x, y + 6, "Resumo dos e-mails com IA (Claude)", LARGURA)
        y = f.paragrafo(x, y, "Com a chave, os 10 e-mails mais recentes de cada conta viram um resumo dos pontos "
                              "importantes. O texto dos e-mails é enviado para a API da Anthropic. Crie a chave em "
                              "console.anthropic.com > API Keys.", LARGURA)
        if f.botao("claudeguia", x, y + 6, 260, "Abrir console.anthropic.com"):
            webbrowser.open("https://console.anthropic.com/settings/keys")
        y += 52
        f.texto(x, y, "Chave do Claude")
        self.chaves["ANTHROPIC_API_KEY"] = f.campo("claudekey", x, y + 22, 640, self.chaves.get("ANTHROPIC_API_KEY", ""),
                                                   secreto=True, dica="sk-ant-...")
        if f.botao("claudetest", x + 720, y + 22, 170, "Testar"):
            self.rodar("claudetest", assistente.testar_claude, self.chaves["ANTHROPIC_API_KEY"].strip(),
                       self.cfg["ia"]["modelo"])
        y = f.status(x, y + 64, self.mensagens.get("claudetest"))
        f.texto(x, y + 6, "Modelo")
        from ..resumo_email import MODELOS
        self.cfg["ia"]["modelo"] = f.opcoes("modelo", x + 90, y, self.cfg["ia"]["modelo"], MODELOS, 260, 3)
        return y + 50

    def _chaves_zoom(self, id_, emp, con, x, y):
        f = self.form
        y = f.paragrafo(x, y, "No Zoom: marketplace.zoom.us > Develop > Build App > Server-to-Server OAuth. Dê um nome, "
                              "em Scopes adicione meeting:read:list_meetings:admin, ative o app e copie Account ID, "
                              "Client ID e Client Secret. Pode precisar do admin da conta Zoom.", LARGURA)
        if f.botao(id_ + "guia", x, y + 6, 260, "Abrir Zoom Marketplace"):
            webbrowser.open("https://marketplace.zoom.us/develop/create")
        y += 54
        f.texto(x, y, "Account ID")
        con["account_id"] = f.campo(id_ + "acc", x, y + 22, 430, con.get("account_id", ""))
        f.texto(x + 460, y, "Client ID")
        con["client_id"] = f.campo(id_ + "cid", x + 460, y + 22, 430, con.get("client_id", ""))
        y += 70
        self._segredo(id_, con, "client_secret", x, y, 500, "Client Secret", "")
        f.texto(x + 580, y, "Seu e-mail no Zoom")
        con["email"] = f.campo(id_ + "mail", x + 580, y + 22, 310, con.get("email", ""), dica="felipe@...")
        return y + 72

    def _chaves_gmail(self, id_, emp, con, x, y):
        f = self.form
        if not con.get("credenciais"):          # outra conta já tem o arquivo? usa o mesmo
            for e in self.cfg["empresas"]:
                for c in e["conectores"]:
                    if c is not con and c.get("tipo") == "gmail" and c.get("credenciais"):
                        con["credenciais"] = c["credenciais"]
        y = f.paragrafo(x, y, "No Google Cloud: crie um projeto, ative Gmail API e Calendar API, configure a tela de "
                              "consentimento e crie um ID do cliente OAuth do tipo App para computador. "
                              "Baixe o arquivo .json e escolha ele aqui.", LARGURA)
        if f.botao(id_ + "guia", x, y + 6, 260, "Abrir Google Cloud"):
            webbrowser.open("https://console.cloud.google.com/apis/credentials")
        y += 54
        f.texto(x, y, "Arquivo de credenciais OAuth (.json)")
        con["credenciais"] = f.campo(id_ + "cred", x, y + 22, 560, con.get("credenciais", ""), dica="clique em Procurar")
        if f.botao(id_ + "proc", x + 570, y + 22, 150, "Procurar..."):
            caminho = escolher_arquivo()
            if caminho:
                destino = config.TOKENS / f"google-cliente-{con.get('conta', 'padrao')}.json"
                shutil.copyfile(caminho, destino)
                con["credenciais"] = str(destino.relative_to(config.ROOT)).replace("\\", "/")
        conta = config.TOKENS / f"google-{con.get('conta', 'padrao')}.json"
        if f.botao(id_ + "login", x + 730, y + 22, 160, "Fazer login"):
            def entrar(e=emp, c=con):
                from ..connectors.google import GmailConector
                email = GmailConector(e["nome"], c, self._cfg_pronto()).login()
                c["email"] = email
                return f"login feito como {email}!"
            self.rodar(id_ + "login", entrar, aguarde="abrindo o navegador... escolha a conta certa e autorize")
        y = f.status(x, y + 66, self.mensagens.get(id_ + "login"))
        if conta.exists():
            f.texto(x, y + 4, f"Conectado{' como ' + con['email'] if con.get('email') else ''}", VERDE)
        else:
            f.texto(x, y + 4, "Ainda não conectado", AMARELO)
        y += 34
        con["agenda"] = f.alternar(id_ + "agenda", x, y, con.get("agenda", True), "Incluir a Google Agenda")
        con["resumo_ia"] = f.alternar(id_ + "ia", x + 400, y, con.get("resumo_ia", True), "Resumir os e-mails com IA")
        return y + 40

    def _chaves_microsoft(self, id_, emp, con, x, y):
        f = self.form
        y = f.paragrafo(x, y, "No portal do Azure: Entra ID > Registros de aplicativo > Novo registro. Em Autenticação, "
                              "ligue Permitir fluxos de clientes públicos. Em Permissões, adicione (delegadas) User.Read, "
                              "Mail.Read, Calendars.ReadWrite, Chat.Read, ChatMessage.Send, People.Read e "
                              "User.ReadBasic.All. Pode precisar do TI da empresa.", LARGURA)
        if f.botao(id_ + "guia", x, y + 6, 240, "Abrir portal Azure"):
            webbrowser.open("https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade")
        y += 54
        f.texto(x, y, "ID do aplicativo (cliente)")
        con["client_id"] = f.campo(id_ + "cid", x, y + 22, 430, con.get("client_id", ""), dica="0000-...")
        f.texto(x + 460, y, "ID do diretório (locatário)")
        con["tenant"] = f.campo(id_ + "ten", x + 460, y + 22, 430, con.get("tenant", "organizations"), dica="organizations")
        y += 70
        if f.botao(id_ + "login", x, y, 200, "Fazer login"):
            def entrar(e=emp, c=con, k=id_):
                from ..connectors.microsoft import MicrosoftConector
                MicrosoftConector(e["nome"], c, self._cfg_pronto()).login(
                    mostrar_codigo=lambda site, codigo: self.codigos.__setitem__(k, (site, codigo)))
                self.codigos.pop(k, None)
                return "login feito!"
            self.rodar(id_ + "login", entrar, aguarde="gerando o código...")
        y = f.status(x + 214, y + 10, self.mensagens.get(id_ + "login"))
        if id_ in self.codigos:
            site, codigo = self.codigos[id_]
            y = f.paragrafo(x, y + 6, f"Abra {site} e digite o código:", LARGURA, BRANCO)
            f.texto(x, y + 4, codigo, AMARELO, 5)
            if f.botao(id_ + "abrir", x + 420, y, 160, "Abrir site"):
                webbrowser.open(site)
            if f.botao(id_ + "copiar", x + 590, y, 180, "Copiar código"):
                copiar(codigo)
            y += 54
        from ..connectors.microsoft import slug
        conectado = (config.TOKENS / f"ms-{slug(emp['nome'])}.json").exists()   # login salvo
        f.texto(x, y + 6, "Conectado" if conectado else "Ainda não conectado", VERDE if conectado else AMARELO)
        return y + 40

    def aba_reunioes(self, x, y):
        f, r = self.form, self.cfg["reunioes"]
        y = f.secao(x, y, "Agendador de reuniões (Outlook + Teams)", LARGURA)
        y = f.paragrafo(x, y, "Usa a empresa com 'Agendador de reuniões' marcado na aba Empresas. Quando alguém pede "
                              "reunião no Teams, ele mostra os horários livres para vocês dois.", LARGURA) + 10
        f.texto(x, y + 10, "Duração padrão")
        r["duracao_padrao"] = f.numero("dur", x + 360, y, int(r["duracao_padrao"]), 15, 240, 15, "{} min")
        f.texto(x, y + 60, "Quantos dias úteis olhar")
        r["dias_para_frente"] = f.numero("dias", x + 360, y + 50, int(r["dias_para_frente"]), 1, 10, 1, "{} dias")
        y += 110
        r["responder_no_teams"] = f.alternar("resp", x, y, r["responder_no_teams"],
                                             "Responder sozinho no chat do Teams com os horários livres")
        y += 46
        f.texto(x, y, "Palavras que indicam pedido de reunião (separadas por vírgula)")
        # o texto digitado fica guardado como está (com vírgulas e espaços); a lista é derivada dele
        texto = self.dados.setdefault("palavras", ", ".join(r["palavras"]))
        self.dados["palavras"] = f.campo("palavras", x, y + 22, LARGURA, texto)
        r["palavras"] = [p.strip() for p in self.dados["palavras"].split(",") if p.strip()] or r["palavras"]
        return y + 70


def escolher_arquivo():
    """Janela do sistema para escolher o .json do Google."""
    try:
        import tkinter
        from tkinter import filedialog
        raiz = tkinter.Tk()
        raiz.withdraw()
        raiz.attributes("-topmost", True)
        caminho = filedialog.askopenfilename(title="Arquivo de credenciais do Google",
                                             filetypes=[("JSON", "*.json"), ("Todos", "*.*")])
        raiz.destroy()
        return caminho
    except Exception:
        return ""
