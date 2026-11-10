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
import html
import re
from datetime import datetime, timedelta

from .. import net
from ..config import TOKENS
from ..models import ALTA, NORMAL, URGENTE, Horario, Item
from .base import Conector

GRAPH = "https://graph.microsoft.com/v1.0"


def slug(texto):
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def texto_puro(conteudo_html):
    """Mensagens do Teams vêm em HTML: tira as tags e decodifica &amp; etc."""
    sem_tags = re.sub(r"<[^>]+>", " ", conteudo_html or "")
    return " ".join(html.unescape(sem_tags).split())


class MicrosoftConector(Conector):
    tipo = "microsoft"

    def __init__(self, empresa, opcoes, cfg):
        super().__init__(empresa, opcoes, cfg)
        self.client_id = self.opcao("client_id")
        self.tenant = self.opcao("tenant", obrigatorio=False) or "organizations"
        self.arquivo_token = TOKENS / f"ms-{slug(empresa)}.json"
        self.fuso_windows = cfg["usuario"]["fuso_windows"]
        self.usar = {k: opcoes.get(k, True) for k in ("email", "agenda", "teams", "agendador")}
        self._app = None
        self._cache = None
        self._eu = None

    # ---------- OAuth (MSAL) ----------
    def escopos(self):
        s = ["User.Read"]
        if self.usar["email"]:
            s.append("Mail.Read")
        if self.usar["agenda"] or self.usar["agendador"]:
            s.append("Calendars.ReadWrite")
        if self.usar["teams"] or self.usar["agendador"]:
            s += ["Chat.Read", "ChatMessage.Send"]
        if self.usar["agendador"]:
            s += ["People.Read", "User.ReadBasic.All"]
        return s

    def _msal(self):
        import msal
        if self._app is None:
            self._cache = msal.SerializableTokenCache()
            if self.arquivo_token.exists():
                self._cache.deserialize(self.arquivo_token.read_text(encoding="utf-8"))
            self._app = msal.PublicClientApplication(
                self.client_id, authority=f"https://login.microsoftonline.com/{self.tenant}",
                token_cache=self._cache)
        return self._app

    def _salvar_cache(self):
        if self._cache is not None and self._cache.has_state_changed:
            self.arquivo_token.write_text(self._cache.serialize(), encoding="utf-8")

    def precisa_login(self):
        return not self._msal().get_accounts()

    def login(self, mostrar_codigo=None):
        """Login por código: mostra um código que você digita em microsoft.com/devicelogin.

        mostrar_codigo(url, codigo): a tela de Configurações usa para exibir o código grande.
        Sem ela, o código é impresso no terminal.
        """
        app = self._msal()
        flow = app.initiate_device_flow(scopes=self.escopos())
        if "user_code" not in flow:
            raise net.ApiError("Microsoft", f"não deu para iniciar o login: {flow.get('error_description')}")
        if mostrar_codigo:
            mostrar_codigo(flow["verification_uri"], flow["user_code"])
        else:
            print(flow["message"])
        resultado = app.acquire_token_by_device_flow(flow)    # espera você autorizar no navegador
        if "access_token" not in resultado:
            raise net.ApiError("Microsoft", resultado.get("error_description", "login recusado"))
        self._salvar_cache()

    def _token(self):
        app = self._msal()
        contas = app.get_accounts()
        resultado = app.acquire_token_silent(self.escopos(), account=contas[0]) if contas else None
        if not resultado or "access_token" not in resultado:
            raise net.ApiError("Microsoft", "falta fazer o login (Configurações > Chaves de API > Fazer login)")
        self._salvar_cache()
        return resultado["access_token"]

    def _headers(self):
        return {"Authorization": f"Bearer {self._token()}",
                # Faz o Outlook devolver os horários já no nosso fuso
                "Prefer": f'outlook.timezone="{self.fuso_windows}"'}

    def _get(self, caminho, **params):
        return net.get_json("Microsoft", GRAPH + caminho, client=self.client, params=params, headers=self._headers())

    def _post(self, caminho, payload):
        return net.post_json("Microsoft", GRAPH + caminho, payload, client=self.client, headers=self._headers())

    def hora_local(self, valor):
        """Converte datas do Graph para o nosso fuso.

        Eventos vêm sem fuso ("2026-11-06T14:00:00.0000000", já no fuso pedido no Prefer);
        mensagens vêm em UTC ("2026-11-06T17:01:02.123Z").
        """
        if valor.endswith("Z") or "+" in valor[10:]:
            return datetime.fromisoformat(valor.replace("Z", "+00:00")).astimezone(self.fuso)
        return datetime.fromisoformat(valor[:19]).replace(tzinfo=self.fuso)

    def eu(self):
        if self._eu is None:
            self._eu = self._get("/me", **{"$select": "id,displayName,mail,userPrincipalName"})
        return self._eu

    # ---------- coleta para o resumo ----------
    def eventos(self):
        dados = self._get("/me/calendarView", **{
            "startDateTime": self.inicio_do_dia().isoformat(),
            "endDateTime": self.fim_de_amanha().isoformat(),
            "$select": "id,subject,start,isOnlineMeeting,webLink,isCancelled,organizer",
            "$orderby": "start/dateTime", "$top": 30})
        return [Item(
            empresa=self.empresa, fonte="outlook", tipo="evento",
            titulo=ev.get("subject") or "(sem título)",
            detalhe="Teams" if ev.get("isOnlineMeeting") else "",
            quando=self.hora_local(ev["start"]["dateTime"]),
            url=ev.get("webLink", ""), prioridade=ALTA, id=ev["id"],
        ) for ev in dados.get("value", []) if not ev.get("isCancelled")]

    def emails(self):
        dados = self._get("/me/mailFolders/inbox/messages", **{
            "$filter": "isRead eq false", "$top": 15,
            "$select": "id,subject,from,receivedDateTime,importance,webLink,bodyPreview"})
        itens = []
        for m in dados.get("value", []):
            remetente = (m.get("from") or {}).get("emailAddress", {}).get("name", "?")
            itens.append(Item(
                empresa=self.empresa, fonte="outlook", tipo="email",
                titulo=f"{remetente}: {m.get('subject') or '(sem assunto)'}",
                detalhe=(m.get("bodyPreview") or "")[:120],
                quando=self.hora_local(m["receivedDateTime"]), url=m.get("webLink", ""),
                prioridade=ALTA if m.get("importance") == "high" else NORMAL, id=m["id"]))
        return itens

    def chats(self):
        """Lista os chats com a prévia da última mensagem (uma chamada só)."""
        return self._get("/me/chats", **{"$expand": "lastMessagePreview", "$top": 50}).get("value", [])

    def mensagens_teams(self):
        """Chats com mensagem de outra pessoa ainda não lida nas últimas 24 h."""
        meu_id = self.eu()["id"]
        limite = self.agora() - timedelta(hours=24)
        itens = []
        for chat in self.chats():
            prev = chat.get("lastMessagePreview") or {}
            autor = ((prev.get("from") or {}).get("user") or {})
            if not prev or autor.get("id") in (None, meu_id):
                continue
            criada = self.hora_local(prev["createdDateTime"])
            lida = (chat.get("viewpoint") or {}).get("lastMessageReadDateTime")
            if criada < limite or (lida and self.hora_local(lida) >= criada):
                continue
            itens.append(Item(
                empresa=self.empresa, fonte="teams", tipo="mensagem",
                titulo=f"{autor.get('displayName', '?')}: {texto_puro(prev.get('body', {}).get('content'))[:90]}",
                detalhe=chat.get("topic") or "chat", quando=criada, url=chat.get("webUrl", ""),
                prioridade=URGENTE if chat.get("chatType") == "oneOnOne" else ALTA,
                id=f"{chat['id']}:{prev.get('id')}"))
        return itens

    def coletar(self):
        itens = []
        if self.usar["agenda"]:
            itens += self.eventos()
        if self.usar["email"]:
            itens += self.emails()
        if self.usar["teams"]:
            itens += self.mensagens_teams()
        return itens

    # ---------- agendador de reuniões ----------
    def mensagens_novas(self, desde):
        """Mensagens de outras pessoas no Teams depois de 'desde' (para achar pedidos de reunião)."""
        meu_id = self.eu()["id"]
        novas = []
        for chat in self.chats():
            prev = chat.get("lastMessagePreview") or {}
            if not prev or self.hora_local(prev["createdDateTime"]) <= desde:
                continue
            dados = self._get(f"/me/chats/{chat['id']}/messages", **{"$top": 10})
            for m in dados.get("value", []):
                autor = ((m.get("from") or {}).get("user") or {})
                if m.get("messageType") != "message" or autor.get("id") in (None, meu_id):
                    continue
                if self.hora_local(m["createdDateTime"]) <= desde:
                    continue
                novas.append({"chat_id": chat["id"], "user_id": autor["id"],
                              "nome": autor.get("displayName", "?"),
                              "texto": texto_puro((m.get("body") or {}).get("content"))})
        return novas

    def email_de(self, user_id):
        u = self._get(f"/users/{user_id}", **{"$select": "displayName,mail,userPrincipalName"})
        return u.get("mail") or u.get("userPrincipalName")

    def buscar_pessoa(self, nome):
        """'Ana' -> lista de (nome completo, e-mail) das pessoas com quem você mais fala."""
        dados = self._get("/me/people", **{"$search": f'"{nome}"', "$top": 5})
        achados = []
        for p in dados.get("value", []):
            emails = p.get("scoredEmailAddresses") or []
            if emails and emails[0].get("address"):
                achados.append((p.get("displayName", nome), emails[0]["address"]))
        return achados

    def horarios_livres(self, email, minutos, janelas, maximo=3):
        """Pergunta ao Outlook os horários livres para mim E para a outra pessoa."""
        fmt = "%Y-%m-%dT%H:%M:%S"
        payload = {
            "attendees": [{"type": "required", "emailAddress": {"address": email}}],
            "timeConstraint": {"activityDomain": "unrestricted", "timeSlots": [
                {"start": {"dateTime": a.strftime(fmt), "timeZone": self.fuso_windows},
                 "end": {"dateTime": b.strftime(fmt), "timeZone": self.fuso_windows}} for a, b in janelas]},
            "meetingDuration": f"PT{int(minutos)}M",
            "maxCandidates": 20, "isOrganizerOptional": False,
            "returnSuggestionReasons": True, "minimumAttendeePercentage": 100,
        }
        dados = self._post("/me/findMeetingTimes", payload)
        sugestoes = dados.get("meetingTimeSuggestions", [])
        if not sugestoes:
            motivo = dados.get("emptySuggestionsReason") or "sem horário em comum"
            raise net.ApiError("Microsoft", f"nenhum horário livre ({motivo})")
        horarios = [Horario(self.hora_local(s["meetingTimeSlot"]["start"]["dateTime"]),
                            self.hora_local(s["meetingTimeSlot"]["end"]["dateTime"]),
                            float(s.get("confidence", 100))) for s in sugestoes]
        horarios.sort(key=lambda h: h.inicio)
        return espalhar(horarios, maximo)

    def agendar(self, email, nome, horario, assunto):
        fmt = "%Y-%m-%dT%H:%M:%S"
        ev = self._post("/me/events", {
            "subject": assunto,
            "start": {"dateTime": horario.inicio.strftime(fmt), "timeZone": self.fuso_windows},
            "end": {"dateTime": horario.fim.strftime(fmt), "timeZone": self.fuso_windows},
            "attendees": [{"type": "required", "emailAddress": {"address": email, "name": nome}}],
            "isOnlineMeeting": True, "onlineMeetingProvider": "teamsForBusiness",
        })
        return ev.get("webLink", "")

    def responder(self, chat_id, texto_html):
        self._post(f"/chats/{chat_id}/messages", {"body": {"contentType": "html", "content": texto_html}})


def espalhar(horarios, maximo):
    """Escolhe sugestões variadas: evita oferecer 14:00, 14:30 e 15:00 do mesmo dia.

    Pega no máximo uma por dia primeiro; se faltar, completa com as restantes.
    """
    escolhidos, dias = [], set()
    for h in horarios:
        if h.inicio.date() not in dias:
            escolhidos.append(h)
            dias.add(h.inicio.date())
        if len(escolhidos) == maximo:
            return escolhidos
    for h in horarios:
        if h not in escolhidos:
            escolhidos.append(h)
        if len(escolhidos) == maximo:
            break
    return sorted(escolhidos, key=lambda h: h.inicio)

