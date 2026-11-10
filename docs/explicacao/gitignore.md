# `.gitignore`

[Voltar ao índice](README.md) · [Ver o arquivo](../../.gitignore)

Diz ao Git quais arquivos nunca devem ir para o repositório. É a principal proteção para que chaves e dados pessoais não fiquem públicos no GitHub.

### Linha 1

```
# segredos e dados pessoais: nunca no GitHub
```

Comentário explicando a seção.

### Linha 2

```
.env
```

`.env`: as chaves de API e tokens.

### Linha 3

```
config.yaml
```

`config.yaml`: a configuração real (empresas, canais, local do clima).

### Linhas 4 a 5

```
tokens/*
!tokens/.gitkeep
```

`tokens/*` ignora tudo dentro de `tokens/` (logins OAuth do Google e da Microsoft e o arquivo de credenciais), mas a linha com `!` abre uma exceção para o `.gitkeep`, um arquivo vazio que só serve para a pasta existir no repositório.

### Linhas 6 a 7

```
data/*
!data/.gitkeep
```

Mesma ideia para `data/` (resumos diários, caches, log e fila de notificações).

### Linha 9

```
# python
```

Comentário da seção do Python.

### Linha 10

```
.venv/
```

`.venv/`: o ambiente virtual com as bibliotecas instaladas (cada pessoa cria o seu).

### Linhas 11 a 12

```
__pycache__/
*.pyc
```

Arquivos compilados que o Python gera sozinho (`__pycache__` e `.pyc`).

### Linha 13

```
.pytest_cache/
```

Cache do pytest.
