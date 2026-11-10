"""Texto em pixel art com acentos.

Duas fontes gratuitas (licença OFL, arquivos em ui/fontes/):
- "texto":  Pixelify Sans, para quase tudo (tem todos os acentos do português);
- "titulo": Silkscreen, letras de fliperama para títulos e números grandes.

As fontes são desenhadas SEM suavização (antialias=False), então os pixels ficam
retinhos como num jogo antigo.

"escala" é o tamanho: 1 = pequeno, 2 = normal, 3 = subtítulo ... 10 = enorme.
As funções medem em pixels de verdade, então quebrar linha e cortar com "…"
sempre cabem na largura pedida.
"""
from collections import OrderedDict
from pathlib import Path

import pygame

PASTA = Path(__file__).resolve().parent / "fontes"
ARQUIVOS = {"texto": "PixelifySans.ttf", "titulo": "Silkscreen-Regular.ttf"}
# tamanho em pixels para cada escala (a Silkscreen fica nítida em múltiplos de 8)
TAMANHOS = {
    "texto": {1: 16, 2: 20, 3: 24, 4: 32, 5: 40, 6: 48, 7: 56, 8: 64, 9: 80, 10: 96},
    "titulo": {1: 8, 2: 16, 3: 24, 4: 32, 5: 40, 6: 48, 7: 56, 8: 64, 9: 80, 10: 96},
}

_fontes = {}
_cache = OrderedDict()      # textos já desenhados (os mais usados ficam; o resto sai)
LIMITE_CACHE = 400


def fonte(escala=2, familia="texto"):
    tamanho = TAMANHOS[familia].get(escala, escala * 8)
    chave = (familia, tamanho)
    if chave not in _fontes:
        if not pygame.font.get_init():
            pygame.font.init()
        _fontes[chave] = pygame.font.Font(str(PASTA / ARQUIVOS[familia]), tamanho)
    return _fontes[chave]


def render(texto, escala=2, cor=(255, 255, 255), shadow=None, familia="texto"):
    """Desenha o texto numa Surface transparente (com sombra opcional). Usa cache."""
    chave = (texto, escala, cor, shadow, familia)
    if chave in _cache:
        _cache.move_to_end(chave)
        return _cache[chave]
    f = fonte(escala, familia)
    frente = f.render(texto, False, cor)
    if shadow:
        d = max(1, f.get_height() // 12)          # sombra proporcional ao tamanho
        surf = pygame.Surface((frente.get_width() + d, frente.get_height() + d), pygame.SRCALPHA)
        surf.blit(f.render(texto, False, shadow), (d, d))
        surf.blit(frente, (0, 0))
    else:
        surf = frente
    _cache[chave] = surf
    if len(_cache) > LIMITE_CACHE:
        _cache.popitem(last=False)
    return surf


def largura(texto, escala=2, familia="texto"):
    return fonte(escala, familia).size(texto)[0]


def altura(escala=2, familia="texto"):
    return fonte(escala, familia).get_height()


def cortar(texto, largura_max, escala=2, familia="texto"):
    """Corta o fim do texto com "…" para caber na largura."""
    if largura(texto, escala, familia) <= largura_max:
        return texto
    while texto and largura(texto + "…", escala, familia) > largura_max:
        texto = texto[:-1]
    return texto.rstrip() + "…"


def cauda(texto, largura_max, escala=2, familia="texto"):
    """Mostra só o FINAL do texto ("…fim"), usado no campo que está sendo digitado."""
    if largura(texto, escala, familia) <= largura_max:
        return texto
    while texto and largura("…" + texto, escala, familia) > largura_max:
        texto = texto[1:]
    return "…" + texto


def wrap(texto, largura_max, escala=2, familia="texto"):
    """Quebra o texto em linhas que cabem na largura (por palavra)."""
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = f"{atual} {palavra}" if atual else palavra
        if largura(teste, escala, familia) <= largura_max:
            atual = teste
            continue
        if atual:
            linhas.append(atual)
        while largura(palavra, escala, familia) > largura_max:   # palavra gigante (ex.: um token)
            corte = len(palavra)
            while corte > 1 and largura(palavra[:corte], escala, familia) > largura_max:
                corte -= 1
            linhas.append(palavra[:corte])
            palavra = palavra[corte:]
        atual = palavra
    if atual:
        linhas.append(atual)
    return linhas
