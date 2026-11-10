"""Gmail + Google Agenda (OAuth 2.0). Dá para ter várias contas (uma por conector).

Login: botão "Fazer login" nas Configurações. Abre o navegador, você autoriza, e o
token fica em tokens/google-<conta>.json (fora do GitHub). Depois o token é
renovado sozinho com o refresh token (POST simples no Google, sem bibliotecas pesadas).

Para não ficar baixando tudo de novo:
- tem_novidade() faz UMA chamada barata (o "historyId" da caixa). Só se mudou é que
  os e-mails são lidos de novo; a agenda é relida no máximo a cada 30 minutos.

Escopos só de leitura: gmail.readonly e calendar.readonly.
"""
import base64
import html
import json
import re
import time
from datetime import datetime

from .. import net
from ..config import ROOT, TOKENS
from ..models import ALTA, NORMAL, Item
from .base import Conector

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly",
          "https://www.googleapis.com/auth/calendar.readonly"]
GMAIL = "https://gmail.googleapis.com/gmail/v1/users/me/"
AGENDA = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
BUSCA_PADRAO = "newer_than:1d in:inbox -category:promotions -category:social"
AGENDA_A_CADA = 30 * 60       # segundos entre leituras da agenda


def texto_do_email(payload, limite=1500):
    """Tira o texto de um e-mail do Gmail (partes em base64), sem citações de respostas antigas."""
    def partes(p):
        yield p
        for filho in p.get("parts", []) or []:
            yield from partes(filho)

    simples, rico = "", ""
    for p in partes(payload):
        dados = (p.get("body") or {}).get("data")
        if not dados:
            continue
        conteudo = base64.urlsafe_b64decode(dados + "=" * (-len(dados) % 4)).decode("utf-8", "replace")
        if p.get("mimeType") == "text/plain" and not simples:
            simples = conteudo
        elif p.get("mimeType") == "text/html" and not rico:
            rico = re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", conteudo, flags=re.S | re.I)
            rico = html.unescape(re.sub(r"<[^>]+>", " ", rico))
    texto = simples or rico
    # corta a parte citada ("Em ... escreveu:" / "On ... wrote:") e linhas começando com ">"
    texto = re.split(r"\n(?:Em .{5,80} escreveu:|On .{5,80} wrote:)", texto)[0]
    linhas = [l.strip() for l in texto.splitlines() if l.strip() and not l.strip().startswith(">")]
    return " ".join(" ".join(linhas).split())[:limite]


class GmailConector(Conector):
    tipo = "gmail"

    def __init__(self, empresa, opcoes, cfg):
        super().__init__(empresa, opcoes, cfg)
        self.conta = opcoes.get("conta", "padrao")
        self.arquivo_token = TOKENS / f"google-{self.conta}.json"
        self.segredo = str(ROOT / self.opcao("credenciais"))   # arquivo baixado do Google Cloud
        self.busca = opcoes.get("busca", BUSCA_PADRAO)
        self.com_agenda = opcoes.get("agenda", True)
        self.email = opcoes.get("email", "")
        self.mensagens = []            # os 10 e-mails mais recentes (para o resumo com IA)
        self._historico = None         # historyId da última leitura
        self._eventos, self._agenda_em = [], 0
        self._acesso, self._expira = None, 0

    @property
    def nome(self):
        return f"{self.empresa} / gmail{(' ' + self.email) if self.email else ''}"

    # ---------- OAuth ----------
    def precisa_login(self):
        return not self.arquivo_token.exists()

    def login(self):
        """Abre o navegador para autorizar. Devolve o e-mail da conta conectada."""
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(self.segredo, SCOPES)
        creds = flow.run_local_server(port=0, prompt="consent select_account")
        self.arquivo_token.write_text(creds.to_json(), encoding="utf-8")
        self._acesso, self._expira = None, 0
        self.email = self._get(GMAIL + "profile").get("emailAddress", "")
        return self.email

    def _token(self):
        """Token de acesso válido; renova com o refresh token quando vence (a cada ~1 h)."""
        if self._acesso and time.time() < self._expira - 60:
            return self._acesso
        if self.precisa_login():
            raise net.ApiError("Google", "falta fazer o login (Configurações > Chaves de API > Fazer login)")
        salvo = json.loads(self.arquivo_token.read_text(encoding="utf-8"))
        try:
            r = net.request("Google", "POST", salvo.get("token_uri", "https://oauth2.googleapis.com/token"), data={
                "client_id": salvo["client_id"], "client_secret": salvo["client_secret"],
                "refresh_token": salvo["refresh_token"], "grant_type": "refresh_token"}, client=self.client)
        except net.ApiError as exc:
            raise net.ApiError("Google", f"o login venceu ou foi revogado; faça o login de novo ({exc})") from exc
        dados = r.json()
        self._acesso, self._expira = dados["access_token"], time.time() + int(dados.get("expires_in", 3600))
        salvo["token"] = self._acesso
        self.arquivo_token.write_text(json.dumps(salvo), encoding="utf-8")
        return self._acesso

    def _get(self, url, **params):
        return net.get_json("Google", url, client=self.client, params=params,
                            headers={"Authorization": f"Bearer {self._token()}"})

    # ---------- novidades (barato) ----------
    def tem_novidade(self):
        """True se chegou e-mail novo (1 chamada) ou se a agenda já está velha (30 min)."""
        perfil = self._get(GMAIL + "profile")
        self.email = perfil.get("emailAddress", self.email)
        mudou = perfil.get("historyId") != self._historico
        agenda_velha = self.com_agenda and time.time() - self._agenda_em > AGENDA_A_CADA
        return mudou or agenda_velha

    # ---------- coleta ----------
    def ler_emails(self):
        """Os 10 e-mails mais recentes das últimas 24 h, com o texto (usado na lista e no resumo)."""
        perfil = self._get(GMAIL + "profile")
        self.email = perfil.get("emailAddress", self.email)
        if perfil.get("historyId") == self._historico and self.mensagens:
            return self.mensagens                      # nada novo: reaproveita
        lista = self._get(GMAIL + "messages", q=self.busca, maxResults=10).get("messages", [])
        anteriores = {m["id"]: m for m in self.mensagens}
        mensagens = []
        for ref in lista:
            if ref["id"] in anteriores:                # já lido antes: não baixa de novo
                mensagens.append(anteriores[ref["id"]])
                continue
            m = self._get(GMAIL + f"messages/{ref['id']}", format="full")
            cab = {h["name"].lower(): h["value"] for h in m.get("payload", {}).get("headers", [])}
            mensagens.append({
                "id": ref["id"],
                "de": cab.get("from", "?").split("<")[0].strip().strip('"'),
                "assunto": cab.get("subject", "(sem assunto)"),
                "quando": int(m["internalDate"]) / 1000,
                "texto": texto_do_email(m.get("payload", {})) or m.get("snippet", ""),
                "nao_lido": "UNREAD" in m.get("labelIds", []),
                "importante": "IMPORTANT" in m.get("labelIds", []),
            })
        self.mensagens, self._historico = mensagens, perfil.get("historyId")
        return mensagens

    def emails(self):
        link = f"https://mail.google.com/mail/?authuser={self.email}#inbox/" if self.email else "https://mail.google.com/mail/#inbox/"
        return [Item(
            empresa=self.empresa, fonte="gmail", tipo="email",
            titulo=f"{m['de']}: {m['assunto']}", detalhe=m["texto"][:120],
            quando=datetime.fromtimestamp(m["quando"], self.fuso), url=link + m["id"],
            prioridade=ALTA if m["importante"] else NORMAL, id=m["id"],
        ) for m in self.ler_emails()]

    def eventos(self):
        if time.time() - self._agenda_em < AGENDA_A_CADA and self._agenda_em:
            return self._eventos                      # agenda lida há pouco: reaproveita
        dados = self._get(AGENDA, timeMin=self.inicio_do_dia().isoformat(),
                          timeMax=self.fim_de_amanha().isoformat(),
                          singleEvents="true", orderBy="startTime", maxResults=20)
        itens = []
        for ev in dados.get("items", []):
            inicio = ev.get("start", {})
            if "dateTime" in inicio:
                quando = datetime.fromisoformat(inicio["dateTime"]).astimezone(self.fuso)
            else:  # evento de dia inteiro
                quando = datetime.fromisoformat(inicio["date"]).replace(tzinfo=self.fuso)
            itens.append(Item(
                empresa=self.empresa, fonte="google_agenda", tipo="evento",
                titulo=ev.get("summary", "(sem título)"),
                detalhe="Google Meet" if ev.get("hangoutLink") else ("Zoom" if "zoom.us" in json.dumps(ev) else ""),
                quando=quando, url=ev.get("htmlLink", ""), prioridade=ALTA, id=ev["id"],
            ))
        self._eventos, self._agenda_em = itens, time.time()
        return itens

    def coletar(self):
        itens = self.emails()
        if self.com_agenda:
            itens += self.eventos()
        return itens
