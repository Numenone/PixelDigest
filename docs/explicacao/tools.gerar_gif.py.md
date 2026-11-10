# `tools/gerar_gif.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../tools/gerar_gif.py)

Script auxiliar que gera o GIF animado do README (`docs/img/demo.gif`): o clima passando de sol para tempestade e uma reunião sendo agendada. Usa o modo demonstração, então nenhum dado real aparece.

### Linhas 1 a 4

```python
"""Gera docs/img/demo.gif: o clima mudando de sol para tempestade e uma reunião agendada.

Rodar: python tools/gerar_gif.py   (precisa do Pillow: pip install -r requirements-dev.txt)
"""
```

Docstring: o que o script faz e como rodar (precisa do Pillow, que está em `requirements-dev.txt`).

### Linhas 5 a 8

```python
import os
import sys
from datetime import datetime
from pathlib import Path
```

Imports: `os`, `sys`, `datetime` e `Path`.

### Linha 10

```python
os.environ["SDL_VIDEODRIVER"] = "dummy"
```

Driver de vídeo falso: o pygame desenha na memória, sem abrir janela.

### Linha 11

```python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
```

Coloca a raiz do projeto no começo do caminho de busca de módulos, para o `import pixeldigest` funcionar rodando o script da pasta `tools/`.

### Linhas 13 a 20

```python
import pygame  # noqa: E402
from PIL import Image  # noqa: E402

from pixeldigest import config  # noqa: E402
from pixeldigest.core import Motor  # noqa: E402
from pixeldigest.meetings import rotulo  # noqa: E402
from pixeldigest.ui import effects  # noqa: E402
from pixeldigest.ui.app import App  # noqa: E402
```

Imports que precisam vir depois das duas linhas acima. O comentário `noqa: E402` avisa ao verificador de estilo que os imports fora do topo são de propósito.

### Linhas 22 a 23

```python
pygame.init()
tela = pygame.display.set_mode((1280, 720))
```

Inicia o pygame e cria a "janela" falsa de 1280x720.

### Linha 24

```python
cfg = config.carregar(demo=True)
```

Configuração em modo demonstração.

### Linhas 25 a 26

```python
motor = Motor(cfg)
motor.atualizar_resumo(avisar_urgentes=False)
```

Cria o motor e monta o resumo de exemplo.

### Linhas 27 a 28

```python
app = App(cfg, motor, tela)
app.receber()
```

Cria a tela e recebe os eventos do motor.

### Linhas 29 a 30

```python
alvo = datetime.now().astimezone().replace(hour=14, minute=20)
app.desloc_horas = (alvo - datetime.now().astimezone()).total_seconds() / 3600
```

Adianta o relógio do cenário para 14:20 (dia claro), calculando a diferença em horas.

### Linha 32

```python
quadros = []
```

Lista de quadros capturados.

### Linha 33

```python
roteiro = [("sol", 30), ("nublado", 40), ("chuva", 45), ("tempestade", 60)]
```

Roteiro: cada clima e quantos quadros ele dura.

### Linhas 34 a 36

```python
for preset, n in roteiro:
    app.preset = preset
    app.cena.definir_clima(preset=preset)
```

Para cada clima, força o preset no cenário.

### Linhas 37 a 40

```python
    for i in range(n):
        app.quadro(1 / 15)
        if i % 2 == 0:
            quadros.append(pygame.image.tobytes(tela, "RGB"))
```

Desenha os quadros (a 15 por segundo) e guarda um a cada dois, como bytes RGB.

### Linhas 41 a 42

```python
h = motor.agendador.conector.horarios_livres("", 30, [])[0]
app.efeitos.append(effects.Agendado("Ana", rotulo(h), "Reunião"))
```

Pega um horário livre da demonstração e começa a animação de reunião agendada.

### Linhas 43 a 46

```python
for i in range(70):
    app.quadro(1 / 15)
    if i % 2 == 0:
        quadros.append(pygame.image.tobytes(tela, "RGB"))
```

Desenha mais 70 quadros dessa animação, guardando um a cada dois.

### Linha 48

```python
imgs = [Image.frombytes("RGB", (1280, 720), q).resize((640, 360), Image.NEAREST) for q in quadros]
```

Converte cada quadro numa imagem do Pillow e reduz pela metade sem suavizar (`NEAREST`, mantém o pixel art).

### Linha 49

```python
saida = Path(__file__).resolve().parent.parent / "docs" / "img" / "demo.gif"
```

Caminho de saída.

### Linha 50

```python
imgs[0].save(saida, save_all=True, append_images=imgs[1:], duration=133, loop=0, optimize=True)
```

Salva como GIF animado: todas as imagens, 133 ms por quadro, repetindo para sempre (`loop=0`) e otimizado.

### Linha 51

```python
print("salvo", saida, f"{saida.stat().st_size / 1024:.0f} KB", len(imgs), "quadros")
```

Mostra o tamanho do arquivo e quantos quadros ele tem.
