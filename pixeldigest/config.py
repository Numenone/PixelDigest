"""Carrega, valida e salva a configuração.

Tudo é configurado pela tela de Configurações do próprio app. Ela grava em dois arquivos:
- config.yaml: o que monitorar (empresas, serviços, horários, local do clima). Sem segredos.
- .env: as chaves de API e tokens (requisito 4). Nunca vai para o GitHub (.gitignore).

No config.yaml cada chave aparece só pelo NOME da variável (ex.: token_env: PD_MINHA_EMPRESA_SLACK_TOKEN).
O valor de verdade só existe no .env.
"""
import copy
import os
import re
from datetime import time
from pathlib import Path

import yaml
from dotenv import load_dotenv, set_key

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TOKENS = ROOT / "tokens"
ARQ_CONFIG = ROOT / "config.yaml"
ARQ_ENV = ROOT / ".env"

TIPOS = {"slack", "clickup", "gmail", "microsoft", "zoom"}

# Fusos do Brasil (IANA) -> nome usado pelo Outlook/Microsoft Graph
FUSOS = {
    "America/Sao_Paulo": "E. South America Standard Time",
    "America/Bahia": "Bahia Standard Time",
    "America/Fortaleza": "SA Eastern Standard Time",
    "America/Recife": "SA Eastern Standard Time",
    "America/Belem": "SA Eastern Standard Time",
    "America/Cuiaba": "Central Brazilian Standard Time",
    "America/Manaus": "SA Western Standard Time",
    "America/Rio_Branco": "SA Pacific Standard Time",
    "America/Noronha": "UTC-02",
}

PADRAO = {
    "demo": False,
    "usuario": {"nome": "", "fuso": "America/Sao_Paulo"},
    "clima": {"local": "São Paulo", "lat": None, "lon": None},
    "horarios": {"inicio_dia": "07:00", "fim_dia": "18:00", "expediente": ["09:00", "18:00"]},
    "notificacoes": {"discord": True, "celular": True, "ouvir_alarme": True},
    "ia": {"modelo": "claude-opus-5-5"},      # resumo dos e-mails com o Claude
    "tela": {"orientacao": "automatica", "resolucao": "1280x720", "tela_cheia": False},
    "reunioes": {"duracao_padrao": 30, "dias_para_frente": 3, "responder_no_teams": False,
                 "palavras": ["reunião", "reuniao", "call", "meet", "meeting", "conversar", "alinhar", "papo"]},
    "empresas": [],
}


class ConfigError(Exception):
    pass


def env(nome, obrigatorio=True):
    """Lê uma variável do .env com mensagem clara quando falta."""
    valor = os.getenv(nome, "").strip()
    if obrigatorio and not valor:
        raise ConfigError(f"falta a chave {nome} (preencha em Configurações > Chaves de API)")
    return valor


def existe():
    """True se o usuário já salvou as configurações alguma vez."""
    return ARQ_CONFIG.exists()


def _mesclar(base, novo):
    """Completa o que faltar em 'novo' com os valores padrão."""
    saida = copy.deepcopy(base)
    for k, v in (novo or {}).items():
        saida[k] = _mesclar(saida[k], v) if isinstance(v, dict) and isinstance(saida.get(k), dict) else v
    return saida


def carregar_bruto(caminho=None):
    """config.yaml do jeito que está no arquivo (horários como texto), já com os padrões."""
    load_dotenv(ARQ_ENV, override=True)
    caminho = Path(caminho) if caminho else ARQ_CONFIG
    dados = {}
    if caminho.exists():
        with open(caminho, encoding="utf-8") as f:
            dados = yaml.safe_load(f) or {}
    # compatibilidade com a versão antiga, que usava "cidade"
    if "cidade" in dados and "clima" not in dados:
        dados["clima"] = {"local": dados.pop("cidade")}
    return _mesclar(PADRAO, dados)


def _hora(texto, campo):
    try:
        h, m = str(texto).split(":")
        return time(int(h), int(m))
    except ValueError:
        raise ConfigError(f"horário inválido em '{campo}': {texto} (use HH:MM)") from None


def preparar(bruto, demo=False):
    """Converte o config bruto no formato usado pelo programa e valida."""
    cfg = copy.deepcopy(bruto)
    u = cfg["usuario"]
    u["nome"] = u.get("nome") or "você"
    u["fuso_windows"] = u.get("fuso_windows") or FUSOS.get(u["fuso"], "E. South America Standard Time")
    h = cfg["horarios"]
    h["inicio_dia"] = _hora(h["inicio_dia"], "início do dia")
    h["fim_dia"] = _hora(h["fim_dia"], "fim do dia")
    h["expediente"] = (_hora(h["expediente"][0], "expediente"), _hora(h["expediente"][1], "expediente"))
    for emp in cfg["empresas"]:
        if not emp.get("nome"):
            raise ConfigError("toda empresa precisa de um nome")
        emp.setdefault("cor", "#5ab0ff")
        emp.setdefault("ativa", True)            # empresa desligada = nenhum serviço dela roda
        for con in emp.setdefault("conectores", []):
            if con.get("tipo") not in TIPOS:
                raise ConfigError(f"{emp['nome']}: serviço '{con.get('tipo')}' não existe")
    cfg["demo"] = bool(demo or cfg.get("demo"))
    DATA.mkdir(exist_ok=True)
    TOKENS.mkdir(exist_ok=True)
    return cfg


def carregar(caminho=None, demo=False):
    """Atalho: lê o config.yaml + .env e devolve pronto para usar."""
    return preparar(carregar_bruto(caminho), demo)


def nome_segredo(*partes):
    """('Minha Empresa', 'slack', 'token') -> 'PD_MINHA_EMPRESA_SLACK_TOKEN'."""
    texto = "_".join(partes)
    return "PD_" + re.sub(r"[^A-Z0-9]+", "_", texto.upper()).strip("_")


def salvar(bruto, segredos):
    """Grava o config.yaml (sem segredos) e as chaves no .env.

    segredos: {NOME_DA_VARIAVEL: valor}. Valor vazio apaga a chave.
    """
    with open(ARQ_CONFIG, "w", encoding="utf-8") as f:
        f.write("# Gerado pela tela de Configurações do PixelDigest. As chaves ficam no .env.\n")
        yaml.safe_dump(bruto, f, allow_unicode=True, sort_keys=False)
    ARQ_ENV.touch(exist_ok=True)
    for nome, valor in segredos.items():
        valor = (valor or "").strip()
        set_key(str(ARQ_ENV), nome, valor, quote_mode="never")
        os.environ[nome] = valor


def cor_rgb(hexa):
    """'#3fa7ff' vira (63, 167, 255)."""
    hexa = hexa.lstrip("#")
    return tuple(int(hexa[i:i + 2], 16) for i in (0, 2, 4))
