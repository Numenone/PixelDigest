# `requirements-dev.txt`

[Voltar ao índice](README.md) · [Ver o arquivo](../../requirements-dev.txt)

Bibliotecas usadas só no desenvolvimento (não precisam estar instaladas para usar o programa).

### Linha 1

```text
pytest>=8.0
```

`pytest`: roda os testes automáticos da pasta `tests/`.

### Linha 2

```text
Pillow>=10.0
```

`Pillow`: biblioteca de imagens, usada só pelo `tools/gerar_gif.py` para montar o GIF do README.
