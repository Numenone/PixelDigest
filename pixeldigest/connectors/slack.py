"""Slack: mensagens das últimas 24 h nos canais escolhidos, nas DMs e nos grupos.

Autenticação: Bearer Token.
- Token de USUÁRIO (xoxp-), o recomendado: lê como você. Vê seus canais privados
  (ex.: #it-support) e suas DMs, sem precisar convidar ninguém.
  Escopos de usuário: channels:history, channels:read, groups:history, groups:read,
  im:history, im:read, mpim:history, mpim:read, users:read.
- Token de BOT (xoxb-): só lê canais em que o bot foi convidado e nunca lê DMs.

As listas do Slack vêm em páginas (cursor); _paginar() junta todas.

Particularidade do Slack: erros vêm com HTTP 200 e {"ok": false, "error": "..."},
então além do status precisamos validar o campo "ok".
"""
import re
from datetime import datetime, timedelta

from .. import net
from ..models import ALTA, NORMAL, URGENTE, Item
from .base import Conector

API = "https://slack.com/api/"
URGENTE_RE = re.compile(r"\b(urgente|asap|hoje|agora|importante|prazo)\b", re.I)


class SlackConector(Conector):
    tipo = "slack"

    def __init__(self, empresa, opcoes, cfg):
        super().__init__(empresa, opcoes, cfg)
        self.token = self.opcao("token")
        self.meu_id = self.opcao("meu_id", obrigatorio=False)
        self._nomes = {}      # cache: id do usuário -> nome
        self.avisos = []      # canais pulados nesta coleta (apagados, sem acesso...)
        self._por_canal = {}  # mensagens já trazidas de cada canal (últimas 24 h)
        self._ultimo = {}     # timestamp da mensagem mais nova de cada canal

    def _api(self, metodo, **params):
        dados = net.get_json("Slack", API + metodo, client=self.client, params=params,
                             headers={"Authorization": f"Bearer {self.token}"})
        if not dados.get("ok"):
            raise net.ApiError("Slack", f"{metodo} falhou: {dados.get('error', 'erro desconhecido')}")
        return dados

    def _paginar(self, metodo, chave, maximo=1000, **params):
        """Junta todas as páginas de uma lista do Slack (o Slack devolve aos pedaços)."""
        tudo, cursor = [], None
        while len(tudo) < maximo:
            if cursor:
                params["cursor"] = cursor
            dados = self._api(metodo, **params)
            tudo += dados.get(chave, [])
            cursor = (dados.get("response_metadata") or {}).get("next_cursor")
            if not cursor:
                break
        return tudo[:maximo]

    def _nome(self, user_id):
        if user_id not in self._nomes:
            try:
                u = self._api("users.info", user=user_id)["user"]
                self._nomes[user_id] = u.get("profile", {}).get("display_name") or u.get("real_name") or user_id
            except net.ApiError:
                self._nomes[user_id] = user_id
        return self._nomes[user_id]

    def limpar(self, texto):
        """Troca <@U123> por @nome e <http://x|rótulo> por rótulo."""
        texto = re.sub(r"<@(\w+)>", lambda m: "@" + self._nome(m.group(1)), texto)
        texto = re.sub(r"<([^|>]+)\|([^>]+)>", r"\2", texto)
        texto = re.sub(r"<(https?://[^>]+)>", r"\1", texto)
        return " ".join(texto.split())

    def canais(self):
        """Lista de (id, nome) a ler: os canais do config + DMs se incluir_dms: true."""
        lista = []
        for cid in self.opcoes.get("canais", []):
            try:
                nome = "#" + self._api("conversations.info", channel=cid)["channel"]["name"]
            except net.ApiError:
                nome = cid
            lista.append((cid, nome))
        if self.opcoes.get("incluir_dms"):
            # users.conversations = conversas de que EU participo (precisa de token xoxp)
            try:
                conversas = self._paginar("users.conversations", "channels", 150, types="im,mpim",
                                          exclude_archived="true", limit=200)
            except net.ApiError as exc:
                motivo = "precisa do token de usuário (xoxp-)" if "missing_scope" in str(exc) else str(exc)
                self.avisos.append(f"DMs: {motivo}")
                conversas = []
            # o Slack dá uma "prioridade" para cada conversa: lê só as 40 mais importantes,
            # para não estourar o limite de chamadas da API (HTTP 429)
            conversas = [c for c in conversas if not c.get("is_user_deleted")]
            conversas.sort(key=lambda c: c.get("priority") or 0, reverse=True)
            for c in conversas[:40]:
                if c.get("is_im"):
                    lista.append((c["id"], "DM " + self._nome(c.get("user", ""))))
                else:
                    lista.append((c["id"], "Grupo " + c.get("name", "").replace("mpdm-", "")[:30]))
        return lista

    def coletar(self):
        desde = (datetime.now() - timedelta(hours=24)).timestamp()
        if not self.meu_id and self.token.startswith("xoxp-"):
            self.meu_id = self._api("auth.test").get("user_id", "")     # token de usuário: descobre quem sou eu
        itens, self.avisos = [], []
        for cid, nome_canal in self.canais():   # canais() pode acrescentar avisos (ex.: DMs sem permissão)
            # só pede o que chegou depois da última mensagem que já temos deste canal
            a_partir = max(desde, self._ultimo.get(cid, 0))
            try:
                msgs = self._api("conversations.history", channel=cid, oldest=f"{a_partir:.6f}", limit=50)["messages"]
            except net.ApiError as exc:
                # um canal apagado ou sem acesso não pode derrubar o resumo inteiro: pula e avisa
                self.avisos.append(f"{nome_canal}: {str(exc).split('falhou: ')[-1]}")
                itens += [i for i in self._por_canal.get(cid, []) if i.quando.timestamp() >= desde]
                continue
            novos = []
            for m in msgs:
                # Ignora entradas de sistema (alguém entrou no canal etc.) e mensagens minhas
                if m.get("subtype") or not m.get("text") or m.get("user") == self.meu_id:
                    continue
                texto = m["text"]
                prioridade = NORMAL
                if self.meu_id and f"<@{self.meu_id}>" in texto:
                    prioridade = URGENTE          # me marcaram
                elif nome_canal.startswith(("DM", "Grupo")):
                    prioridade = ALTA
                elif URGENTE_RE.search(texto):
                    prioridade = ALTA
                novos.append(Item(
                    empresa=self.empresa, fonte="slack", tipo="mensagem",
                    titulo=f"{self._nome(m.get('user', ''))}: {self.limpar(texto)[:90]}",
                    detalhe=nome_canal,
                    quando=datetime.fromtimestamp(float(m["ts"]), self.fuso),
                    prioridade=prioridade, id=f"{cid}:{m['ts']}",
                ))
            if msgs:
                self._ultimo[cid] = max(float(m["ts"]) for m in msgs) + 0.000001
            # junta as novas com as antigas e descarta o que passou de 24 h
            ja = {i.id for i in novos}
            juntas = novos + [i for i in self._por_canal.get(cid, []) if i.id not in ja and i.quando.timestamp() >= desde]
            self._por_canal[cid] = juntas
            itens += juntas
        return itens
