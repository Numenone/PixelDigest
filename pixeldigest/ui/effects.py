"""Animações que aparecem por cima da tela.

Cada efeito tem um tempo de vida (dur) e dois desenhos opcionais:
- draw_baixa(surf): desenha no cenário pequeno (320x180), vira pixel grande;
- draw(tela): desenha na tela grande (1280x720), para textos e cartões.

Efeitos: BomDia (07:00), FimDia (18:00), Agendado (reunião marcada),
Alarme (alarme do celular), Toast (aviso rápido) e Confete.
"""
import math
import random

import pygame

from . import font

# Centro horizontal e altura do texto grande; a tela principal ajusta conforme a orientação
CX = 640
BANNER_Y = 250
LARGURA_TELA = 1280

# ---------- sprites em texto: cada letra é uma cor ----------
CALENDARIO = [
    "..K..........K..",
    ".RKRRRRRRRRRRKR.",
    ".RKRRRRRRRRRRKR.",
    ".RRRRRRRRRRRRRR.",
    ".RRRRRRRRRRRRRR.",
    ".WWWWWWWWWWWWWW.",
    ".WWWWWWWWWWWWWW.",
    ".WWWWWWWWWWWWWW.",
    ".WWWWWWWWWWWWWW.",
    ".WWWWWWWWWWWWWW.",
    ".WWWWWWWWWWWWWW.",
    ".WWWWWWWWWWWWWW.",
    ".WWWWWWWWWWWWWW.",
    ".WWWWWWWWWWWWWW.",
    ".GGGGGGGGGGGGGG.",
]
DESPERTADOR = [
    ".YY..........YY.",
    "YYYY........YYYY",
    "YYY..KKKKKK..YYY",
    ".Y.KKWWWWWWKK.Y.",
    "..KWWWWKWWWWWK..",
    ".KWWWWWKWWWWWWK.",
    ".KWWWWWKWWWWWWK.",
    "KWWWWWWKWWWWWWWK",
    "KWWWWWWKKKKWWWWK",
    "KWWWWWWWWWWWWWWK",
    ".KWWWWWWWWWWWWK.",
    ".KWWWWWWWWWWWWK.",
    "..KWWWWWWWWWWK..",
    "...KKWWWWWWKK...",
    "..K..KKKKKK..K..",
    ".K............K.",
]
CORES = {"K": (30, 30, 40), "R": (220, 60, 70), "W": (250, 250, 250), "G": (190, 190, 200), "Y": (255, 200, 60)}


def sprite(linhas, escala, cores=CORES):
    s = pygame.Surface((len(linhas[0]) * escala, len(linhas) * escala), pygame.SRCALPHA)
    for y, linha in enumerate(linhas):
        for x, ch in enumerate(linha):
            if ch in cores:
                s.fill(cores[ch], (x * escala, y * escala, escala, escala))
    return s


def ease_out_back(t):
    """Passa um pouco do ponto e volta (efeito 'mola')."""
    c = 1.7
    t -= 1
    return 1 + (c + 1) * t ** 3 + c * t ** 2


def centro(tela, surf, y, cx=None):
    cx = CX if cx is None else cx          # CX muda com a orientação: lê o valor na hora
    tela.blit(surf, (cx - surf.get_width() // 2, y))


class Efeito:
    dur = 3.0
    bloqueia = False      # True: fica até o usuário fechar (alarme)

    def __init__(self):
        self.t = 0.0
        self.vivo = True

    def update(self, dt):
        self.t += dt
        if self.t >= self.dur and not self.bloqueia:
            self.vivo = False

    def fechar(self):
        self.vivo = False

    def draw_baixa(self, surf):
        pass

    def draw(self, tela):
        pass


class Confete(Efeito):
    CORES = [(255, 90, 90), (255, 200, 60), (90, 200, 255), (120, 230, 120), (220, 120, 255)]

    def __init__(self, x, y, n=90, dur=3.0):
        super().__init__()
        self.dur = dur
        self.p = [[x, y, random.uniform(-380, 380), random.uniform(-620, -150), random.choice(self.CORES)] for _ in range(n)]

    def update(self, dt):
        super().update(dt)
        for p in self.p:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 900 * dt          # gravidade

    def draw(self, tela):
        for x, y, *_, cor in self.p:
            tela.fill(cor, (int(x) // 4 * 4, int(y) // 4 * 4, 8, 8))   # "trava" na grade de 4 px


class Banner(Efeito):
    """Texto grande com as letras caindo uma a uma."""

    def __init__(self, texto, sub="", cor=(255, 255, 255), dur=4.5, y=None):
        super().__init__()
        self.texto, self.sub, self.cor, self.dur = texto.upper(), sub, cor, dur
        self.y = BANNER_Y if y is None else y

    def alpha(self):
        return max(0, min(255, int(255 * (self.dur - self.t) / 0.6)))

    def draw(self, tela):
        # o maior tamanho que cabe na largura da tela (vertical é mais estreita)
        escala = next((e for e in (6, 5, 4, 3) if font.largura(self.texto, e, "titulo") <= LARGURA_TELA - 60), 3)
        largura = font.largura(self.texto, escala, "titulo")
        x0 = CX - largura // 2
        a = self.alpha()
        for i, ch in enumerate(self.texto):
            t = max(0.0, min(1.0, (self.t - i * 0.05) / 0.5))
            if t <= 0 or ch == " ":
                continue
            y = self.y - 220 * (1 - ease_out_back(t))
            letra = font.render(ch, escala, self.cor, shadow=(20, 20, 30), familia="titulo").copy()
            letra.set_alpha(a)
            # cada letra cai no lugar dela: a posição é a largura do texto antes dela
            tela.blit(letra, (x0 + font.largura(self.texto[:i], escala, "titulo"), int(y)))
        if self.sub and self.t > 0.8:
            s = font.render(self.sub, 3, (240, 240, 240), shadow=(20, 20, 30)).copy()
            s.set_alpha(a)
            centro(tela, s, self.y + 80)


class BomDia(Efeito):
    """07:00: o sol nasce rápido, a tela ganha um brilho quente e aparece o 'BOM DIA'."""
    dur = 6.5

    def __init__(self, nome, n_itens):
        super().__init__()
        self.banner = Banner(f"BOM DIA, {nome}!", f"{n_itens} itens no seu resumo de hoje", (255, 214, 90), self.dur)

    def update(self, dt):
        super().update(dt)
        self.banner.update(dt)

    def draw_baixa(self, surf):
        p = min(1.0, self.t / 2.5)
        y = int(175 - 110 * math.sin(p * math.pi / 2))
        brilho = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        brilho.fill((255, 170, 80, int(110 * (1 - self.t / self.dur))))
        surf.blit(brilho, (0, 0))
        for i in range(12):                  # raios girando
            ang = self.t * 0.8 + i * math.pi / 6
            x2, y2 = CX // 4 + math.cos(ang) * 34, y + math.sin(ang) * 34
            pygame.draw.line(surf, (255, 226, 120), (CX // 4, y), (int(x2), int(y2)))
        pygame.draw.circle(surf, (255, 200, 80), (CX // 4, y), 18)
        pygame.draw.circle(surf, (255, 236, 130), (CX // 4, y), 13)

    def draw(self, tela):
        self.banner.draw(tela)


class FimDia(Efeito):
    """18:00: a lua sobe, as janelas da cidade acendem e aparece 'FIM DO EXPEDIENTE'."""
    dur = 6.5

    def __init__(self):
        super().__init__()
        self.banner = Banner("FIM DO EXPEDIENTE", "bom descanso!", (190, 170, 255), self.dur)
        self.estrelas = [(random.randint(0, 319), random.randint(0, 90), random.random() * 3) for _ in range(40)]

    def update(self, dt):
        super().update(dt)
        self.banner.update(dt)

    def draw_baixa(self, surf):
        p = min(1.0, self.t / 2.5)
        noite = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        noite.fill((20, 10, 60, int(120 * p * (1 - max(0, self.t - 5) / 1.5))))
        surf.blit(noite, (0, 0))
        y = int(170 - 120 * math.sin(p * math.pi / 2))
        cor_ceu = surf.get_at((150, max(0, y - 20)))[:3]
        pygame.draw.circle(surf, (236, 236, 214), (150, y), 14)
        pygame.draw.circle(surf, cor_ceu, (156, y - 4), 12)      # recorte com a cor do céu = lua crescente
        for x, ys, atraso in self.estrelas:
            if self.t > atraso and int((self.t + atraso) * 4) % 3:
                surf.set_at((x, ys), (255, 255, 220))

    def draw(self, tela):
        self.banner.draw(tela)


class Agendado(Efeito):
    """Reunião marcada: o calendário entra voando, ganha o carimbo e solta confete."""
    dur = 5.0

    def __init__(self, pessoa, quando, assunto):
        super().__init__()
        self.pessoa, self.quando, self.assunto = pessoa, quando, assunto
        self.cal = sprite(CALENDARIO, 14)
        self.confete = None

    def update(self, dt):
        super().update(dt)
        if self.t > 1.1 and self.confete is None:
            self.confete = Confete(CX, 330, 120)
        if self.confete:
            self.confete.update(dt)

    def draw(self, tela):
        p = min(1.0, self.t / 0.9)
        y = int(760 - (760 - 150) * ease_out_back(p))
        x = CX - self.cal.get_width() // 2
        fade = max(0, min(255, int(255 * (self.dur - self.t) / 0.6)))
        cal = self.cal.copy()
        cal.set_alpha(fade)
        tela.blit(cal, (x, y))
        dia = font.render(self.quando.split()[1][:5] if " " in self.quando else self.quando, 5, (40, 40, 50), familia="titulo")
        dia = dia.copy()
        dia.set_alpha(fade)
        tela.blit(dia, (x + (self.cal.get_width() - dia.get_width()) // 2, y + 105))
        if self.t > 1.1:
            # carimbo: começa grande e "bate" no tamanho certo, com tremida
            q = min(1.0, (self.t - 1.1) / 0.25)
            escala = int(9 - 4 * q)
            tremida = int(math.sin(self.t * 60) * 6 * (1 - q))
            carimbo = font.render("AGENDADO!", escala, (60, 200, 90), shadow=(10, 40, 20), familia="titulo").copy()
            carimbo.set_alpha(fade)
            centro(tela, carimbo, 470 + tremida)
            info = font.render(f"{self.quando} com {self.pessoa}", 3, (255, 255, 255), shadow=(20, 20, 30)).copy()
            info.set_alpha(fade)
            centro(tela, info, 540)
        if self.confete:
            self.confete.draw(tela)


class Alarme(Efeito):
    """Alarme do celular: despertador tremendo, borda piscando. Fica até fechar."""
    dur = 45.0
    bloqueia = True

    def __init__(self, titulo, texto):
        super().__init__()
        self.titulo, self.texto = titulo, texto
        self.relogio = sprite(DESPERTADOR, 16)

    def update(self, dt):
        super().update(dt)
        if self.t > self.dur:
            self.vivo = False

    def draw(self, tela):
        w, h = tela.get_size()
        pisca = (math.sin(self.t * 10) + 1) / 2
        borda = int(10 + 14 * pisca)
        cor = (255, int(60 + 80 * pisca), 60)
        for r in [(0, 0, w, borda), (0, h - borda, w, borda), (0, 0, borda, h), (w - borda, 0, borda, h)]:
            tela.fill(cor, r)
        fundo = pygame.Surface((w, h), pygame.SRCALPHA)
        fundo.fill((60, 0, 0, 90))
        tela.blit(fundo, (0, 0))
        dx = int(math.sin(self.t * 45) * 10)
        ang = math.sin(self.t * 30) * 8
        relogio = pygame.transform.rotate(self.relogio, ang)
        tela.blit(relogio, ((w - relogio.get_width()) // 2 + dx, 110))
        caixa = pygame.Surface((760, 170), pygame.SRCALPHA)
        caixa.fill((30, 0, 0, 170))
        tela.blit(caixa, (w // 2 - 380, 386))
        centro(tela, font.render("ALARME!", 8, (255, 240, 120), shadow=(60, 0, 0), familia="titulo"), 396, w // 2)
        centro(tela, font.render(self.texto or self.titulo, 3, (255, 255, 255), shadow=(60, 0, 0)), 476, w // 2)
        if int(self.t * 2) % 2:
            centro(tela, font.render("clique ou aperte qualquer tecla", 2, (255, 220, 220)), 516, w // 2)


class Toast(Efeito):
    """Aviso rápido que desliza do topo."""
    dur = 6.0
    topo_base = 140           # a tela muda para baixo quando o resumo dos e-mails está aberto

    def __init__(self, titulo, texto, cor=(90, 170, 255)):
        super().__init__()
        self.titulo, self.texto, self.cor = titulo, texto, cor

    def draw(self, tela, indice=0):
        entrada = min(1.0, self.t / 0.35)
        saida = min(1.0, max(0.0, (self.dur - self.t) / 0.35))
        p = min(entrada, saida)
        largura, altura = 620, 80
        x = CX - largura // 2
        topo = Toast.topo_base + indice * (altura + 10)          # logo abaixo da barra do topo
        y = int(topo - 40 * (1 - ease_out_back(p)))
        caixa_alpha = int(255 * p)
        caixa = pygame.Surface((largura, altura), pygame.SRCALPHA)
        caixa.fill((14, 16, 28, 225))
        caixa.fill(self.cor, (0, 0, 8, altura))
        caixa.blit(font.render(font.cortar(self.titulo, largura - 40), 2, self.cor), (22, 8))
        linhas = font.wrap(self.texto, largura - 40, 1)
        if len(linhas) > 2:
            linhas = [linhas[0], font.cortar(" ".join(linhas[1:]), largura - 40, 1)]
        for i, l in enumerate(linhas[:2]):
            caixa.blit(font.render(l, 1, (235, 235, 240)), (22, 36 + i * 19))
        caixa.set_alpha(caixa_alpha)
        tela.blit(caixa, (x, y))
