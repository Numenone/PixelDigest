"""Monta os conectores a partir do config.yaml.

Para adicionar um serviço novo, crie o arquivo do conector e registre o tipo aqui.
"""
from ..config import ConfigError
from .clickup import ClickUpConector
from .demo import EMPRESAS_DEMO, DemoConector
from .google import GmailConector
from .microsoft import MicrosoftConector
from .slack import SlackConector
from .zoom import ZoomConector

TIPOS = {
    "slack": SlackConector,
    "clickup": ClickUpConector,
    "gmail": GmailConector,
    "microsoft": MicrosoftConector,   # Outlook + Teams
    "zoom": ZoomConector,             # reuniões agendadas no Zoom
}


def montar(cfg):
    """Devolve (conectores, erros). No modo demo, usa empresas inventadas.

    Um conector mal configurado (ex.: token faltando no .env) vira um erro na
    lista, mas não impede os outros de funcionarem.
    """
    if cfg.get("demo"):
        cfg["empresas"] = EMPRESAS_DEMO
        return [DemoConector(emp["nome"], con, cfg) for emp in EMPRESAS_DEMO for con in emp["conectores"]], []
    conectores, erros = [], []
    for emp in cfg["empresas"]:
        if emp.get("ativa", True) is False:      # empresa desligada nas Configurações
            continue
        for con in emp["conectores"]:
            try:
                conectores.append(TIPOS[con["tipo"]](emp["nome"], con, cfg))
            except ConfigError as exc:
                erros.append(f"{emp['nome']} / {con['tipo']}: {exc}")
    return conectores, erros
