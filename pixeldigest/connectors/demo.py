"""Modo demonstração: dados inventados, sem nenhuma conta real.

Serve para o GitHub público e para a apresentação: mostra tudo funcionando sem
expor clientes nem mensagens de empresa nenhuma. Ative com --demo.
"""
from datetime import datetime, timedelta

from ..models import ALTA, NORMAL, URGENTE, Horario, Item
from .base import Conector

EMPRESAS_DEMO = [
    {"nome": "Acme Ltda", "cor": "#4fa3ff",
     "conectores": [{"tipo": "slack"}, {"tipo": "clickup"}, {"tipo": "gmail"}]},
    {"nome": "Contoso", "cor": "#7ad67a",
     "conectores": [{"tipo": "microsoft", "agendador": True}]},
]


class DemoConector(Conector):
    """Finge ser um conector real do tipo pedido."""

    def __init__(self, empresa, opcoes, cfg):
        super().__init__(empresa, opcoes, cfg)
        self.tipo = opcoes.get("tipo", "demo")
        self.usar = {"agendador": opcoes.get("agendador", self.tipo == "microsoft")}
        self.email = f"voce@{empresa.split()[0].lower()}.example" if self.tipo == "gmail" else ""
        agora = datetime.now().timestamp()
        # e-mails de exemplo para o "resumo dos e-mails" da demonstração
        self.mensagens = [
            {"id": "d1", "de": "Financeiro", "assunto": "Nota fiscal de outubro", "quando": agora - 3600,
             "texto": "Oi! Segue a nota fiscal de outubro. Precisamos da aprovação até sexta para pagar o fornecedor.",
             "nao_lido": True, "importante": True},
            {"id": "d2", "de": "Cliente Atlas", "assunto": "Proposta revisada", "quando": agora - 7200,
             "texto": "Recebemos a proposta, mas queremos rever o prazo de entrega. Podemos conversar amanhã?",
             "nao_lido": True, "importante": True},
            {"id": "d3", "de": "Newsletter", "assunto": "Novidades da semana", "quando": agora - 9000,
             "texto": "As 10 notícias mais lidas da semana.", "nao_lido": False, "importante": False},
        ] if self.tipo == "gmail" else []

    def coletar(self):
        hoje = self.inicio_do_dia()
        h = lambda horas, minutos=0: hoje + timedelta(hours=horas, minutes=minutos)  # noqa: E731
        e = self.empresa
        dados = {
            "slack": [
                Item(e, "slack", "mensagem", "Marina: @voce consegue revisar o fluxo de onboarding hoje?", "#operacoes", h(8, 42), prioridade=URGENTE, id="s1"),
                Item(e, "slack", "mensagem", "Rafael: subi a nova versão do relatório", "#dados", h(9, 10), id="s2"),
            ],
            "clickup": [
                Item(e, "clickup", "tarefa", "Enviar proposta para o cliente Atlas", "ATRASADA", h(-6), prioridade=URGENTE, id="c1"),
                Item(e, "clickup", "tarefa", "Configurar automação de boas-vindas", "em andamento", h(17), prioridade=ALTA, id="c2"),
                Item(e, "clickup", "tarefa", "Atualizar planilha de métricas", "a fazer", h(40), id="c3"),
            ],
            "gmail": [
                Item(e, "gmail", "email", "Financeiro: nota fiscal de outubro", "Segue em anexo a nota...", h(7, 55), prioridade=ALTA, id="g1"),
                Item(e, "gmail", "email", "Newsletter: novidades da semana", "", h(6, 30), prioridade=NORMAL, id="g2"),
            ],
            "microsoft": [
                Item(e, "outlook", "evento", "Daily do time", "Teams", h(9, 30), prioridade=ALTA, id="o1"),
                Item(e, "outlook", "evento", "Planejamento do trimestre", "Teams", h(15), prioridade=ALTA, id="o2"),
                Item(e, "teams", "mensagem", "Beatriz: vamos marcar uma call pra alinhar o projeto?", "chat", h(10, 5), prioridade=URGENTE, id="t1"),
                Item(e, "outlook", "email", "RH: confirmação do benefício", "", h(8, 15), id="o3"),
            ],
        }
        return dados.get(self.tipo, [])

    # ----- mesmas funções do MicrosoftConector, com respostas falsas -----
    def precisa_login(self):
        return False

    def mensagens_novas(self, desde):
        return []

    def email_de(self, user_id):
        return "beatriz@contoso.example"

    def buscar_pessoa(self, nome):
        nome = nome.strip().title()
        return [(f"{nome} Souza", f"{nome.lower().split()[0]}@contoso.example")]

    def horarios_livres(self, email, minutos, janelas, maximo=3):
        """Finge a resposta do Outlook: horários dentro das janelas pedidas."""
        if not janelas:      # sem janelas (só usado para imagens): próximo dia útil
            dia = self.agora() + timedelta(days=1)
            while dia.weekday() >= 5:
                dia += timedelta(days=1)
            base = dia.replace(hour=9, minute=0, second=0, microsecond=0)
            janelas = [(base, base.replace(hour=18))]
        candidatos = []
        for n, (ini, fim) in enumerate(janelas):
            opcoes = [(60, 330, 150), (330, 150, 60), (150, 60, 330)][n % 3]   # varia o horário de cada dia
            for desloc in ((0,) if len(janelas) == 1 and fim - ini <= timedelta(hours=4) else opcoes):
                inicio = ini + timedelta(minutes=desloc)
                if inicio + timedelta(minutes=minutos) <= fim:
                    candidatos.append(Horario(inicio, inicio + timedelta(minutes=minutos)))
        if not candidatos:
            from .. import net
            raise net.ApiError("Microsoft", "nenhum horário livre (demo)")
        from .microsoft import espalhar
        return espalhar(candidatos, maximo)

    def agendar(self, email, nome, horario, assunto):
        return "https://teams.microsoft.com/l/meetup-join/demo"

    def responder(self, chat_id, texto_html):
        pass


def pedido_demo(agora: datetime):
    """Mensagem falsa de alguém pedindo reunião (tecla F4 na demonstração)."""
    return {"chat_id": "demo-chat", "user_id": "demo-user", "nome": "Beatriz Lima",
            "texto": "Oi! Podemos marcar uma reunião essa semana pra alinhar o projeto?"}
