# `.env.example`

[Voltar ao índice](README.md) · [Ver o arquivo](../../.env.example)

Exemplo do `.env`, com todas as variáveis de ambiente que o projeto usa. O `.env` real é gravado pela tela de Configurações e nunca vai para o GitHub.

### Linhas 1 a 3

```bash
# Exemplo do .env. Você NÃO precisa editar este arquivo:
# preencha as chaves em Configurações > Chaves de API dentro do programa.
# O .env real nunca vai para o GitHub (.gitignore).
```

Comentários: não é preciso editar, a tela grava sozinha, e o arquivo real está no `.gitignore`.

### Linha 5

```bash
# Notificações
```

Comentário da seção.

### Linha 6

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/seu_webhook_aqui
```

URL do webhook do Discord (o canal onde as notificações aparecem).

### Linha 7

```bash
NTFY_TOPIC=pixeldigest-seu_topico_aqui
```

Tópico do ntfy das notificações no celular. Funciona como senha: quem sabe o nome lê as mensagens.

### Linha 8

```bash
NTFY_TOPIC_ALARME=pixeldigest-alarme-seu_topico_aqui
```

Tópico do ntfy do alarme do celular (o MacroDroid publica aqui e o PC escuta).

### Linha 9

```bash
NTFY_SERVER=https://ntfy.sh
```

Servidor do ntfy (o público, por padrão).

### Linha 10

```bash
NTFY_TOKEN=
```

Token do ntfy, só para servidores com senha. Vazio no ntfy.sh.

### Linha 12

```bash
# Resumo dos e-mails com IA (Claude)
```

Comentário da seção.

### Linha 13

```bash
ANTHROPIC_API_KEY=sk-ant-sua_chave_aqui
```

Chave da API do Claude, para o resumo dos e-mails. Sem ela, o resumo é feito sem IA.

### Linha 15

```bash
# Tokens dos serviços (o nome é criado pela tela: PD_<EMPRESA>_<SERVIÇO>_<CAMPO>)
```

Comentário: o nome das variáveis dos serviços é montado pela tela a partir da empresa e do serviço.

### Linha 16

```bash
PD_MINHA_EMPRESA_SLACK_TOKEN=xoxp-seu_token_aqui
```

Token de usuário do Slack.

### Linha 17

```bash
PD_MINHA_EMPRESA_CLICKUP_TOKEN=pk_seu_token_aqui
```

Token pessoal do ClickUp.

### Linha 18

```bash
PD_MINHA_EMPRESA_ZOOM_SECRET=seu_client_secret_aqui
```

Client Secret do app Server-to-Server do Zoom.
