# `requirements.txt`

[Voltar ao índice](README.md) · [Ver o arquivo](../../requirements.txt)

Lista das bibliotecas externas que o projeto usa. O comando `pip install -r requirements.txt` instala todas. O `>=` define a versão mínima testada.

### Linha 1

```text
pygame-ce>=2.5
```

`pygame-ce`: a edição da comunidade do pygame, usada para a janela, o desenho do pixel art, as fontes e o teclado e mouse.

### Linha 2

```text
httpx>=0.27
```

`httpx`: cliente HTTP de todas as chamadas às APIs, com timeout, conexões reaproveitadas e transporte falso para os testes.

### Linha 3

```text
PyYAML>=6.0
```

`PyYAML`: lê e grava o `config.yaml`.

### Linha 4

```text
python-dotenv>=1.0
```

`python-dotenv`: lê e grava o `.env` com as chaves.

### Linha 5

```text
msal>=1.31
```

`msal`: biblioteca oficial da Microsoft para o login OAuth (device code) do Outlook e do Teams.

### Linha 6

```text
google-auth>=2.30
```

`google-auth`: base da autenticação do Google.

### Linha 7

```text
google-auth-oauthlib>=1.2
```

`google-auth-oauthlib`: o fluxo de login que abre o navegador para autorizar o Gmail e a Agenda.

### Linha 8

```text
tzdata>=2024.1
```

`tzdata`: banco de dados de fusos horários. No Windows, o `zoneinfo` do Python precisa dele para entender "America/Sao_Paulo".

### Linha 9

```text
qrcode>=7.4
```

`qrcode`: gera o QR code das Configurações (assinar o tópico no celular).

### Linha 10

```text
anthropic>=2.6
```

`anthropic`: SDK oficial da API do Claude, usado no resumo dos e-mails com IA.
