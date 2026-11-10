"""Ícones pixel art desenhados em código (16x16, ampliados sem suavizar).

Cada ícone é uma lista de linhas de texto: cada letra é uma cor da paleta.
Assim dá para "ver" o desenho direto no código.
"""
import pygame

PALETA = {
    "Y": (255, 210, 70), "O": (255, 160, 40), "W": (245, 246, 252), "G": (170, 178, 196),
    "D": (110, 116, 136), "B": (110, 170, 255), "L": (255, 250, 150), "M": (230, 230, 210),
    "K": (24, 26, 36), "R": (235, 80, 90), "C": (120, 220, 140),
}

SOL = [
    ".......Y........",
    "...Y...Y...Y....",
    "....Y.....Y.....",
    "......YYY.......",
    ".....YOOOY......",
    "YY..YOOOOOY..YY.",
    ".....YOOOY......",
    "......YYY.......",
    "....Y.....Y.....",
    "...Y...Y...Y....",
    ".......Y........",
]
LUA = [
    ".....MMMM.......",
    "...MMMM.........",
    "..MMMM..........",
    ".MMMM...........",
    ".MMMM...........",
    ".MMMM...........",
    ".MMMMM......M...",
    "..MMMMMM..MMM...",
    "...MMMMMMMMM....",
    ".....MMMMM......",
]
NUVEM = [
    "......WWWW......",
    "....WWWWWWWW....",
    "..WWWWWWWWWWWW..",
    ".WWWWWWWWWWWWWW.",
    "WWWWWWWWWWWWWWWW",
    "GGGGGGGGGGGGGGGG",
    ".GGGGGGGGGGGGGG.",
]
NUVEM_ESCURA = [linha.replace("W", "G").replace("G", "D", 0) for linha in NUVEM]
GOTAS = [
    "..B...B...B...B.",
    ".B...B...B...B..",
    "................",
    "...B...B...B....",
    "..B...B...B.....",
]
RAIO = [
    "........LL......",
    ".......LL.......",
    "......LLLL......",
    "........LL......",
    ".......L........",
]
NEVOA = [
    "GGGGGGGGGGGG....",
    "................",
    "...GGGGGGGGGGGGG",
    "................",
    "GGGGGGGGGGGGG...",
]
NEVE = [
    "..W...W...W...W.",
    "................",
    "....W...W...W...",
    "................",
    "..W...W...W.....",
]

TAREFA = [
    "KKKKKKKKKK",
    "KWWWWWWWWK",
    "KWWWWWWCWK",
    "KWWWWWCCWK",
    "KWCWWCCWWK",
    "KWCCCCWWWK",
    "KWWCCWWWWK",
    "KWWWWWWWWK",
    "KKKKKKKKKK",
]
MENSAGEM = [
    ".KKKKKKKK.",
    "KWWWWWWWWK",
    "KWDDDDDDWK",
    "KWWWWWWWWK",
    "KWDDDDWWWK",
    "KWWWWWWWWK",
    ".KKKWKKKK.",
    "...KK.....",
    "...K......",
]
EMAIL = [
    "KKKKKKKKKK",
    "KBWWWWWWBK",
    "KWBWWWWBWK",
    "KWWBWWBWWK",
    "KWWWBBWWWK",
    "KWWWWWWWWK",
    "KWWWWWWWWK",
    "KKKKKKKKKK",
]
EVENTO = [
    ".K......K.",
    "KRKRRRRKRK",
    "KRRRRRRRRK",
    "KWWWWWWWWK",
    "KWKWKWKWWK",
    "KWWWWWWWWK",
    "KWKWKWWWWK",
    "KWWWWWWWWK",
    "KKKKKKKKKK",
]

CASA = [
    "....KK....",
    "...KWWK...",
    "..KWWWWK..",
    ".KWWWWWWK.",
    "KKWWWWWWKK",
    ".KWWRRWWK.",
    ".KWWRRWWK.",
    ".KWWRRWWK.",
    ".KKKKKKKK.",
]
ENGRENAGEM = [
    "...K..K...",
    "..KGKKGK..",
    ".KGGGGGGK.",
    "KGGGKKGGGK",
    ".KGK..KGK.",
    ".KGK..KGK.",
    "KGGGKKGGGK",
    ".KGGGGGGK.",
    "..KGKKGK..",
    "...K..K...",
]
LISTA = [
    "KKKKKKKKKK",
    "KWWWWWWWWK",
    "KWCWDDDDWK",
    "KWWWWWWWWK",
    "KWCWDDDDWK",
    "KWWWWWWWWK",
    "KWCWDDDDWK",
    "KWWWWWWWWK",
    "KKKKKKKKKK",
]

_cache = {}


def desenhar(camadas, tamanho):
    """Junta camadas [(sprite, dx, dy)] numa Surface 16x16 e amplia para 'tamanho'."""
    base = pygame.Surface((16, 16), pygame.SRCALPHA)
    for sprite, dx, dy in camadas:
        for y, linha in enumerate(sprite):
            for x, ch in enumerate(linha):
                if ch in PALETA and 0 <= x + dx < 16 and 0 <= y + dy < 16:
                    base.set_at((x + dx, y + dy), PALETA[ch])
    return pygame.transform.scale(base, (tamanho, tamanho))


def clima(codigo, noite=False, tamanho=48):
    """Ícone do tempo pelo código WMO do Open-Meteo."""
    chave = ("clima", codigo, noite, tamanho)
    if chave in _cache:
        return _cache[chave]
    astro = (LUA, 1, 0) if noite else (SOL, 0, 0)
    if codigo <= 1:
        camadas = [astro]
    elif codigo == 2:
        camadas = [astro, (NUVEM, 0, 8)]
    elif codigo == 3:
        camadas = [(NUVEM, 0, 4), (NUVEM_ESCURA, 0, 8)]
    elif codigo in (45, 48):
        camadas = [(NUVEM, 0, 2), (NEVOA, 0, 10)]
    elif 71 <= codigo <= 77 or codigo in (85, 86):
        camadas = [(NUVEM, 0, 2), (NEVE, 0, 10)]
    elif codigo >= 95:
        camadas = [(NUVEM_ESCURA, 0, 2), (RAIO, 0, 9), (GOTAS, 0, 10)]
    elif codigo >= 51:
        camadas = [(NUVEM, 0, 2), (GOTAS, 0, 10)]
    else:
        camadas = [astro]
    _cache[chave] = desenhar(camadas, tamanho)
    return _cache[chave]


def item(tipo, tamanho=20):
    """Ícone do tipo de item do resumo: tarefa, mensagem, email, evento."""
    chave = ("item", tipo, tamanho)
    if chave not in _cache:
        sprite = {"tarefa": TAREFA, "mensagem": MENSAGEM, "email": EMAIL, "evento": EVENTO,
                  "casa": CASA, "engrenagem": ENGRENAGEM, "lista": LISTA}.get(tipo, TAREFA)
        _cache[chave] = desenhar([(sprite, 3, 3)], tamanho)
    return _cache[chave]
