# `pixeldigest/ui/font.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/ui/font.py)

Desenho de texto em pixel art, com acentos. Também mede, corta e quebra textos para caberem em qualquer largura.

### Linhas 1 a 13

```python
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
```

Docstring: duas fontes gratuitas de licença OFL (Pixelify Sans para o texto, Silkscreen para títulos), desenhadas sem suavização para os pixels ficarem retos. A "escala" vai de 1 a 10 e as funções medem em pixels reais.

### Linha 14

```python
from collections import OrderedDict
```

Importa `OrderedDict`, um dicionário que lembra a ordem de inserção. É a base do cache LRU (descarta o usado há mais tempo).

### Linha 15

```python
from pathlib import Path
```

Importa `Path`.

### Linha 17

```python
import pygame
```

Importa o pygame.

### Linha 19

```python
PASTA = Path(__file__).resolve().parent / "fontes"
```

Pasta das fontes, ao lado deste arquivo.

### Linha 20

```python
ARQUIVOS = {"texto": "PixelifySans.ttf", "titulo": "Silkscreen-Regular.ttf"}
```

Arquivo de cada família.

### Linhas 21 a 25

```python
# tamanho em pixels para cada escala (a Silkscreen fica nítida em múltiplos de 8)
TAMANHOS = {
    "texto": {1: 16, 2: 20, 3: 24, 4: 32, 5: 40, 6: 48, 7: 56, 8: 64, 9: 80, 10: 96},
    "titulo": {1: 8, 2: 16, 3: 24, 4: 32, 5: 40, 6: 48, 7: 56, 8: 64, 9: 80, 10: 96},
}
```

Tamanho em pixels de cada escala. O comentário explica: a Silkscreen fica nítida em múltiplos de 8.

### Linha 27

```python
_fontes = {}
```

Cache dos objetos de fonte já carregados.

### Linha 28

```python
_cache = OrderedDict()      # textos já desenhados (os mais usados ficam; o resto sai)
```

Cache dos textos já desenhados. Desenhar texto é caro; como a tela redesenha 30 vezes por segundo os mesmos textos, reaproveitar economiza muito processamento.

### Linha 29

```python
LIMITE_CACHE = 400
```

Limite do cache (400 textos), para a memória não crescer sem parar.

### Linha 32

```python
def fonte(escala=2, familia="texto"):
```

Devolve o objeto de fonte de uma escala e família.

### Linha 33

```python
    tamanho = TAMANHOS[familia].get(escala, escala * 8)
```

Tamanho pela tabela; se a escala não estiver nela, usa escala vezes 8.

### Linha 34

```python
    chave = (familia, tamanho)
```

Chave do cache.

### Linhas 35 a 38

```python
    if chave not in _fontes:
        if not pygame.font.get_init():
            pygame.font.init()
        _fontes[chave] = pygame.font.Font(str(PASTA / ARQUIVOS[familia]), tamanho)
```

Se ainda não carregou essa fonte: garante que o módulo de fontes do pygame foi iniciado e carrega o arquivo TTF no tamanho pedido.

### Linha 39

```python
    return _fontes[chave]
```

Devolve.

### Linha 42

```python
def render(texto, escala=2, cor=(255, 255, 255), shadow=None, familia="texto"):
```

Desenha um texto e devolve uma superfície transparente.

### Linha 43

```python
    """Desenha o texto numa Surface transparente (com sombra opcional). Usa cache."""
```

Docstring.

### Linha 44

```python
    chave = (texto, escala, cor, shadow, familia)
```

A chave do cache junta tudo o que muda o desenho: texto, escala, cor, sombra e família.

### Linhas 45 a 47

```python
    if chave in _cache:
        _cache.move_to_end(chave)
        return _cache[chave]
```

Se já existe no cache, move para o fim (marca como usado agora) e devolve.

### Linha 48

```python
    f = fonte(escala, familia)
```

Pega a fonte.

### Linha 49

```python
    frente = f.render(texto, False, cor)
```

Desenha o texto. O `False` desliga a suavização (antialias).

### Linhas 50 a 54

```python
    if shadow:
        d = max(1, f.get_height() // 12)          # sombra proporcional ao tamanho
        surf = pygame.Surface((frente.get_width() + d, frente.get_height() + d), pygame.SRCALPHA)
        surf.blit(f.render(texto, False, shadow), (d, d))
        surf.blit(frente, (0, 0))
```

Com sombra: calcula o deslocamento proporcional ao tamanho (no mínimo 1 pixel), cria uma superfície um pouco maior, desenha o texto na cor da sombra deslocado e o texto normal por cima.

### Linhas 55 a 56

```python
    else:
        surf = frente
```

Sem sombra, usa o desenho direto.

### Linha 57

```python
    _cache[chave] = surf
```

Guarda no cache.

### Linhas 58 a 59

```python
    if len(_cache) > LIMITE_CACHE:
        _cache.popitem(last=False)
```

Se passou do limite, remove o mais antigo (`last=False` remove do começo).

### Linha 60

```python
    return surf
```

Devolve.

### Linhas 63 a 64

```python
def largura(texto, escala=2, familia="texto"):
    return fonte(escala, familia).size(texto)[0]
```

Largura em pixels de um texto (`size` devolve largura e altura).

### Linhas 67 a 68

```python
def altura(escala=2, familia="texto"):
    return fonte(escala, familia).get_height()
```

Altura de uma linha.

### Linha 71

```python
def cortar(texto, largura_max, escala=2, familia="texto"):
```

Corta o fim do texto com reticências para caber.

### Linha 72

```python
    """Corta o fim do texto com "…" para caber na largura."""
```

Docstring.

### Linhas 73 a 74

```python
    if largura(texto, escala, familia) <= largura_max:
        return texto
```

Se já cabe, devolve igual.

### Linhas 75 a 76

```python
    while texto and largura(texto + "…", escala, familia) > largura_max:
        texto = texto[:-1]
```

Enquanto o texto mais as reticências não couber, tira a última letra.

### Linha 77

```python
    return texto.rstrip() + "…"
```

Devolve sem espaço no fim, com as reticências.

### Linha 80

```python
def cauda(texto, largura_max, escala=2, familia="texto"):
```

Mostra só o final do texto.

### Linha 81

```python
    """Mostra só o FINAL do texto ("…fim"), usado no campo que está sendo digitado."""
```

Docstring: usado no campo que está sendo digitado, para ver o que acabou de digitar.

### Linhas 82 a 86

```python
    if largura(texto, escala, familia) <= largura_max:
        return texto
    while texto and largura("…" + texto, escala, familia) > largura_max:
        texto = texto[1:]
    return "…" + texto
```

Mesma ideia da função anterior, mas tirando letras do começo e pondo as reticências na frente.

### Linha 89

```python
def wrap(texto, largura_max, escala=2, familia="texto"):
```

Quebra o texto em linhas.

### Linha 90

```python
    """Quebra o texto em linhas que cabem na largura (por palavra)."""
```

Docstring.

### Linha 91

```python
    linhas, atual = [], ""
```

Lista de linhas e a linha atual.

### Linha 92

```python
    for palavra in texto.split():
```

Para cada palavra.

### Linha 93

```python
        teste = f"{atual} {palavra}" if atual else palavra
```

Testa a linha atual com a palavra nova.

### Linhas 94 a 96

```python
        if largura(teste, escala, familia) <= largura_max:
            atual = teste
            continue
```

Se cabe, aceita e vai para a próxima palavra.

### Linhas 97 a 98

```python
        if atual:
            linhas.append(atual)
```

Se não cabe, fecha a linha atual.

### Linhas 99 a 104

```python
        while largura(palavra, escala, familia) > largura_max:   # palavra gigante (ex.: um token)
            corte = len(palavra)
            while corte > 1 and largura(palavra[:corte], escala, familia) > largura_max:
                corte -= 1
            linhas.append(palavra[:corte])
            palavra = palavra[corte:]
```

Se a palavra sozinha não cabe (ex.: um token enorme), corta a palavra em pedaços que cabem: procura o maior corte possível, coloca como linha e continua com o resto.

### Linha 105

```python
        atual = palavra
```

A palavra (ou o que sobrou dela) começa a nova linha.

### Linhas 106 a 107

```python
    if atual:
        linhas.append(atual)
```

Fecha a última linha.

### Linha 108

```python
    return linhas
```

Devolve as linhas.
