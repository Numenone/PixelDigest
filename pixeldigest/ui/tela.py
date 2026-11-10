"""Tamanho da tela, orientação e escala ("media queries" do app).

O app desenha sempre numa tela LÓGICA de tamanho fixo para cada orientação:
- horizontal: 1280x720
- vertical:   720x1280
Depois essa tela é ampliada ou reduzida para caber na janela de verdade, de
qualquer resolução, mantendo a proporção (sobra uma faixa preta se precisar).

Na orientação "automática" vale a regra de media query: janela mais alta que
larga = layout vertical; senão, horizontal. A janela pode ser redimensionada à vontade.

O mouse chega em coordenadas da janela; mouse_pos() e converter() traduzem para
a tela lógica, então o resto do código nem sabe que existe escala.
"""
import pygame

LOGICO = {"horizontal": (1280, 720), "vertical": (720, 1280)}
RESOLUCOES = {
    "horizontal": ["960x540", "1280x720", "1600x900", "1920x1080"],
    "vertical": ["540x960", "720x1280", "900x1600", "1080x1920"],
}
ORIENTACOES = [("automatica", "Automática"), ("horizontal", "Horizontal"), ("vertical", "Vertical")]
EVENTOS_COM_POSICAO = (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION)


def tamanho(texto):
    """'1280x720' -> (1280, 720)."""
    w, h = str(texto).lower().split("x")
    return int(w), int(h)


def orientacao(cfg_tela, janela):
    """Qual layout usar para esta janela (a 'media query')."""
    escolhida = cfg_tela.get("orientacao", "automatica")
    if escolhida in ("horizontal", "vertical"):
        return escolhida
    w, h = janela
    return "vertical" if h > w else "horizontal"


class Viewport:
    """Como a tela lógica é encaixada na janela: escala e deslocamento."""

    def __init__(self):
        self.escala, self.ox, self.oy = 1.0, 0, 0
        self.logico = (1280, 720)

    def ajustar(self, logico, janela):
        self.logico = logico
        lw, lh = logico
        jw, jh = janela
        self.escala = min(jw / lw, jh / lh)
        self.ox = int((jw - lw * self.escala) // 2)
        self.oy = int((jh - lh * self.escala) // 2)

    def para_logico(self, pos):
        x, y = pos
        return int((x - self.ox) / self.escala), int((y - self.oy) / self.escala)

    def apresentar(self, superficie, janela):
        """Copia a tela lógica para a janela, na escala certa."""
        self.ajustar(superficie.get_size(), janela.get_size())
        if self.escala == 1 and self.ox == 0 and self.oy == 0:
            janela.blit(superficie, (0, 0))
            return
        janela.fill((0, 0, 0))
        w, h = int(superficie.get_width() * self.escala), int(superficie.get_height() * self.escala)
        janela.blit(pygame.transform.scale(superficie, (w, h)), (self.ox, self.oy))


VIEW = Viewport()


def mouse_pos():
    """Posição do mouse na tela lógica."""
    return VIEW.para_logico(pygame.mouse.get_pos())


def converter(ev):
    """Evento de mouse com a posição já na tela lógica."""
    if ev.type in EVENTOS_COM_POSICAO:
        dados = dict(ev.dict)
        dados["pos"] = VIEW.para_logico(ev.pos)
        return pygame.event.Event(ev.type, dados)
    return ev
