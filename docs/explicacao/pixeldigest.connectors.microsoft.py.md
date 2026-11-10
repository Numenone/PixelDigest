# `pixeldigest/connectors/microsoft.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/connectors/microsoft.py)

Conector do Microsoft 365 pelo Microsoft Graph: e-mail e agenda do Outlook e chats do Teams. Também é a base do agendador: procura horário livre para duas pessoas e cria a reunião com link do Teams.

### Linhas 1 a 13

```python
"""Microsoft 365 pelo Microsoft Graph: Outlook (e-mail e agenda) + Teams (chats).

Também é a base do agendador de reuniões: procura horário livre para duas pessoas
(findMeetingTimes) e cria a reunião com link do Teams.

Autenticação: OAuth 2.0 com "device code" (biblioteca MSAL). No primeiro login o
programa mostra um código; você abre microsoft.com/devicelogin, digita o código e
autoriza. O token fica em tokens/ms-<empresa>.json e é renovado sozinho.

Permissões delegadas (o app só faz o que VOCÊ poderia fazer):
User.Read, Mail.Read, Calendars.ReadWrite, Chat.Read, ChatMessage.Send,
People.Read, User.ReadBasic.All
"""
```

Docstring: autenticação OAuth 2.0 com "device code" pela biblioteca MSAL (o programa mostra um código, você digita em microsoft.com/devicelogin e autoriza). O token fica em `tokens/` e é renovado sozinho. Lista as permissões delegadas: o app só faz o que você mesmo poderia fazer.

### Linha 14

```python
import html
```

Importa `html` (decodificar entidades das mensagens do Teams).

### Linha 15

```python
import re
```

Importa `re`.

### Linha 16

```python
from datetime import datetime, timedelta
```

Importa `datetime` e `timedelta`.

### Linhas 18 a 21

```python
from .. import net
from ..config import TOKENS
from ..models import ALTA, NORMAL, URGENTE, Horario, Item
from .base import Conector
```

Importa `net`, a pasta de tokens, as prioridades, `Horario`, `Item` e a base.

### Linha 23

```python
GRAPH = "https://graph.microsoft.com/v1.0"
```

Endereço base do Microsoft Graph, versão 1.0.

### Linhas 26 a 27

```python
def slug(texto):
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")
```

Transforma um texto em "slug" para nome de arquivo: minúsculas e tudo o que não for letra ou número vira hífen (ex.: "Outra Empresa" vira "outra-empresa").

### Linhas 30 a 33

```python
def texto_puro(conteudo_html):
    """Mensagens do Teams vêm em HTML: tira as tags e decodifica &amp; etc."""
    sem_tags = re.sub(r"<[^>]+>", " ", conteudo_html or "")
    return " ".join(html.unescape(sem_tags).split())
```

Tira as tags HTML das mensagens do Teams e decodifica entidades como `&amp;`, juntando os espaços.

### Linhas 36 a 37

```python
class MicrosoftConector(Conector):
    tipo = "microsoft"
```

Classe do conector, tipo "microsoft".

### Linhas 39 a 40

```python
    def __init__(self, empresa, opcoes, cfg):
        super().__init__(empresa, opcoes, cfg)
```

Construtor; chama o da base.

### Linha 41

```python
        self.client_id = self.opcao("client_id")
```

Client ID do app registrado no Azure (obrigatório).

### Linha 42

```python
        self.tenant = self.opcao("tenant", obrigatorio=False) or "organizations"
```

Tenant (organização). "organizations" aceita qualquer conta corporativa.

### Linha 43

```python
        self.arquivo_token = TOKENS / f"ms-{slug(empresa)}.json"
```

Arquivo do token desta empresa.

### Linha 44

```python
        self.fuso_windows = cfg["usuario"]["fuso_windows"]
```

Fuso no padrão Windows, usado nas chamadas ao Outlook.

### Linha 45

```python
        self.usar = {k: opcoes.get(k, True) for k in ("email", "agenda", "teams", "agendador")}
```

Quais partes usar (e-mail, agenda, Teams, agendador), todas ligadas por padrão.

### Linhas 46 a 48

```python
        self._app = None
        self._cache = None
        self._eu = None
```

Objeto da MSAL, cache de tokens e dados do usuário, criados quando forem precisos.

### Linha 50

```python
    # ---------- OAuth (MSAL) ----------
```

Comentário da parte de OAuth.

### Linha 51

```python
    def escopos(self):
```

Monta a lista de permissões conforme as partes ligadas (pedir só o necessário é uma boa prática de segurança).

### Linha 52

```python
        s = ["User.Read"]
```

Sempre pede `User.Read` (ler o próprio perfil).

### Linhas 53 a 54

```python
        if self.usar["email"]:
            s.append("Mail.Read")
```

E-mail ligado: `Mail.Read`.

### Linhas 55 a 56

```python
        if self.usar["agenda"] or self.usar["agendador"]:
            s.append("Calendars.ReadWrite")
```

Agenda ou agendador: `Calendars.ReadWrite` (ler a agenda e criar reuniões).

### Linhas 57 a 58

```python
        if self.usar["teams"] or self.usar["agendador"]:
            s += ["Chat.Read", "ChatMessage.Send"]
```

Teams ou agendador: ler chats e mandar mensagens.

### Linhas 59 a 60

```python
        if self.usar["agendador"]:
            s += ["People.Read", "User.ReadBasic.All"]
```

Agendador: buscar pessoas e ler o perfil básico de colegas (para achar o e-mail).

### Linha 61

```python
        return s
```

Devolve.

### Linha 63

```python
    def _msal(self):
```

Cria (uma vez) o objeto da MSAL.

### Linha 64

```python
        import msal
```

Importa a biblioteca `msal` só quando necessário.

### Linhas 65 a 66

```python
        if self._app is None:
            self._cache = msal.SerializableTokenCache()
```

Se ainda não existe, cria um cache de tokens que pode ser salvo em arquivo.

### Linhas 67 a 68

```python
            if self.arquivo_token.exists():
                self._cache.deserialize(self.arquivo_token.read_text(encoding="utf-8"))
```

Se o arquivo de token existe, carrega o cache dele.

### Linhas 69 a 71

```python
            self._app = msal.PublicClientApplication(
                self.client_id, authority=f"https://login.microsoftonline.com/{self.tenant}",
                token_cache=self._cache)
```

Cria o app público (sem segredo, próprio para programas instalados) com o client id, o endereço de login da organização e o cache.

### Linha 72

```python
        return self._app
```

Devolve.

### Linhas 74 a 76

```python
    def _salvar_cache(self):
        if self._cache is not None and self._cache.has_state_changed:
            self.arquivo_token.write_text(self._cache.serialize(), encoding="utf-8")
```

Salva o cache no arquivo só se ele mudou (`has_state_changed`).

### Linhas 78 a 79

```python
    def precisa_login(self):
        return not self._msal().get_accounts()
```

Precisa de login se a MSAL não conhece nenhuma conta.

### Linha 81

```python
    def login(self, mostrar_codigo=None):
```

Faz o login por código.

### Linhas 82 a 86

```python
        """Login por código: mostra um código que você digita em microsoft.com/devicelogin.

        mostrar_codigo(url, codigo): a tela de Configurações usa para exibir o código grande.
        Sem ela, o código é impresso no terminal.
        """
```

Docstring: a tela de Configurações passa uma função para mostrar o código grande; sem ela, o código sai no terminal.

### Linhas 87 a 88

```python
        app = self._msal()
        flow = app.initiate_device_flow(scopes=self.escopos())
```

Inicia o fluxo de device code com as permissões.

### Linhas 89 a 90

```python
        if "user_code" not in flow:
            raise net.ApiError("Microsoft", f"não deu para iniciar o login: {flow.get('error_description')}")
```

Se a resposta não trouxe o código, mostra o motivo.

### Linhas 91 a 94

```python
        if mostrar_codigo:
            mostrar_codigo(flow["verification_uri"], flow["user_code"])
        else:
            print(flow["message"])
```

Mostra o endereço e o código na tela, ou a mensagem pronta da MSAL no terminal.

### Linha 95

```python
        resultado = app.acquire_token_by_device_flow(flow)    # espera você autorizar no navegador
```

Espera você autorizar no navegador (esta chamada fica bloqueada até lá, por isso a tela roda em segundo plano).

### Linhas 96 a 97

```python
        if "access_token" not in resultado:
            raise net.ApiError("Microsoft", resultado.get("error_description", "login recusado"))
```

Se não veio token, mostra o motivo.

### Linha 98

```python
        self._salvar_cache()
```

Salva o cache com o token.

### Linha 100

```python
    def _token(self):
```

Devolve um token de acesso válido.

### Linhas 101 a 103

```python
        app = self._msal()
        contas = app.get_accounts()
        resultado = app.acquire_token_silent(self.escopos(), account=contas[0]) if contas else None
```

Pega a conta salva e pede o token "em silêncio": a MSAL devolve o token guardado ou renova sozinha com o refresh token, sem abrir nada.

### Linhas 104 a 105

```python
        if not resultado or "access_token" not in resultado:
            raise net.ApiError("Microsoft", "falta fazer o login (Configurações > Chaves de API > Fazer login)")
```

Se não conseguiu, pede para fazer o login.

### Linhas 106 a 107

```python
        self._salvar_cache()
        return resultado["access_token"]
```

Salva o cache (pode ter renovado) e devolve o token.

### Linhas 109 a 112

```python
    def _headers(self):
        return {"Authorization": f"Bearer {self._token()}",
                # Faz o Outlook devolver os horários já no nosso fuso
                "Prefer": f'outlook.timezone="{self.fuso_windows}"'}
```

Cabeçalhos de toda chamada: o token e o `Prefer` com o fuso, que faz o Outlook devolver os horários já no nosso fuso.

### Linhas 114 a 115

```python
    def _get(self, caminho, **params):
        return net.get_json("Microsoft", GRAPH + caminho, client=self.client, params=params, headers=self._headers())
```

Atalho de GET no Graph.

### Linhas 117 a 118

```python
    def _post(self, caminho, payload):
        return net.post_json("Microsoft", GRAPH + caminho, payload, client=self.client, headers=self._headers())
```

Atalho de POST no Graph.

### Linha 120

```python
    def hora_local(self, valor):
```

Converte datas do Graph para o nosso fuso.

### Linhas 121 a 125

```python
        """Converte datas do Graph para o nosso fuso.

        Eventos vêm sem fuso ("2026-11-06T14:00:00.0000000", já no fuso pedido no Prefer);
        mensagens vêm em UTC ("2026-11-06T17:01:02.123Z").
        """
```

Docstring: eventos vêm sem fuso (já no fuso pedido), mensagens vêm em UTC terminadas em "Z".

### Linhas 126 a 127

```python
        if valor.endswith("Z") or "+" in valor[10:]:
            return datetime.fromisoformat(valor.replace("Z", "+00:00")).astimezone(self.fuso)
```

Se tem fuso (termina em "Z" ou tem "+" depois da data), converte para o nosso.

### Linha 128

```python
        return datetime.fromisoformat(valor[:19]).replace(tzinfo=self.fuso)
```

Se não tem, corta os primeiros 19 caracteres ("2026-11-06T14:00:00", sem as frações de segundo que o Graph manda com 7 casas) e coloca o nosso fuso.

### Linhas 130 a 133

```python
    def eu(self):
        if self._eu is None:
            self._eu = self._get("/me", **{"$select": "id,displayName,mail,userPrincipalName"})
        return self._eu
```

Dados do usuário logado (`/me`), buscados uma vez. `$select` pede só os campos necessários (parâmetro OData).

### Linha 135

```python
    # ---------- coleta para o resumo ----------
```

Comentário da coleta.

### Linha 136

```python
    def eventos(self):
```

Eventos da agenda.

### Linhas 137 a 141

```python
        dados = self._get("/me/calendarView", **{
            "startDateTime": self.inicio_do_dia().isoformat(),
            "endDateTime": self.fim_de_amanha().isoformat(),
            "$select": "id,subject,start,isOnlineMeeting,webLink,isCancelled,organizer",
            "$orderby": "start/dateTime", "$top": 30})
```

`calendarView` devolve os eventos entre duas datas, com as repetições já expandidas. Pede só os campos usados, ordenados pelo início, até 30.

### Linhas 142 a 148

```python
        return [Item(
            empresa=self.empresa, fonte="outlook", tipo="evento",
            titulo=ev.get("subject") or "(sem título)",
            detalhe="Teams" if ev.get("isOnlineMeeting") else "",
            quando=self.hora_local(ev["start"]["dateTime"]),
            url=ev.get("webLink", ""), prioridade=ALTA, id=ev["id"],
        ) for ev in dados.get("value", []) if not ev.get("isCancelled")]
```

Um `Item` por evento não cancelado: título, "Teams" se for reunião online, horário convertido, link e prioridade alta.

### Linha 150

```python
    def emails(self):
```

E-mails.

### Linhas 151 a 153

```python
        dados = self._get("/me/mailFolders/inbox/messages", **{
            "$filter": "isRead eq false", "$top": 15,
            "$select": "id,subject,from,receivedDateTime,importance,webLink,bodyPreview"})
```

E-mails não lidos da caixa de entrada (`$filter` é o filtro OData), até 15, só com os campos necessários.

### Linha 154

```python
        itens = []
```

Lista.

### Linhas 155 a 156

```python
        for m in dados.get("value", []):
            remetente = (m.get("from") or {}).get("emailAddress", {}).get("name", "?")
```

Para cada e-mail, pega o nome do remetente com segurança (cada `get` com padrão evita erro se faltar um nível).

### Linhas 157 a 162

```python
            itens.append(Item(
                empresa=self.empresa, fonte="outlook", tipo="email",
                titulo=f"{remetente}: {m.get('subject') or '(sem assunto)'}",
                detalhe=(m.get("bodyPreview") or "")[:120],
                quando=self.hora_local(m["receivedDateTime"]), url=m.get("webLink", ""),
                prioridade=ALTA if m.get("importance") == "high" else NORMAL, id=m["id"]))
```

Cria o `Item`: título com remetente e assunto, prévia do corpo, data, link e prioridade alta se o e-mail foi marcado como importante.

### Linha 163

```python
        return itens
```

Devolve.

### Linhas 165 a 167

```python
    def chats(self):
        """Lista os chats com a prévia da última mensagem (uma chamada só)."""
        return self._get("/me/chats", **{"$expand": "lastMessagePreview", "$top": 50}).get("value", [])
```

Lista os chats com a prévia da última mensagem já incluída (`$expand`), numa chamada só.

### Linha 169

```python
    def mensagens_teams(self):
```

Mensagens do Teams não lidas.

### Linha 170

```python
        """Chats com mensagem de outra pessoa ainda não lida nas últimas 24 h."""
```

Docstring.

### Linha 171

```python
        meu_id = self.eu()["id"]
```

Seu id, para ignorar as próprias mensagens.

### Linha 172

```python
        limite = self.agora() - timedelta(hours=24)
```

Limite de 24 horas.

### Linha 173

```python
        itens = []
```

Lista.

### Linha 174

```python
        for chat in self.chats():
```

Para cada chat.

### Linhas 175 a 176

```python
            prev = chat.get("lastMessagePreview") or {}
            autor = ((prev.get("from") or {}).get("user") or {})
```

Prévia da última mensagem e seu autor.

### Linhas 177 a 178

```python
            if not prev or autor.get("id") in (None, meu_id):
                continue
```

Pula chats sem mensagem, mensagens de sistema (sem autor) e mensagens suas.

### Linha 179

```python
            criada = self.hora_local(prev["createdDateTime"])
```

Quando a última mensagem foi criada.

### Linha 180

```python
            lida = (chat.get("viewpoint") or {}).get("lastMessageReadDateTime")
```

Quando você leu esse chat pela última vez.

### Linhas 181 a 182

```python
            if criada < limite or (lida and self.hora_local(lida) >= criada):
                continue
```

Pula se a mensagem é mais velha que 24 horas ou se você já leu depois dela.

### Linhas 183 a 188

```python
            itens.append(Item(
                empresa=self.empresa, fonte="teams", tipo="mensagem",
                titulo=f"{autor.get('displayName', '?')}: {texto_puro(prev.get('body', {}).get('content'))[:90]}",
                detalhe=chat.get("topic") or "chat", quando=criada, url=chat.get("webUrl", ""),
                prioridade=URGENTE if chat.get("chatType") == "oneOnOne" else ALTA,
                id=f"{chat['id']}:{prev.get('id')}"))
```

Cria o `Item`: título com autor e texto limpo (90 caracteres), tópico do chat, data, link. Conversa um a um é urgente; grupo é alta.

### Linha 189

```python
        return itens
```

Devolve.

### Linhas 191 a 199

```python
    def coletar(self):
        itens = []
        if self.usar["agenda"]:
            itens += self.eventos()
        if self.usar["email"]:
            itens += self.emails()
        if self.usar["teams"]:
            itens += self.mensagens_teams()
        return itens
```

Coleta só as partes ligadas.

### Linha 201

```python
    # ---------- agendador de reuniões ----------
```

Comentário do agendador.

### Linha 202

```python
    def mensagens_novas(self, desde):
```

Mensagens novas no Teams, para procurar pedidos de reunião.

### Linha 203

```python
        """Mensagens de outras pessoas no Teams depois de 'desde' (para achar pedidos de reunião)."""
```

Docstring.

### Linhas 204 a 205

```python
        meu_id = self.eu()["id"]
        novas = []
```

Seu id e a lista.

### Linhas 206 a 209

```python
        for chat in self.chats():
            prev = chat.get("lastMessagePreview") or {}
            if not prev or self.hora_local(prev["createdDateTime"]) <= desde:
                continue
```

Para cada chat, pula se não houver mensagem nova depois de `desde` (economiza chamadas: só abre os chats que mudaram).

### Linha 210

```python
            dados = self._get(f"/me/chats/{chat['id']}/messages", **{"$top": 10})
```

Busca as 10 últimas mensagens do chat.

### Linhas 211 a 214

```python
            for m in dados.get("value", []):
                autor = ((m.get("from") or {}).get("user") or {})
                if m.get("messageType") != "message" or autor.get("id") in (None, meu_id):
                    continue
```

Pula o que não for mensagem normal (ex.: aviso de sistema) e as suas.

### Linhas 215 a 216

```python
                if self.hora_local(m["createdDateTime"]) <= desde:
                    continue
```

Pula as anteriores a `desde`.

### Linhas 217 a 219

```python
                novas.append({"chat_id": chat["id"], "user_id": autor["id"],
                              "nome": autor.get("displayName", "?"),
                              "texto": texto_puro((m.get("body") or {}).get("content"))})
```

Guarda chat, autor, nome e texto limpo.

### Linha 220

```python
        return novas
```

Devolve.

### Linhas 222 a 224

```python
    def email_de(self, user_id):
        u = self._get(f"/users/{user_id}", **{"$select": "displayName,mail,userPrincipalName"})
        return u.get("mail") or u.get("userPrincipalName")
```

E-mail de um usuário pelo id: o campo `mail` ou, se vazio, o nome de login.

### Linha 226

```python
    def buscar_pessoa(self, nome):
```

Procura uma pessoa pelo nome.

### Linha 227

```python
        """'Ana' -> lista de (nome completo, e-mail) das pessoas com quem você mais fala."""
```

Docstring.

### Linha 228

```python
        dados = self._get("/me/people", **{"$search": f'"{nome}"', "$top": 5})
```

`/me/people` busca entre as pessoas com quem você mais conversa.

### Linhas 229 a 233

```python
        achados = []
        for p in dados.get("value", []):
            emails = p.get("scoredEmailAddresses") or []
            if emails and emails[0].get("address"):
                achados.append((p.get("displayName", nome), emails[0]["address"]))
```

Para cada resultado com e-mail, guarda nome e o primeiro e-mail.

### Linha 234

```python
        return achados
```

Devolve.

### Linha 236

```python
    def horarios_livres(self, email, minutos, janelas, maximo=3):
```

Pergunta ao Outlook os horários livres dos dois.

### Linha 237

```python
        """Pergunta ao Outlook os horários livres para mim E para a outra pessoa."""
```

Docstring.

### Linha 238

```python
        fmt = "%Y-%m-%dT%H:%M:%S"
```

Formato de data sem fuso (o fuso vai num campo separado).

### Linhas 239 a 247

```python
        payload = {
            "attendees": [{"type": "required", "emailAddress": {"address": email}}],
            "timeConstraint": {"activityDomain": "unrestricted", "timeSlots": [
                {"start": {"dateTime": a.strftime(fmt), "timeZone": self.fuso_windows},
                 "end": {"dateTime": b.strftime(fmt), "timeZone": self.fuso_windows}} for a, b in janelas]},
            "meetingDuration": f"PT{int(minutos)}M",
            "maxCandidates": 20, "isOrganizerOptional": False,
            "returnSuggestionReasons": True, "minimumAttendeePercentage": 100,
        }
```

Corpo da chamada `findMeetingTimes`:
- `attendees`: a outra pessoa como obrigatória (você, o organizador, entra automaticamente).
- `timeConstraint`: as janelas de expediente calculadas antes, cada uma com início, fim e fuso.
- `meetingDuration`: duração no formato ISO 8601 (`PT30M` é 30 minutos).
- `maxCandidates`: até 20 sugestões.
- `isOrganizerOptional: False`: você precisa estar livre também.
- `minimumAttendeePercentage: 100`: todos precisam poder.

### Linha 248

```python
        dados = self._post("/me/findMeetingTimes", payload)
```

Faz a chamada.

### Linha 249

```python
        sugestoes = dados.get("meetingTimeSuggestions", [])
```

Lista de sugestões.

### Linhas 250 a 252

```python
        if not sugestoes:
            motivo = dados.get("emptySuggestionsReason") or "sem horário em comum"
            raise net.ApiError("Microsoft", f"nenhum horário livre ({motivo})")
```

Sem sugestões: lança erro com o motivo que o Outlook deu.

### Linhas 253 a 255

```python
        horarios = [Horario(self.hora_local(s["meetingTimeSlot"]["start"]["dateTime"]),
                            self.hora_local(s["meetingTimeSlot"]["end"]["dateTime"]),
                            float(s.get("confidence", 100))) for s in sugestoes]
```

Converte cada sugestão em `Horario` com início, fim e confiança.

### Linha 256

```python
        horarios.sort(key=lambda h: h.inicio)
```

Ordena por horário.

### Linha 257

```python
        return espalhar(horarios, maximo)
```

Escolhe sugestões variadas (ver `espalhar`).

### Linha 259

```python
    def agendar(self, email, nome, horario, assunto):
```

Cria a reunião.

### Linha 260

```python
        fmt = "%Y-%m-%dT%H:%M:%S"
```

Formato de data.

### Linhas 261 a 267

```python
        ev = self._post("/me/events", {
            "subject": assunto,
            "start": {"dateTime": horario.inicio.strftime(fmt), "timeZone": self.fuso_windows},
            "end": {"dateTime": horario.fim.strftime(fmt), "timeZone": self.fuso_windows},
            "attendees": [{"type": "required", "emailAddress": {"address": email, "name": nome}}],
            "isOnlineMeeting": True, "onlineMeetingProvider": "teamsForBusiness",
        })
```

POST em `/me/events` com assunto, início e fim no nosso fuso, a pessoa como convidada obrigatória e `isOnlineMeeting` com o provedor Teams, o que gera o link da reunião automaticamente. O Outlook manda o convite por e-mail para a pessoa.

### Linha 268

```python
        return ev.get("webLink", "")
```

Devolve o link do evento.

### Linhas 270 a 271

```python
    def responder(self, chat_id, texto_html):
        self._post(f"/chats/{chat_id}/messages", {"body": {"contentType": "html", "content": texto_html}})
```

Responde num chat do Teams com uma mensagem em HTML.

### Linha 274

```python
def espalhar(horarios, maximo):
```

Escolhe sugestões variadas.

### Linhas 275 a 278

```python
    """Escolhe sugestões variadas: evita oferecer 14:00, 14:30 e 15:00 do mesmo dia.

    Pega no máximo uma por dia primeiro; se faltar, completa com as restantes.
    """
```

Docstring: evita oferecer três horários seguidos no mesmo dia; primeiro pega no máximo um por dia e depois completa.

### Linha 279

```python
    escolhidos, dias = [], set()
```

Escolhidos e dias já usados.

### Linhas 280 a 285

```python
    for h in horarios:
        if h.inicio.date() not in dias:
            escolhidos.append(h)
            dias.add(h.inicio.date())
        if len(escolhidos) == maximo:
            return escolhidos
```

Primeira passada: pega o primeiro horário de cada dia. Se já tem o máximo, devolve.

### Linhas 286 a 290

```python
    for h in horarios:
        if h not in escolhidos:
            escolhidos.append(h)
        if len(escolhidos) == maximo:
            break
```

Segunda passada: completa com os que sobraram.

### Linha 291

```python
    return sorted(escolhidos, key=lambda h: h.inicio)
```

Devolve ordenados por horário.
