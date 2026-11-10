"""Gera docs/img/demo.gif: o clima mudando de sol para tempestade e uma reunião agendada.

Rodar: python tools/gerar_gif.py   (precisa do Pillow: pip install -r requirements-dev.txt)
"""
import os
import sys
from datetime import datetime
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402
from PIL import Image  # noqa: E402

from pixeldigest import config  # noqa: E402
from pixeldigest.core import Motor  # noqa: E402
from pixeldigest.meetings import rotulo  # noqa: E402
from pixeldigest.ui import effects  # noqa: E402
from pixeldigest.ui.app import App  # noqa: E402

pygame.init()
tela = pygame.display.set_mode((1280, 720))
cfg = config.carregar(demo=True)
motor = Motor(cfg)
motor.atualizar_resumo(avisar_urgentes=False)
app = App(cfg, motor, tela)
app.receber()
alvo = datetime.now().astimezone().replace(hour=14, minute=20)
app.desloc_horas = (alvo - datetime.now().astimezone()).total_seconds() / 3600

quadros = []
roteiro = [("sol", 30), ("nublado", 40), ("chuva", 45), ("tempestade", 60)]
for preset, n in roteiro:
    app.preset = preset
    app.cena.definir_clima(preset=preset)
    for i in range(n):
        app.quadro(1 / 15)
        if i % 2 == 0:
            quadros.append(pygame.image.tobytes(tela, "RGB"))
h = motor.agendador.conector.horarios_livres("", 30, [])[0]
app.efeitos.append(effects.Agendado("Ana", rotulo(h), "Reunião"))
for i in range(70):
    app.quadro(1 / 15)
    if i % 2 == 0:
        quadros.append(pygame.image.tobytes(tela, "RGB"))

imgs = [Image.frombytes("RGB", (1280, 720), q).resize((640, 360), Image.NEAREST) for q in quadros]
saida = Path(__file__).resolve().parent.parent / "docs" / "img" / "demo.gif"
imgs[0].save(saida, save_all=True, append_images=imgs[1:], duration=133, loop=0, optimize=True)
print("salvo", saida, f"{saida.stat().st_size / 1024:.0f} KB", len(imgs), "quadros")
