# Como conseguir cada chave

Tudo é preenchido dentro do programa, em **Configurações > Chaves de API**: a aba já mostra um resumo destas instruções e tem botões para abrir cada site. Este guia é a versão completa.

Em contas de empresa, criar apps ou dar permissões pode exigir aprovação do TI. Peça antes.

## Slack

1. Acesse https://api.slack.com/apps e clique em **Create New App > From scratch**. Escolha o workspace.
2. Em **OAuth & Permissions > Bot Token Scopes**, adicione:
   `channels:history`, `channels:read`, `groups:history`, `groups:read`, `users:read`.
3. Clique em **Install to Workspace**. Alguns workspaces exigem aprovação de um administrador.
4. Copie o **Bot User OAuth Token** (`xoxb-...`) para o `.env`.
5. Em cada canal que quer acompanhar, digite `/invite @NomeDoApp`.
6. Os IDs dos canais (`C0123...`) vão em `canais:` no `config.yaml`. Para achar: clique no nome do canal, e o ID aparece no fim da janela.
7. O seu ID de usuário (`U0123...`) fica no seu perfil, em **⋮ > Copiar ID do membro**. Com ele, o programa reconhece quando te marcam.

Para ler também as suas DMs: use um **User Token** (`xoxp-...`) com os escopos `im:history` e `im:read` (além dos de cima), e coloque `incluir_dms: true`.

## ClickUp

1. No ClickUp, vá em **Configurações > Apps > API Token** e gere o token (`pk_...`).
2. O ID da equipe (Workspace) é o número que aparece na URL: `app.clickup.com/1234567/...`.

## Gmail e Google Agenda

1. Em https://console.cloud.google.com, crie um projeto.
2. Em **APIs e serviços > Biblioteca**, ative a **Gmail API** e a **Google Calendar API**.
3. Em **Tela de consentimento OAuth**, escolha "Interno" (conta Workspace) ou "Externo", e adicione o seu e-mail como usuário de teste.
4. Em **Credenciais > Criar credenciais > ID do cliente OAuth**, escolha **App para computador** e baixe o JSON.
5. Salve o arquivo em `tokens/google-client-secret.json` e aponte `GOOGLE_CLIENT_SECRET_FILE` para ele.
6. Rode `python -m pixeldigest login`. O navegador abre para você autorizar.

Os escopos são só de leitura: `gmail.readonly` e `calendar.readonly`.

## Microsoft 365 (Outlook + Teams + agendador)

1. Em https://portal.azure.com, abra **Microsoft Entra ID > Registros de aplicativo > Novo registro**.
   * Nome: PixelDigest
   * Tipos de conta: "Somente contas deste diretório organizacional"
2. Copie o **ID do aplicativo (cliente)** e o **ID do diretório (locatário)** para o `.env`.
3. Em **Autenticação**, ligue **Permitir fluxos de clientes públicos** (necessário para o login por código).
4. Em **Permissões de API > Adicionar > Microsoft Graph > Permissões delegadas**, adicione:

   | Permissão | Para quê |
   |---|---|
   | `User.Read` | saber quem é você |
   | `Mail.Read` | e-mails não lidos |
   | `Calendars.ReadWrite` | ler a agenda, achar horário livre e criar a reunião |
   | `Chat.Read` | ler os chats do Teams |
   | `ChatMessage.Send` | responder no chat com os horários (opcional) |
   | `People.Read` | achar a pessoa pelo nome ("reunião com Ana") |
   | `User.ReadBasic.All` | descobrir o e-mail de quem te chamou no chat |

5. Rode `python -m pixeldigest login`. Ele mostra um código: abra https://microsoft.com/devicelogin, digite o código e entre com a conta da empresa.

Se a empresa bloquear o consentimento de usuários, um administrador precisa clicar em **Conceder consentimento do administrador**.

No `config.yaml`, desligue o que não quiser: `email`, `agenda`, `teams` e `agendador` (true/false). O agendador usa a primeira empresa com `agendador: true`. Com `responder_no_teams: true`, ele responde no chat com os horários. Deixe `false` até testar.

## Discord

No servidor: **Configurações do canal > Integrações > Webhooks > Novo webhook > Copiar URL**. Cole em `DISCORD_WEBHOOK_URL`.

## Adicionando outra empresa

Copie um bloco em `empresas:` e troque o nome, a cor e os nomes das variáveis:

```yaml
  - nome: Minha Empresa
    cor: "#ff9f43"
    conectores:
      - tipo: microsoft            # ou slack / clickup / gmail
        client_id_env: MINHA_MS_CLIENT_ID
        tenant_env: MINHA_MS_TENANT
        agendador: false
```

Para criar um conector novo (ex.: Jira): faça uma classe filha de `Conector` em `pixeldigest/connectors/`, implemente `coletar()` devolvendo uma lista de `Item` e registre o tipo em `connectors/__init__.py`.
