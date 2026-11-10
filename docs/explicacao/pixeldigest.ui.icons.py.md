# `pixeldigest/ui/icons.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/ui/icons.py)

Ícones em pixel art desenhados direto no código, sem nenhum arquivo de imagem. Cada ícone é uma lista de textos em que cada letra é uma cor.

### Linhas 1 a 5

```python
"""Ícones pixel art desenhados em código (16x16, ampliados sem suavizar).

Cada ícone é uma lista de linhas de texto: cada letra é uma cor da paleta.
Assim dá para "ver" o desenho direto no código.
"""
```

Docstring: os ícones têm 16x16 pixels e são ampliados sem suavizar (o que mantém o visual de pixel art). Como cada letra é uma cor, dá para "ver" o desenho no código.

### Linha 6

```python
import pygame
```

Importa o pygame.

### Linhas 8 a 12

```python
PALETA = {
    "Y": (255, 210, 70), "O": (255, 160, 40), "W": (245, 246, 252), "G": (170, 178, 196),
    "D": (110, 116, 136), "B": (110, 170, 255), "L": (255, 250, 150), "M": (230, 230, 210),
    "K": (24, 26, 36), "R": (235, 80, 90), "C": (120, 220, 140),
}
```

Paleta: cada letra vira uma cor RGB. Y amarelo, O laranja, W branco, G cinza, D cinza escuro, B azul, L amarelo claro, M bege, K quase preto, R vermelho, C verde. O ponto (`.`) não está na paleta, então fica transparente.

### Linhas 14 a 26

```python
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
```

Sol: raios de "Y" em volta de um centro "O".

### Linhas 27 a 38

```python
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
```

Lua crescente em "M".

### Linhas 39 a 47

```python
NUVEM = [
    "......WWWW......",
    "....WWWWWWWW....",
    "..WWWWWWWWWWWW..",
    ".WWWWWWWWWWWWWW.",
    "WWWWWWWWWWWWWWWW",
    "GGGGGGGGGGGGGGGG",
    ".GGGGGGGGGGGGGG.",
]
```

Nuvem: parte de cima branca e base cinza (sombra).

### Linha 48

```python
NUVEM_ESCURA = [linha.replace("W", "G").replace("G", "D", 0) for linha in NUVEM]
```

Nuvem escura gerada a partir da nuvem: troca W por G. O segundo `replace` com 0 não troca nada (fica como estava); a nuvem escura é a versão em cinza.

### Linhas 49 a 55

```python
GOTAS = [
    "..B...B...B...B.",
    ".B...B...B...B..",
    "................",
    "...B...B...B....",
    "..B...B...B.....",
]
```

Gotas de chuva em azul.

### Linhas 56 a 62

```python
RAIO = [
    "........LL......",
    ".......LL.......",
    "......LLLL......",
    "........LL......",
    ".......L........",
]
```

Raio em amarelo claro.

### Linhas 63 a 69

```python
NEVOA = [
    "GGGGGGGGGGGG....",
    "................",
    "...GGGGGGGGGGGGG",
    "................",
    "GGGGGGGGGGGGG...",
]
```

Névoa: faixas cinzas.

### Linhas 70 a 76

```python
NEVE = [
    "..W...W...W...W.",
    "................",
    "....W...W...W...",
    "................",
    "..W...W...W.....",
]
```

Neve: pontos brancos.

### Linhas 78 a 88

```python
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
```

Ícone de tarefa: caixa com um sinal de visto verde.

### Linhas 89 a 99

```python
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
```

Balão de mensagem.

### Linhas 100 a 109

```python
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
```

Envelope de e-mail.

### Linhas 110 a 120

```python
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
```

Calendário com o topo vermelho.

### Linhas 122 a 132

```python
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
```

Casa (aba Início).

### Linhas 133 a 144

```python
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
```

Engrenagem (aba Configurações).

### Linhas 145 a 155

```python
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
```

Lista (aba Resumo).

### Linha 157

```python
_cache = {}
```

Cache dos ícones já desenhados (desenhar pixel por pixel é lento, então cada ícone é desenhado uma vez só).

### Linha 160

```python
def desenhar(camadas, tamanho):
```

Desenha camadas de sprites numa superfície de 16x16 e amplia.

### Linha 161

```python
    """Junta camadas [(sprite, dx, dy)] numa Surface 16x16 e amplia para 'tamanho'."""
```

Docstring: cada camada é (sprite, deslocamento x, deslocamento y).

### Linha 162

```python
    base = pygame.Surface((16, 16), pygame.SRCALPHA)
```

Superfície transparente (`SRCALPHA`) de 16x16.

### Linhas 163 a 167

```python
    for sprite, dx, dy in camadas:
        for y, linha in enumerate(sprite):
            for x, ch in enumerate(linha):
                if ch in PALETA and 0 <= x + dx < 16 and 0 <= y + dy < 16:
                    base.set_at((x + dx, y + dy), PALETA[ch])
```

Para cada camada, cada linha e cada letra: se a letra está na paleta e o pixel cabe dentro dos 16x16, pinta aquele pixel. `enumerate` dá a posição (y da linha, x da letra).

### Linha 168

```python
    return pygame.transform.scale(base, (tamanho, tamanho))
```

Amplia para o tamanho pedido. O `transform.scale` não suaviza, então cada pixel vira um quadrado.

### Linha 171

```python
def clima(codigo, noite=False, tamanho=48):
```

Ícone do clima pelo código WMO.

### Linha 172

```python
    """Ícone do tempo pelo código WMO do Open-Meteo."""
```

Docstring.

### Linhas 173 a 175

```python
    chave = ("clima", codigo, noite, tamanho)
    if chave in _cache:
        return _cache[chave]
```

Chave do cache e devolução se já existir.

### Linha 176

```python
    astro = (LUA, 1, 0) if noite else (SOL, 0, 0)
```

Astro: lua à noite, sol de dia.

### Linhas 177 a 178

```python
    if codigo <= 1:
        camadas = [astro]
```

Céu limpo ou quase (0 e 1): só o astro.

### Linhas 179 a 180

```python
    elif codigo == 2:
        camadas = [astro, (NUVEM, 0, 8)]
```

Parcialmente nublado (2): astro com nuvem por baixo.

### Linhas 181 a 182

```python
    elif codigo == 3:
        camadas = [(NUVEM, 0, 4), (NUVEM_ESCURA, 0, 8)]
```

Nublado (3): nuvem clara atrás e escura na frente, sem astro.

### Linhas 183 a 184

```python
    elif codigo in (45, 48):
        camadas = [(NUVEM, 0, 2), (NEVOA, 0, 10)]
```

Neblina: nuvem com névoa.

### Linhas 185 a 186

```python
    elif 71 <= codigo <= 77 or codigo in (85, 86):
        camadas = [(NUVEM, 0, 2), (NEVE, 0, 10)]
```

Neve: nuvem com neve.

### Linhas 187 a 188

```python
    elif codigo >= 95:
        camadas = [(NUVEM_ESCURA, 0, 2), (RAIO, 0, 9), (GOTAS, 0, 10)]
```

Trovoada (95 ou mais): nuvem escura, raio e gotas.

### Linhas 189 a 190

```python
    elif codigo >= 51:
        camadas = [(NUVEM, 0, 2), (GOTAS, 0, 10)]
```

Garoa e chuva (51 a 94): nuvem com gotas.

### Linhas 191 a 192

```python
    else:
        camadas = [astro]
```

Qualquer outro código: só o astro.

### Linhas 193 a 194

```python
    _cache[chave] = desenhar(camadas, tamanho)
    return _cache[chave]
```

Desenha, guarda no cache e devolve.

### Linha 197

```python
def item(tipo, tamanho=20):
```

Ícone de um tipo de item ou aba.

### Linha 198

```python
    """Ícone do tipo de item do resumo: tarefa, mensagem, email, evento."""
```

Docstring.

### Linhas 199 a 204

```python
    chave = ("item", tipo, tamanho)
    if chave not in _cache:
        sprite = {"tarefa": TAREFA, "mensagem": MENSAGEM, "email": EMAIL, "evento": EVENTO,
                  "casa": CASA, "engrenagem": ENGRENAGEM, "lista": LISTA}.get(tipo, TAREFA)
        _cache[chave] = desenhar([(sprite, 3, 3)], tamanho)
    return _cache[chave]
```

Escolhe o sprite pelo nome (tarefa como padrão), desenha deslocado 3 pixels para centralizar e guarda no cache.
