"""Funções usadas pelos botões da tela de Configurações.

Cada uma faz uma chamada de rede curta e devolve um resultado simples (ou levanta
net.ApiError com uma mensagem para mostrar na tela). A tela roda tudo isso em
segundo plano para não travar.
"""
import os
import secrets
import sys
from pathlib import Path

from . import net
from .config import ROOT

UA = {"User-Agent": "PixelDigest/1.0 (projeto academico de automacao)"}


# ---------- clima: endereço -> coordenadas ----------
def buscar_endereco(texto):
    """'Av. Paulista, 1000' -> lista de {local, lat, lon}.

    Usa o Nominatim (OpenStreetMap), que entende endereço completo, bairro ou cidade.
    Se ele falhar, tenta o geocoding do Open-Meteo (só cidades).
    """
    texto = texto.strip()
    if not texto:
        raise net.ApiError("Busca", "digite um endereço, bairro ou cidade")
    try:
        from .connectors.weather import lugar_curto
        dados = net.get_json("OpenStreetMap", "https://nominatim.openstreetmap.org/search", headers=UA, params={
            "q": texto, "format": "jsonv2", "limit": 5, "accept-language": "pt-BR", "addressdetails": 1})
        achados = [{"local": d["display_name"], "cidade": lugar_curto(d.get("address", {})),
                    "lat": round(float(d["lat"]), 4), "lon": round(float(d["lon"]), 4)} for d in dados]
    except net.ApiError:
        achados = []
    if not achados:
        dados = net.get_json("Open-Meteo", "https://geocoding-api.open-meteo.com/v1/search",
                             params={"name": texto, "count": 5, "language": "pt", "format": "json"})
        achados = [{"local": ", ".join(x for x in (r.get("name"), r.get("admin1"), r.get("country")) if x),
                    "lat": r["latitude"], "lon": r["longitude"], "fuso": r.get("timezone")}
                   for r in dados.get("results") or []]
    if not achados:
        raise net.ApiError("Busca", f"não achei '{texto}'. Tente só o bairro e a cidade")
    return achados


def minha_localizacao():
    """Localização aproximada pela internet (cidade do seu provedor)."""
    d = net.get_json("Localização", "https://ipwho.is/", headers=UA)
    if not d.get("success", True):
        raise net.ApiError("Localização", d.get("message", "não deu para descobrir"))
    local = ", ".join(x for x in (d.get("city"), d.get("region"), d.get("country")) if x)
    return {"local": local, "cidade": d.get("city") or local, "lat": d["latitude"], "lon": d["longitude"],
            "fuso": (d.get("timezone") or {}).get("id")}


def fuso_do_local(lat, lon):
    """Pergunta ao Open-Meteo qual é o fuso horário daquelas coordenadas."""
    d = net.get_json("Open-Meteo", "https://api.open-meteo.com/v1/forecast",
                     params={"latitude": lat, "longitude": lon, "timezone": "auto", "current": "temperature_2m"})
    return d.get("timezone")


# ---------- notificações ----------
def novo_topico(prefixo="pixeldigest"):
    """Nome de tópico do ntfy difícil de adivinhar (funciona como senha)."""
    return f"{prefixo}-{secrets.token_hex(5)}"


def testar_discord(url):
    if not url.startswith("https://discord.com/api/webhooks/") and not url.startswith("https://discordapp.com/api/webhooks/"):
        raise net.ApiError("Discord", "a URL do webhook começa com https://discord.com/api/webhooks/")
    net.request("Discord", "POST", url, json={"username": "PixelDigest", "embeds": [{
        "title": "🧪 Teste do PixelDigest", "description": "O Discord está conectado!", "color": 0xFFCC4D}]})
    return "mensagem enviada! Confira o canal"


def testar_ntfy(servidor, topico, token="", titulo="🧪 Teste do PixelDigest", texto="O celular está conectado!"):
    if not topico:
        raise net.ApiError("ntfy", "gere ou digite um tópico primeiro")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    net.request("ntfy", "POST", (servidor or "https://ntfy.sh").rstrip("/"), headers=headers,
                json={"topic": topico, "title": titulo, "message": texto, "tags": ["tada"]})
    return "enviado! Confira o celular"


def endereco_alarme(servidor, topico):
    """Endereço para o MacroDroid. Funciona com GET ou POST e já leva título e mensagem."""
    return f"{(servidor or 'https://ntfy.sh').rstrip('/')}/{topico}/publish?title=Alarme&message=Hora%20de%20acordar"


def ultimas_mensagens(servidor, topico, token=""):
    """O que chegou no tópico do alarme nas últimas 24 h (para conferir se o celular está acertando)."""
    import json
    from datetime import datetime
    if not topico:
        raise net.ApiError("ntfy", "gere o tópico do alarme primeiro")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = net.request("ntfy", "GET", f"{(servidor or 'https://ntfy.sh').rstrip('/')}/{topico}/json",
                    headers=headers, params={"poll": "1", "since": "24h"})
    msgs = [json.loads(linha) for linha in r.text.splitlines() if linha.strip()]
    msgs = [m for m in msgs if m.get("event") == "message"]
    if not msgs:
        return "Nada chegou do celular nas últimas 24 h. Confira o endereço no MacroDroid (use o QR code)."
    ultimas = [f"{datetime.fromtimestamp(m['time']):%d/%m %H:%M} \"{m.get('message', '')[:40]}\"" for m in msgs[-4:]]
    return f"{len(msgs)} mensagem(ns) em 24 h. Últimas: " + " · ".join(ultimas)


# ---------- Slack e ClickUp: descobrir canais e workspaces a partir do token ----------
def slack_conectar(token):
    """Valida o token e lista os canais. Devolve (descrição, [(id, nome)], meu_id).

    Token de usuário (xoxp): lista os canais de que VOCÊ participa, inclusive privados.
    Token de bot (xoxb): lista os canais públicos e avisa que privados e DMs não aparecem.
    """
    if not token.startswith(("xoxb-", "xoxp-")):
        raise net.ApiError("Slack", "o token começa com xoxp- (usuário, recomendado) ou xoxb- (bot)")
    h = {"Authorization": f"Bearer {token}"}
    eu = net.get_json("Slack", "https://slack.com/api/auth.test", headers=h)
    if not eu.get("ok"):
        raise net.ApiError("Slack", f"token recusado ({eu.get('error')})")
    usuario = token.startswith("xoxp-")
    metodo = "users.conversations" if usuario else "conversations.list"
    canais, cursor = [], None
    for _ in range(60):                     # o Slack devolve a lista em páginas
        params = {"types": "public_channel,private_channel", "exclude_archived": "true", "limit": 200}
        if cursor:
            params["cursor"] = cursor
        d = net.get_json("Slack", "https://slack.com/api/" + metodo, headers=h, params=params)
        if not d.get("ok"):
            raise net.ApiError("Slack", f"não deu para listar canais ({d.get('error')}). Faltam escopos no app?")
        canais += d.get("channels", [])
        cursor = (d.get("response_metadata") or {}).get("next_cursor")
        if not cursor:
            break
    lista = sorted(((c["id"], c["name"] + (" (privado)" if c.get("is_private") else "")) for c in canais), key=lambda c: c[1])
    if usuario:
        texto = f"conectado como você no workspace {eu.get('team')} ({len(lista)} canais seus, inclusive privados)"
    else:
        texto = (f"conectado como bot no workspace {eu.get('team')}. Atenção: bot não vê canais privados nem DMs "
                 f"e só lê canais para onde foi convidado. Use o token de usuário (xoxp-)")
    return texto, lista, (eu.get("user_id") if usuario else "")


def clickup_workspaces(token):
    """Valida o token e lista os workspaces. Devolve [(id, nome)]."""
    if not token.startswith("pk_"):
        raise net.ApiError("ClickUp", "o token pessoal começa com pk_")
    d = net.get_json("ClickUp", "https://api.clickup.com/api/v2/team", headers={"Authorization": token})
    return [(str(t["id"]), t["name"]) for t in d.get("teams", [])]


def testar_claude(chave, modelo):
    """Chamada mínima para conferir a chave do Claude."""
    if not chave.startswith("sk-ant-"):
        raise net.ApiError("Claude", "a chave começa com sk-ant-")
    import anthropic
    try:
        anthropic.Anthropic(api_key=chave, timeout=30.0, max_retries=1).messages.create(
            model=modelo, max_tokens=16, messages=[{"role": "user", "content": "Responda só: ok"}])
    except anthropic.AuthenticationError as exc:
        raise net.ApiError("Claude", "chave recusada") from exc
    except anthropic.APIError as exc:
        raise net.ApiError("Claude", f"não respondeu ({exc.__class__.__name__})") from exc
    return "funcionando! O resumo dos e-mails vai usar a IA"


def testar_servico(tipo, empresa, opcoes, cfg):
    """Cria o conector com as opções da tela e tenta coletar de verdade."""
    from .connectors import TIPOS
    con = TIPOS[tipo](empresa, opcoes, cfg)
    if con.precisa_login():
        raise net.ApiError(tipo, "falta fazer o login (botão Fazer login)")
    itens = con.coletar()
    texto = f"funcionando! {len(itens)} itens encontrados agora"
    avisos = getattr(con, "avisos", [])
    if avisos:
        texto += f". {len(avisos)} conversa(s) pulada(s): " + "; ".join(avisos[:3])
    return texto


# ---------- iniciar com o Windows ----------
def _atalho_inicializar():
    pasta = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    return pasta / "PixelDigest.vbs"


def inicia_com_windows():
    return sys.platform == "win32" and _atalho_inicializar().exists()


def definir_inicio_com_windows(ligar):
    """Cria (ou apaga) um atalho na pasta Inicializar que abre o PixelDigest sem janela preta."""
    if sys.platform != "win32":
        return
    atalho = _atalho_inicializar()
    if not ligar:
        atalho.unlink(missing_ok=True)
        return
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    atalho.write_text(
        'Set s = CreateObject("WScript.Shell")\r\n'
        f's.CurrentDirectory = "{ROOT}"\r\n'
        f's.Run """{pythonw}"" -m pixeldigest", 0, False\r\n', encoding="utf-8")
