"""Zoom: reuniões agendadas para hoje e amanhã (o "calendário do Zoom").

Autenticação: app "Server-to-Server OAuth" criado em marketplace.zoom.us
(Develop > Build App > Server-to-Server OAuth). Ele dá três valores:
Account ID, Client ID e Client Secret. O token (vale 1 h) é pedido com Basic Auth.
Escopo necessário: meeting:read:list_meetings:admin (ou meeting:read:admin).

A agenda do Zoom muda pouco, então é relida a cada 30 minutos.
"""
import base64
import time
from datetime import datetime

from .. import net
from ..models import ALTA, Item
from .base import Conector

API = "https://api.zoom.us/v2/"


class ZoomConector(Conector):
    tipo = "zoom"

    def __init__(self, empresa, opcoes, cfg):
        super().__init__(empresa, opcoes, cfg)
        self.account_id = self.opcao("account_id")
        self.client_id = self.opcao("client_id")
        self.client_secret = self.opcao("client_secret")
        self.usuario = self.opcao("email", obrigatorio=False) or "me"   # e-mail da sua conta Zoom
        self._acesso, self._expira = None, 0

    def _token(self):
        if self._acesso and time.time() < self._expira - 60:
            return self._acesso
        basico = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        r = net.request("Zoom", "POST", "https://zoom.us/oauth/token", client=self.client,
                        params={"grant_type": "account_credentials", "account_id": self.account_id},
                        headers={"Authorization": f"Basic {basico}"})
        dados = r.json()
        self._acesso, self._expira = dados["access_token"], time.time() + int(dados.get("expires_in", 3600))
        return self._acesso

    def coletar(self):
        dados = net.get_json("Zoom", API + f"users/{self.usuario}/meetings", client=self.client,
                             params={"type": "upcoming", "page_size": 50},
                             headers={"Authorization": f"Bearer {self._token()}"})
        inicio, fim = self.inicio_do_dia(), self.fim_de_amanha()
        itens = []
        for r in dados.get("meetings", []):
            if not r.get("start_time"):
                continue                                   # reunião sem horário fixo
            quando = datetime.fromisoformat(r["start_time"].replace("Z", "+00:00")).astimezone(self.fuso)
            if not inicio <= quando < fim:
                continue
            itens.append(Item(
                empresa=self.empresa, fonte="zoom", tipo="evento", titulo=r.get("topic") or "Reunião Zoom",
                detalhe=f"Zoom · {r.get('duration', 0)} min", quando=quando,
                url=r.get("join_url", ""), prioridade=ALTA, id=str(r.get("id")),
            ))
        return itens
