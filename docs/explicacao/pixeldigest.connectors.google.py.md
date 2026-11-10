# `pixeldigest/connectors/google.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/connectors/google.py)

Conector do Gmail e do Google Agenda, com OAuth 2.0. Cada conta é um conector separado, então dá para ter várias contas.

### Linhas 1 a 12

```python
"""Gmail + Google Agenda (OAuth 2.0). Dá para ter várias contas (uma por conector).

Login: botão "Fazer login" nas Configurações. Abre o navegador, você autoriza, e o
token fica em tokens/google-<conta>.json (fora do GitHub). Depois o token é
renovado sozinho com o refresh token (POST simples no Google, sem bibliotecas pesadas).

Para não ficar baixando tudo de novo:
- tem_novidade() faz UMA chamada barata (o "historyId" da caixa). Só se mudou é que
  os e-mails são lidos de novo; a agenda é relida no máximo a cada 30 minutos.

Escopos só de leitura: gmail.readonly e calendar.readonly.
"""
```

Docstring: o login abre o navegador e o token fica em `tokens/` (fora do GitHub); depois o token é renovado sozinho. Para economizar, `tem_novidade()` faz uma chamada barata e a agenda é relida no máximo a cada 30 minutos. Os escopos são só de leitura.

### Linha 13

```python
import base64
```

Importa `base64`: o Gmail manda o corpo dos e-mails codificado em Base64.

### Linha 14

```python
import html
```

Importa `html` para converter entidades como `&amp;` de volta em caracteres.

### Linha 15

```python
import json
```

Importa `json` (arquivo do token).

### Linha 16

```python
import re
```

Importa `re` (limpeza do texto).

### Linha 17

```python
import time
```

Importa `time` (validade do token e da agenda).

### Linha 18

```python
from datetime import datetime
```

Importa `datetime`.

### Linhas 20 a 23

```python
from .. import net
from ..config import ROOT, TOKENS
from ..models import ALTA, NORMAL, Item
from .base import Conector
```

Importa `net`, as pastas do projeto, as prioridades, `Item` e a base.

### Linhas 25 a 26

```python
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly",
          "https://www.googleapis.com/auth/calendar.readonly"]
```

Escopos pedidos no login: ler e-mails e ler a agenda, nada além disso.

### Linha 27

```python
GMAIL = "https://gmail.googleapis.com/gmail/v1/users/me/"
```

Endereço base da API do Gmail para o próprio usuário (`me`).

### Linha 28

```python
AGENDA = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
```

Endereço dos eventos da agenda principal.

### Linha 29

```python
BUSCA_PADRAO = "newer_than:1d in:inbox -category:promotions -category:social"
```

Busca padrão no Gmail: e-mails do último dia, na caixa de entrada, sem as abas Promoções e Social. É a mesma sintaxe da busca do site.

### Linha 30

```python
AGENDA_A_CADA = 30 * 60       # segundos entre leituras da agenda
```

A agenda é relida no máximo a cada 30 minutos.

### Linha 33

```python
def texto_do_email(payload, limite=1500):
```

Extrai o texto de um e-mail.

### Linha 34

```python
    """Tira o texto de um e-mail do Gmail (partes em base64), sem citações de respostas antigas."""
```

Docstring.

### Linhas 35 a 38

```python
    def partes(p):
        yield p
        for filho in p.get("parts", []) or []:
            yield from partes(filho)
```

Função geradora interna: devolve (`yield`) a parte atual e depois, recursivamente, todas as partes filhas. Um e-mail pode ter partes dentro de partes (texto, HTML, anexos). `yield from` repassa tudo o que a chamada recursiva gerar.

### Linha 40

```python
    simples, rico = "", ""
```

Guarda a versão em texto simples e a versão em HTML.

### Linha 41

```python
    for p in partes(payload):
```

Percorre todas as partes.

### Linhas 42 a 44

```python
        dados = (p.get("body") or {}).get("data")
        if not dados:
            continue
```

Pega o conteúdo codificado; se a parte não tem conteúdo (ex.: só agrupa outras), pula.

### Linha 45

```python
        conteudo = base64.urlsafe_b64decode(dados + "=" * (-len(dados) % 4)).decode("utf-8", "replace")
```

Decodifica o Base64 "url-safe". O Gmail tira o preenchimento "=" do fim; `"=" * (-len % 4)` repõe o que falta para o tamanho ser múltiplo de 4. `decode("utf-8", "replace")` troca bytes inválidos por um símbolo em vez de dar erro.

### Linhas 46 a 47

```python
        if p.get("mimeType") == "text/plain" and not simples:
            simples = conteudo
```

Guarda a primeira parte em texto simples.

### Linhas 48 a 50

```python
        elif p.get("mimeType") == "text/html" and not rico:
            rico = re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", conteudo, flags=re.S | re.I)
            rico = html.unescape(re.sub(r"<[^>]+>", " ", rico))
```

Para a primeira parte HTML: remove blocos `<style>` e `<script>` inteiros (`re.S` faz o `.` pegar quebras de linha; `\1` exige que a tag de fechamento seja a mesma da abertura), depois troca todas as outras tags por espaço e converte as entidades HTML.

### Linha 51

```python
    texto = simples or rico
```

Prefere o texto simples; se não houver, usa o HTML limpo.

### Linhas 52 a 53

```python
    # corta a parte citada ("Em ... escreveu:" / "On ... wrote:") e linhas começando com ">"
    texto = re.split(r"\n(?:Em .{5,80} escreveu:|On .{5,80} wrote:)", texto)[0]
```

Corta a parte citada de respostas antigas ("Em ... escreveu:" ou "On ... wrote:"), ficando só com o que vem antes.

### Linha 54

```python
    linhas = [l.strip() for l in texto.splitlines() if l.strip() and not l.strip().startswith(">")]
```

Tira linhas vazias e linhas que começam com ">" (citação).

### Linha 55

```python
    return " ".join(" ".join(linhas).split())[:limite]
```

Junta tudo numa linha com espaços simples e corta no limite de caracteres.

### Linhas 58 a 59

```python
class GmailConector(Conector):
    tipo = "gmail"
```

Classe do conector, tipo "gmail".

### Linhas 61 a 62

```python
    def __init__(self, empresa, opcoes, cfg):
        super().__init__(empresa, opcoes, cfg)
```

Construtor; chama o da base.

### Linha 63

```python
        self.conta = opcoes.get("conta", "padrao")
```

Nome da conta (usado no nome do arquivo de token).

### Linha 64

```python
        self.arquivo_token = TOKENS / f"google-{self.conta}.json"
```

Arquivo do token desta conta, como `tokens/google-minha_empresa.json`.

### Linha 65

```python
        self.segredo = str(ROOT / self.opcao("credenciais"))   # arquivo baixado do Google Cloud
```

Caminho do arquivo de credenciais do app, baixado do Google Cloud.

### Linha 66

```python
        self.busca = opcoes.get("busca", BUSCA_PADRAO)
```

Busca do Gmail (a padrão ou uma personalizada).

### Linha 67

```python
        self.com_agenda = opcoes.get("agenda", True)
```

Se também lê a agenda.

### Linha 68

```python
        self.email = opcoes.get("email", "")
```

E-mail da conta (descoberto no login).

### Linha 69

```python
        self.mensagens = []            # os 10 e-mails mais recentes (para o resumo com IA)
```

Os 10 e-mails mais recentes, usados na lista e no resumo com IA.

### Linha 70

```python
        self._historico = None         # historyId da última leitura
```

`historyId` da última leitura. O Gmail muda esse número sempre que algo muda na caixa.

### Linha 71

```python
        self._eventos, self._agenda_em = [], 0
```

Eventos da agenda e quando foram lidos.

### Linha 72

```python
        self._acesso, self._expira = None, 0
```

Token de acesso e quando expira.

### Linhas 74 a 76

```python
    @property
    def nome(self):
        return f"{self.empresa} / gmail{(' ' + self.email) if self.email else ''}"
```

Nome que aparece nos erros, com o e-mail quando conhecido.

### Linha 78

```python
    # ---------- OAuth ----------
```

Comentário da parte de OAuth.

### Linhas 79 a 80

```python
    def precisa_login(self):
        return not self.arquivo_token.exists()
```

Precisa de login se o arquivo do token ainda não existe.

### Linha 82

```python
    def login(self):
```

Faz o login.

### Linha 83

```python
        """Abre o navegador para autorizar. Devolve o e-mail da conta conectada."""
```

Docstring.

### Linha 84

```python
        from google_auth_oauthlib.flow import InstalledAppFlow
```

Importa a biblioteca oficial do Google para o fluxo de login de aplicativos instalados.

### Linha 85

```python
        flow = InstalledAppFlow.from_client_secrets_file(self.segredo, SCOPES)
```

Cria o fluxo a partir do arquivo de credenciais e dos escopos.

### Linha 86

```python
        creds = flow.run_local_server(port=0, prompt="consent select_account")
```

Abre o navegador e sobe um servidor local temporário (numa porta livre, `port=0`) que recebe a resposta do Google. `prompt="consent select_account"` força mostrar a escolha da conta e a tela de permissão, garantindo um refresh token novo.

### Linha 87

```python
        self.arquivo_token.write_text(creds.to_json(), encoding="utf-8")
```

Salva o token (com o refresh token) no arquivo.

### Linha 88

```python
        self._acesso, self._expira = None, 0
```

Zera o token em memória para forçar a leitura do arquivo novo.

### Linhas 89 a 90

```python
        self.email = self._get(GMAIL + "profile").get("emailAddress", "")
        return self.email
```

Descobre o e-mail da conta conectada e devolve.

### Linha 92

```python
    def _token(self):
```

Devolve um token de acesso válido.

### Linha 93

```python
        """Token de acesso válido; renova com o refresh token quando vence (a cada ~1 h)."""
```

Docstring: o token de acesso vale cerca de 1 hora.

### Linhas 94 a 95

```python
        if self._acesso and time.time() < self._expira - 60:
            return self._acesso
```

Se o token atual ainda vale por mais de 1 minuto, reaproveita.

### Linhas 96 a 97

```python
        if self.precisa_login():
            raise net.ApiError("Google", "falta fazer o login (Configurações > Chaves de API > Fazer login)")
```

Sem arquivo de token, pede para fazer o login.

### Linha 98

```python
        salvo = json.loads(self.arquivo_token.read_text(encoding="utf-8"))
```

Lê o arquivo salvo.

### Linhas 99 a 102

```python
        try:
            r = net.request("Google", "POST", salvo.get("token_uri", "https://oauth2.googleapis.com/token"), data={
                "client_id": salvo["client_id"], "client_secret": salvo["client_secret"],
                "refresh_token": salvo["refresh_token"], "grant_type": "refresh_token"}, client=self.client)
```

Renova o token com um POST simples no endereço de token do Google, mandando client id, client secret, refresh token e `grant_type=refresh_token`. É o fluxo padrão do OAuth 2.0, feito sem bibliotecas pesadas.

### Linhas 103 a 104

```python
        except net.ApiError as exc:
            raise net.ApiError("Google", f"o login venceu ou foi revogado; faça o login de novo ({exc})") from exc
```

Se falhar, o login venceu ou foi revogado: pede para fazer de novo.

### Linhas 105 a 106

```python
        dados = r.json()
        self._acesso, self._expira = dados["access_token"], time.time() + int(dados.get("expires_in", 3600))
```

Guarda o token novo e a expiração.

### Linhas 107 a 108

```python
        salvo["token"] = self._acesso
        self.arquivo_token.write_text(json.dumps(salvo), encoding="utf-8")
```

Atualiza o arquivo com o token novo.

### Linha 109

```python
        return self._acesso
```

Devolve.

### Linhas 111 a 113

```python
    def _get(self, url, **params):
        return net.get_json("Google", url, client=self.client, params=params,
                            headers={"Authorization": f"Bearer {self._token()}"})
```

Atalho de GET autenticado na API do Google.

### Linha 115

```python
    # ---------- novidades (barato) ----------
```

Comentário: conferência barata de novidades.

### Linha 116

```python
    def tem_novidade(self):
```

Diz se há algo novo para buscar.

### Linha 117

```python
        """True se chegou e-mail novo (1 chamada) ou se a agenda já está velha (30 min)."""
```

Docstring.

### Linha 118

```python
        perfil = self._get(GMAIL + "profile")
```

Uma chamada só, ao perfil da caixa.

### Linha 119

```python
        self.email = perfil.get("emailAddress", self.email)
```

Atualiza o e-mail.

### Linha 120

```python
        mudou = perfil.get("historyId") != self._historico
```

Mudou se o `historyId` é diferente do da última leitura.

### Linha 121

```python
        agenda_velha = self.com_agenda and time.time() - self._agenda_em > AGENDA_A_CADA
```

A agenda está velha se passou mais de 30 minutos desde a última leitura.

### Linha 122

```python
        return mudou or agenda_velha
```

Há novidade se qualquer uma das duas coisas for verdade.

### Linha 124

```python
    # ---------- coleta ----------
```

Comentário da coleta.

### Linha 125

```python
    def ler_emails(self):
```

Lê os 10 e-mails mais recentes.

### Linha 126

```python
        """Os 10 e-mails mais recentes das últimas 24 h, com o texto (usado na lista e no resumo)."""
```

Docstring.

### Linhas 127 a 128

```python
        perfil = self._get(GMAIL + "profile")
        self.email = perfil.get("emailAddress", self.email)
```

Lê o perfil e atualiza o e-mail.

### Linhas 129 a 130

```python
        if perfil.get("historyId") == self._historico and self.mensagens:
            return self.mensagens                      # nada novo: reaproveita
```

Se nada mudou e já temos mensagens, reaproveita.

### Linha 131

```python
        lista = self._get(GMAIL + "messages", q=self.busca, maxResults=10).get("messages", [])
```

Lista os ids dos 10 e-mails mais recentes que batem com a busca.

### Linha 132

```python
        anteriores = {m["id"]: m for m in self.mensagens}
```

Dicionário id para mensagem das que já temos.

### Linha 133

```python
        mensagens = []
```

Lista nova.

### Linhas 134 a 137

```python
        for ref in lista:
            if ref["id"] in anteriores:                # já lido antes: não baixa de novo
                mensagens.append(anteriores[ref["id"]])
                continue
```

Se a mensagem já foi baixada antes, reaproveita sem nova chamada.

### Linha 138

```python
            m = self._get(GMAIL + f"messages/{ref['id']}", format="full")
```

Senão, baixa a mensagem completa (`format=full`).

### Linha 139

```python
            cab = {h["name"].lower(): h["value"] for h in m.get("payload", {}).get("headers", [])}
```

Monta um dicionário dos cabeçalhos com o nome em minúsculas (From, Subject...).

### Linhas 140 a 148

```python
            mensagens.append({
                "id": ref["id"],
                "de": cab.get("from", "?").split("<")[0].strip().strip('"'),
                "assunto": cab.get("subject", "(sem assunto)"),
                "quando": int(m["internalDate"]) / 1000,
                "texto": texto_do_email(m.get("payload", {})) or m.get("snippet", ""),
                "nao_lido": "UNREAD" in m.get("labelIds", []),
                "importante": "IMPORTANT" in m.get("labelIds", []),
            })
```

Guarda um dicionário simples com: id; remetente (só o nome, sem o e-mail entre "<>" e sem aspas); assunto; data (o Gmail manda em milissegundos); texto extraído (ou o trecho curto que o Gmail fornece); se não foi lido; e se o Gmail marcou como importante (os dois vêm nas etiquetas, `labelIds`).

### Linha 149

```python
        self.mensagens, self._historico = mensagens, perfil.get("historyId")
```

Guarda as mensagens e o `historyId` atual.

### Linha 150

```python
        return mensagens
```

Devolve.

### Linha 152

```python
    def emails(self):
```

Converte os e-mails em `Item`.

### Linha 153

```python
        link = f"https://mail.google.com/mail/?authuser={self.email}#inbox/" if self.email else "https://mail.google.com/mail/#inbox/"
```

Link para abrir cada e-mail no Gmail certo (o `authuser` escolhe a conta quando há várias logadas no navegador).

### Linhas 154 a 159

```python
        return [Item(
            empresa=self.empresa, fonte="gmail", tipo="email",
            titulo=f"{m['de']}: {m['assunto']}", detalhe=m["texto"][:120],
            quando=datetime.fromtimestamp(m["quando"], self.fuso), url=link + m["id"],
            prioridade=ALTA if m["importante"] else NORMAL, id=m["id"],
        ) for m in self.ler_emails()]
```

Um `Item` por e-mail: título "remetente: assunto", começo do texto, data, link, prioridade alta se importante.

### Linha 161

```python
    def eventos(self):
```

Lê os eventos da agenda.

### Linhas 162 a 163

```python
        if time.time() - self._agenda_em < AGENDA_A_CADA and self._agenda_em:
            return self._eventos                      # agenda lida há pouco: reaproveita
```

Se leu há menos de 30 minutos, reaproveita.

### Linhas 164 a 166

```python
        dados = self._get(AGENDA, timeMin=self.inicio_do_dia().isoformat(),
                          timeMax=self.fim_de_amanha().isoformat(),
                          singleEvents="true", orderBy="startTime", maxResults=20)
```

Busca os eventos de hoje e amanhã. `singleEvents=true` expande eventos repetidos em ocorrências separadas e `orderBy=startTime` ordena por horário.

### Linha 167

```python
        itens = []
```

Lista de itens.

### Linha 168

```python
        for ev in dados.get("items", []):
```

Para cada evento.

### Linha 169

```python
            inicio = ev.get("start", {})
```

Dados do início.

### Linhas 170 a 171

```python
            if "dateTime" in inicio:
                quando = datetime.fromisoformat(inicio["dateTime"]).astimezone(self.fuso)
```

Evento com hora: converte para o fuso do usuário.

### Linhas 172 a 173

```python
            else:  # evento de dia inteiro
                quando = datetime.fromisoformat(inicio["date"]).replace(tzinfo=self.fuso)
```

Evento de dia inteiro (só tem data): usa a meia-noite no fuso do usuário.

### Linhas 174 a 179

```python
            itens.append(Item(
                empresa=self.empresa, fonte="google_agenda", tipo="evento",
                titulo=ev.get("summary", "(sem título)"),
                detalhe="Google Meet" if ev.get("hangoutLink") else ("Zoom" if "zoom.us" in json.dumps(ev) else ""),
                quando=quando, url=ev.get("htmlLink", ""), prioridade=ALTA, id=ev["id"],
            ))
```

Cria o `Item` do tipo evento. O detalhe diz se é Google Meet (tem `hangoutLink`) ou Zoom (o texto do evento contém "zoom.us").

### Linha 180

```python
        self._eventos, self._agenda_em = itens, time.time()
```

Guarda os eventos e a hora da leitura.

### Linha 181

```python
        return itens
```

Devolve.

### Linhas 183 a 187

```python
    def coletar(self):
        itens = self.emails()
        if self.com_agenda:
            itens += self.eventos()
        return itens
```

Coleta: e-mails mais, se ligada, a agenda.
