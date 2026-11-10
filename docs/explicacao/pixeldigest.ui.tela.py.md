# `pixeldigest/ui/tela.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/ui/tela.py)

Cuida da orientação (horizontal ou vertical) e da escala da tela. Funciona como as "media queries" de um site: o layout muda conforme o formato da janela.

### Linhas 1 a 14

```python
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
```

Docstring: o app sempre desenha numa tela lógica de tamanho fixo (1280x720 na horizontal, 720x1280 na vertical) e depois amplia ou reduz para caber na janela real, mantendo a proporção. Na orientação automática, janela mais alta que larga vira layout vertical. O mouse é convertido para a tela lógica, então o resto do código nem sabe que existe escala.

### Linha 15

```python
import pygame
```

Importa o pygame.

### Linha 17

```python
LOGICO = {"horizontal": (1280, 720), "vertical": (720, 1280)}
```

Tamanho lógico de cada orientação.

### Linhas 18 a 21

```python
RESOLUCOES = {
    "horizontal": ["960x540", "1280x720", "1600x900", "1920x1080"],
    "vertical": ["540x960", "720x1280", "900x1600", "1080x1920"],
}
```

Resoluções de janela oferecidas nas Configurações, todas na proporção 16:9 (ou 9:16).

### Linha 22

```python
ORIENTACOES = [("automatica", "Automática"), ("horizontal", "Horizontal"), ("vertical", "Vertical")]
```

Opções de orientação: valor salvo e texto mostrado.

### Linha 23

```python
EVENTOS_COM_POSICAO = (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION)
```

Tipos de evento do pygame que trazem posição do mouse (apertar, soltar, mover).

### Linhas 26 a 29

```python
def tamanho(texto):
    """'1280x720' -> (1280, 720)."""
    w, h = str(texto).lower().split("x")
    return int(w), int(h)
```

Converte "1280x720" em `(1280, 720)`: minúsculas, separa no "x" e converte para inteiro.

### Linha 32

```python
def orientacao(cfg_tela, janela):
```

Decide o layout para uma janela.

### Linha 33

```python
    """Qual layout usar para esta janela (a 'media query')."""
```

Docstring.

### Linha 34

```python
    escolhida = cfg_tela.get("orientacao", "automatica")
```

Orientação escolhida nas Configurações (padrão automática).

### Linhas 35 a 36

```python
    if escolhida in ("horizontal", "vertical"):
        return escolhida
```

Se foi escolhida uma orientação fixa, usa ela.

### Linhas 37 a 38

```python
    w, h = janela
    return "vertical" if h > w else "horizontal"
```

Automática: vertical se a altura for maior que a largura.

### Linhas 41 a 42

```python
class Viewport:
    """Como a tela lógica é encaixada na janela: escala e deslocamento."""
```

Classe que guarda como a tela lógica é encaixada na janela.

### Linhas 44 a 46

```python
    def __init__(self):
        self.escala, self.ox, self.oy = 1.0, 0, 0
        self.logico = (1280, 720)
```

Começa com escala 1 e sem deslocamento.

### Linha 48

```python
    def ajustar(self, logico, janela):
```

Recalcula a escala para uma tela lógica e uma janela.

### Linhas 49 a 51

```python
        self.logico = logico
        lw, lh = logico
        jw, jh = janela
```

Guarda e separa as larguras e alturas.

### Linha 52

```python
        self.escala = min(jw / lw, jh / lh)
```

A escala é a menor das duas razões, para a tela inteira caber sem cortar (como o "contain" do CSS).

### Linhas 53 a 54

```python
        self.ox = int((jw - lw * self.escala) // 2)
        self.oy = int((jh - lh * self.escala) // 2)
```

Deslocamento para centralizar: o que sobra dividido por 2. O que sobra vira faixa preta.

### Linhas 56 a 58

```python
    def para_logico(self, pos):
        x, y = pos
        return int((x - self.ox) / self.escala), int((y - self.oy) / self.escala)
```

Converte uma posição da janela para a tela lógica: tira o deslocamento e divide pela escala.

### Linha 60

```python
    def apresentar(self, superficie, janela):
```

Copia a tela lógica para a janela.

### Linha 61

```python
        """Copia a tela lógica para a janela, na escala certa."""
```

Docstring.

### Linha 62

```python
        self.ajustar(superficie.get_size(), janela.get_size())
```

Recalcula a escala com os tamanhos atuais.

### Linhas 63 a 65

```python
        if self.escala == 1 and self.ox == 0 and self.oy == 0:
            janela.blit(superficie, (0, 0))
            return
```

Se a escala é 1 e não há deslocamento, copia direto (mais rápido).

### Linha 66

```python
        janela.fill((0, 0, 0))
```

Pinta a janela de preto (as faixas).

### Linha 67

```python
        w, h = int(superficie.get_width() * self.escala), int(superficie.get_height() * self.escala)
```

Tamanho final da imagem ampliada.

### Linha 68

```python
        janela.blit(pygame.transform.scale(superficie, (w, h)), (self.ox, self.oy))
```

Amplia (`transform.scale`) e copia para a janela na posição centralizada.

### Linha 71

```python
VIEW = Viewport()
```

Instância única usada pelo programa todo.

### Linhas 74 a 76

```python
def mouse_pos():
    """Posição do mouse na tela lógica."""
    return VIEW.para_logico(pygame.mouse.get_pos())
```

Posição atual do mouse já na tela lógica. Os widgets usam esta função em vez de `pygame.mouse.get_pos()`.

### Linha 79

```python
def converter(ev):
```

Converte um evento de mouse.

### Linha 80

```python
    """Evento de mouse com a posição já na tela lógica."""
```

Docstring.

### Linhas 81 a 84

```python
    if ev.type in EVENTOS_COM_POSICAO:
        dados = dict(ev.dict)
        dados["pos"] = VIEW.para_logico(ev.pos)
        return pygame.event.Event(ev.type, dados)
```

Se o evento tem posição, copia os dados, troca a posição pela convertida e cria um evento novo do mesmo tipo.

### Linha 85

```python
    return ev
```

Outros eventos (teclado, por exemplo) passam sem mudança.
