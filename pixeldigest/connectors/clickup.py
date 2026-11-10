"""ClickUp: tarefas atribuídas a mim que vencem até amanhã (inclui as atrasadas).

Autenticação: token pessoal (pk_...) no header Authorization (sem "Bearer").
Datas do ClickUp vêm em milissegundos desde 1970, como texto.
"""
from datetime import datetime

from .. import net
from ..models import ALTA, BAIXA, NORMAL, URGENTE, Item
from .base import Conector

API = "https://api.clickup.com/api/v2/"
# Prioridade do ClickUp (1 urgente ... 4 baixa) -> a nossa
PRIORIDADES = {"1": URGENTE, "2": ALTA, "3": NORMAL, "4": BAIXA}


class ClickUpConector(Conector):
    tipo = "clickup"

    def __init__(self, empresa, opcoes, cfg):
        super().__init__(empresa, opcoes, cfg)
        self.token = self.opcao("token")
        self.equipe = self.opcao("equipe_id")
        self._meu_id = None

    def _get(self, caminho, **params):
        return net.get_json("ClickUp", API + caminho, client=self.client, params=params,
                            headers={"Authorization": self.token})

    def meu_id(self):
        if self._meu_id is None:
            self._meu_id = self._get("user")["user"]["id"]
        return self._meu_id

    def coletar(self):
        limite_ms = int(self.fim_de_amanha().timestamp() * 1000)
        dados = self._get(f"team/{self.equipe}/task", **{
            "assignees[]": self.meu_id(), "due_date_lt": limite_ms,
            "include_closed": "false", "subtasks": "true", "order_by": "due_date",
        })
        agora = self.agora()
        itens = []
        for t in dados.get("tasks", []):
            if not t.get("due_date"):
                continue
            vence = datetime.fromtimestamp(int(t["due_date"]) / 1000, self.fuso)
            prio = PRIORIDADES.get(str((t.get("priority") or {}).get("id", "3")), NORMAL)
            atrasada = vence < agora
            if atrasada:
                prio = URGENTE
            itens.append(Item(
                empresa=self.empresa, fonte="clickup", tipo="tarefa",
                titulo=t["name"],
                detalhe=("ATRASADA" if atrasada else t.get("status", {}).get("status", "")),
                quando=vence, url=t.get("url", ""), prioridade=prio, id=t["id"],
            ))
        return itens
