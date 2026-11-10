"""Componentes da tela de Configurações (no estilo "immediate mode").

Em vez de criar objetos para cada botão, a tela chama funções a cada quadro:

    nome = form.campo("nome", x, y, 400, nome)
    if form.botao("salvar", x, y, 200, "Salvar"):
        salvar()

Cada função desenha o componente e já devolve o novo valor (ou True se clicado).
O Form guarda só o que precisa durar entre quadros: qual campo está com o foco,
o texto digitado, o clique do mouse e a rolagem.
"""
import pygame

from . import font
from .tela import mouse_pos

AZUL = (90, 170, 255)
VERDE = (90, 200, 110)
VERMELHO = (255, 95, 95)
AMARELO = (255, 205, 80)
CINZA = (150, 156, 178)
BRANCO = (240, 242, 248)
FUNDO_CAMPO = (18, 22, 38)
PALETA = ["#3fa7ff", "#7ad67a", "#ff9f43", "#ff6b81", "#a78bfa", "#2dd4bf", "#facc15", "#f472b6"]


def area_de_transferencia():
    """Texto copiado (Ctrl+C) no Windows/macOS/Linux."""
    try:
        return pygame.scrap.get_text() or ""
    except Exception:
        try:
            import tkinter
            r = tkinter.Tk()
            r.withdraw()
            texto = r.clipboard_get()
            r.destroy()
            return texto
        except Exception:
            return ""


def copiar(texto):
    try:
        pygame.scrap.put_text(texto)
    except Exception:
        pass


class Form:
    def __init__(self, tela):
        self.tela = tela
        self.foco = None            # id do campo que está recebendo o teclado
        self.clique = None          # posição do clique deste quadro
        self.digitado = ""
        self.apagar = 0
        self.colar = None
        self.tab = False
        self.campos = []            # ordem dos campos (para o Tab pular para o próximo)
        self.mostrar = set()        # campos secretos que o usuário pediu para ver
        self.rolagem = 0
        self.area = pygame.Rect(0, 0, *tela.get_size())
        self.altura = 0             # altura total do conteúdo (para limitar a rolagem)
        self.desloc = 0             # quanto a parte atual está rolada
        self.altura_visivel = 0     # altura da área que rola
        self._clicou_campo = False

    # ---------- eventos ----------
    def evento(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.clique = ev.pos
        elif ev.type == pygame.MOUSEWHEEL:
            self.rolagem = max(0, min(self.rolagem - ev.y * 40, max(0, self.altura - self.altura_visivel)))
        elif ev.type == pygame.TEXTINPUT and self.foco:
            self.digitado += ev.text
        elif ev.type == pygame.KEYDOWN and self.foco:
            if ev.key == pygame.K_BACKSPACE:
                self.apagar += 1
            elif ev.key == pygame.K_v and ev.mod & pygame.KMOD_CTRL:
                self.colar = area_de_transferencia()
            elif ev.key == pygame.K_TAB:
                self.tab = True
            elif ev.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                self.foco = None

    def comecar(self, area, rolar=False):
        """Começa uma parte da tela; tudo fora de 'area' fica cortado.

        rolar=True: a parte acompanha a rodinha do mouse (o conteúdo das abas).
        """
        self.area = area
        self.desloc = self.rolagem if rolar else 0
        self.tela.set_clip(area)

    def terminar(self, altura_conteudo=None):
        """Fim de uma parte da tela (abas, conteúdo com rolagem, rodapé)."""
        self.tela.set_clip(None)
        if altura_conteudo is not None:
            self.altura = altura_conteudo
            self.altura_visivel = self.area.h
            self.rolagem = max(0, min(self.rolagem, max(0, self.altura - self.altura_visivel)))

    def fim_do_quadro(self):
        """Fim do quadro inteiro: aplica Tab, tira o foco se clicou fora e limpa o teclado/mouse."""
        if self.tab and self.foco in self.campos:
            i = self.campos.index(self.foco)
            self.foco = self.campos[(i + 1) % len(self.campos)]
        elif self.clique and self.foco and not getattr(self, "_clicou_campo", False):
            self.foco = None                  # clicou fora: tira o foco
        self.clique, self.digitado, self.apagar, self.colar, self.tab = None, "", 0, None, False
        self._clicou_campo = False
        self.campos = []
        self.desloc = 0

    # ---------- utilidades ----------
    def r(self, x, y, w, h):
        """Retângulo na tela, já descontando a rolagem."""
        return pygame.Rect(x, y - self.desloc, w, h)

    def clicou(self, rect):
        if self.clique and rect.collidepoint(self.clique) and self.area.collidepoint(self.clique):
            self.clique = None                # um clique vale para um componente só
            return True
        return False

    def sobre(self, rect):
        m = mouse_pos()
        return rect.collidepoint(m) and self.area.collidepoint(m)

    def texto(self, x, y, texto, cor=BRANCO, escala=2, familia="texto"):
        self.tela.blit(font.render(texto, escala, cor, familia=familia), (x, y - self.desloc))

    def texto_no_meio(self, rect, texto, cor=BRANCO, escala=2):
        """Texto centralizado dentro de um retângulo (já na tela)."""
        t = font.render(texto, escala, cor)
        self.tela.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))

    def paragrafo(self, x, y, texto, largura, cor=CINZA, escala=2):
        """Texto quebrado em linhas que cabem na largura. Devolve o y logo abaixo."""
        for linha in font.wrap(texto, largura, escala):
            self.texto(x, y, linha, cor, escala)
            y += font.altura(escala)
        return y

    def secao(self, x, y, titulo, largura):
        """Título de seção (fonte de fliperama) com uma linha embaixo."""
        self.texto(x, y, titulo.upper(), AZUL, 3, "titulo")
        pygame.draw.line(self.tela, (50, 60, 90), (x, y + 30 - self.desloc), (x + largura, y + 30 - self.desloc), 2)
        return y + 42

    # ---------- componentes ----------
    def botao(self, id_, x, y, w, rotulo, cor=AZUL, h=34, ativo=True):
        w = max(w, font.largura(rotulo) + 28)      # nunca corta o texto
        rect = self.r(x, y, w, h)
        cheio = self.sobre(rect) and ativo
        pygame.draw.rect(self.tela, cor if cheio else tuple(c // 3 for c in cor), rect)
        pygame.draw.rect(self.tela, cor if ativo else CINZA, rect, 2)
        self.texto_no_meio(rect, rotulo, (10, 12, 20) if cheio else BRANCO)
        return ativo and self.clicou(rect)

    def campo(self, id_, x, y, w, valor, secreto=False, dica=""):
        """Caixa de texto. Ctrl+V cola, Tab vai para o próximo, Enter confirma."""
        valor = valor or ""
        self.campos.append(id_)
        larg_campo = w - (70 if secreto else 0)
        rect = self.r(x, y, larg_campo, 34)
        if self.clicou(rect):
            self.foco = id_
            self._clicou_campo = True
        focado = self.foco == id_
        if focado:
            if self.apagar:
                valor = valor[:-self.apagar] if self.apagar <= len(valor) else ""
            valor += self.digitado + (self.colar or "").strip()
        pygame.draw.rect(self.tela, FUNDO_CAMPO, rect)
        pygame.draw.rect(self.tela, AZUL if focado else (70, 76, 100), rect, 2)
        if not valor and not focado:
            mostrado, cor = dica, (90, 96, 120)
        elif secreto and id_ not in self.mostrar:
            mostrado, cor = ("•" * min(12, max(0, len(valor) - 4)) + valor[-4:]) if valor else "", BRANCO
        else:
            mostrado, cor = valor, BRANCO
        cabe = larg_campo - 24
        # digitando: mostra o fim do texto; parado: mostra o começo
        mostrado = font.cauda(mostrado, cabe) if focado else font.cortar(mostrado, cabe)
        t = font.render(mostrado, 2, cor)
        ty = rect.centery - t.get_height() // 2
        self.tela.blit(t, (rect.x + 10, ty))
        if focado and pygame.time.get_ticks() // 450 % 2:      # cursor piscando
            pygame.draw.rect(self.tela, AZUL, (rect.x + 12 + t.get_width(), rect.y + 7, 3, rect.h - 14))
        if secreto:
            olho = "ocultar" if id_ in self.mostrar else "ver"
            if self.botao(id_ + ":olho", x + larg_campo + 6, y, 64, olho, CINZA):
                self.mostrar ^= {id_}
        return valor

    def alternar(self, id_, x, y, valor, rotulo):
        """Interruptor liga/desliga com texto ao lado. Clicar no texto também alterna."""
        rect = self.r(x, y, 52, 28)
        largura_txt = font.largura(rotulo)
        if self.clicou(rect) or self.clicou(self.r(x + 60, y, largura_txt + 10, 28)):
            valor = not valor
        pygame.draw.rect(self.tela, VERDE if valor else (60, 64, 84), rect)
        bolinha = self.r(x + (28 if valor else 4), y + 4, 20, 20)
        pygame.draw.rect(self.tela, BRANCO, bolinha)
        self.texto(x + 64, y + 14 - font.altura() // 2, rotulo, BRANCO if valor else CINZA)
        return valor

    def numero(self, id_, x, y, valor, minimo, maximo, passo=1, formato="{}"):
        if self.botao(id_ + ":-", x, y, 34, "-"):
            valor = max(minimo, valor - passo)
        self.texto(x + 46, y + 17 - font.altura() // 2, formato.format(valor))
        larg = font.largura(formato.format(maximo)) + 24
        if self.botao(id_ + ":+", x + 46 + larg, y, 34, "+"):
            valor = min(maximo, valor + passo)
        return valor

    def hora(self, id_, x, y, valor, passo=15):
        """Seletor de horário HH:MM com - e + (de 15 em 15 minutos)."""
        h, m = map(int, valor.split(":"))
        total = h * 60 + m
        if self.botao(id_ + ":-", x, y, 34, "-"):
            total = (total - passo) % (24 * 60)
        if self.botao(id_ + ":+", x + 118, y, 34, "+"):
            total = (total + passo) % (24 * 60)
        texto = f"{total // 60:02d}:{total % 60:02d}"
        self.texto_no_meio(self.r(x + 34, y, 84, 34), texto)
        return texto

    def opcoes(self, id_, x, y, valor, escolhas, largura=150, por_linha=4):
        """Botões lado a lado; o escolhido fica aceso. escolhas: [(valor, rótulo)]."""
        for i, (v, rotulo) in enumerate(escolhas):
            bx = x + (i % por_linha) * (largura + 8)
            by = y + (i // por_linha) * 42
            if self.botao(f"{id_}:{v}", bx, by, largura, rotulo, VERDE if v == valor else (110, 116, 140)):
                valor = v
        return valor

    def cores(self, id_, x, y, valor):
        for i, hexa in enumerate(PALETA):
            rect = self.r(x + i * 40, y, 32, 32)
            cor = tuple(int(hexa[k:k + 2], 16) for k in (1, 3, 5))
            pygame.draw.rect(self.tela, cor, rect)
            if hexa == valor:
                pygame.draw.rect(self.tela, BRANCO, rect.inflate(6, 6), 3)
            if self.clicou(rect):
                valor = hexa
        return valor

    @staticmethod
    def largura_chip(rotulo):
        return font.largura(rotulo) + 46

    def chip(self, id_, x, y, rotulo, marcado):
        """Caixinha de marcar com texto (serviços, canais do Slack...)."""
        w = self.largura_chip(rotulo)
        rect = self.r(x, y, w, 32)
        if self.clicou(rect):
            marcado = not marcado
        pygame.draw.rect(self.tela, (36, 78, 50) if marcado else FUNDO_CAMPO, rect)
        pygame.draw.rect(self.tela, VERDE if marcado else (70, 76, 100), rect, 2)
        caixa = pygame.Rect(rect.x + 10, rect.centery - 7, 14, 14)
        pygame.draw.rect(self.tela, VERDE if marcado else CINZA, caixa, 2)
        if marcado:   # "v" de marcado desenhado em pixels
            pygame.draw.lines(self.tela, BRANCO, False, [(caixa.x + 3, caixa.y + 7), (caixa.x + 6, caixa.y + 10), (caixa.x + 11, caixa.y + 3)], 2)
        t = font.render(rotulo, 2, BRANCO if marcado else CINZA)
        self.tela.blit(t, (rect.x + 32, rect.centery - t.get_height() // 2))
        return marcado, w

    def status(self, x, y, mensagem):
        """Mensagem de resultado de um botão: (texto, cor)."""
        if mensagem:
            texto, cor = mensagem
            return self.paragrafo(x, y, texto, 860, cor)
        return y

    def qrcode(self, x, y, texto, tamanho=4):
        """Desenha um QR code (o celular lê com a câmera)."""
        try:
            import qrcode
        except ImportError:
            return
        qr = qrcode.QRCode(border=2, box_size=1)
        qr.add_data(texto)
        qr.make(fit=True)
        matriz = qr.get_matrix()
        lado = len(matriz) * tamanho
        pygame.draw.rect(self.tela, (255, 255, 255), self.r(x, y, lado, lado))
        for j, linha in enumerate(matriz):
            for i, preto in enumerate(linha):
                if preto:
                    self.tela.fill((0, 0, 0), self.r(x + i * tamanho, y + j * tamanho, tamanho, tamanho))
        return lado
