"""Resumo dos e-mails com IA (Claude): os pontos importantes dos 10 e-mails mais recentes.

- Só chama o Claude quando a lista de e-mails muda (a "assinatura" são os IDs das
  mensagens). Se nada mudou, devolve o último resumo salvo em data/resumos-email.json.
- Sem a chave do Claude (ANTHROPIC_API_KEY), faz um resumo simples, sem IA.
- A resposta vem em JSON validado por um schema (output_config.format), então não
  precisa "adivinhar" o formato do texto.

Privacidade: o texto dos e-mails é enviado para a API da Anthropic para gerar o resumo.
"""
import hashlib
import json
from datetime import datetime

from . import net
from .config import DATA

MODELOS = [("claude-opus-5-5", "Opus 5.5 (melhor)"), ("claude-sonnet-5-5", "Sonnet 5.5"),
           ("claude-haiku-5-5", "Haiku 5.5 (mais barato)")]
CACHE = DATA / "resumos-email.json"

SCHEMA = {
    "type": "object",
    "properties": {
        "resumo": {"type": "string", "description": "uma frase com o panorama da caixa de entrada"},
        "pontos": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "titulo": {"type": "string", "description": "até 60 caracteres"},
                "detalhe": {"type": "string", "description": "até 140 caracteres"},
                "prioridade": {"type": "string", "enum": ["alta", "media", "baixa"]},
                "acao": {"type": "string", "description": "o que você precisa fazer; vazio se nada"},
            },
            "required": ["titulo", "detalhe", "prioridade", "acao"],
            "additionalProperties": False,
        }},
    },
    "required": ["resumo", "pontos"],
    "additionalProperties": False,
}

INSTRUCOES = (
    "Você lê a caixa de entrada de uma pessoa e resume o que importa, em português do Brasil.\n"
    "Regras:\n"
    "- No máximo 6 pontos, do mais importante para o menos importante.\n"
    "- Priorize pedidos diretos, prazos, clientes, pagamentos e reuniões.\n"
    "- Junte e-mails do mesmo assunto num ponto só.\n"
    "- Ignore newsletters, propagandas e notificações automáticas sem ação, a não ser que tragam algo urgente.\n"
    "- Título curto (até 60 caracteres) com quem e o quê. Detalhe com o essencial (até 140 caracteres).\n"
    "- Em 'acao', diga o que a pessoa precisa fazer (ex.: 'responder até sexta'); deixe vazio se nada.\n"
    "- Não invente nada que não esteja nos e-mails."
)


def assinatura(mensagens, modelo):
    ids = ",".join(m["id"] for m in mensagens)
    return hashlib.sha1(f"{modelo}|{ids}".encode()).hexdigest()


def _ler_cache():
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def simples(mensagens, motivo=""):
    """Resumo sem IA: remetente, assunto e o começo do texto."""
    pontos = [{"titulo": f"{m['de']}: {m['assunto']}"[:60], "detalhe": m["texto"][:140],
               "prioridade": "alta" if m.get("importante") else ("media" if m.get("nao_lido") else "baixa"),
               "acao": ""} for m in mensagens[:6]]
    resumo = f"{len(mensagens)} e-mail(s) nas últimas 24 h." + (f" ({motivo})" if motivo else "")
    return {"resumo": resumo, "pontos": pontos, "fonte": "simples"}


def chamar_claude(mensagens, chave, modelo):
    import anthropic                       # carregado só quando precisa (economiza RAM)
    textos = []
    for i, m in enumerate(mensagens, 1):
        hora = datetime.fromtimestamp(m["quando"]).strftime("%d/%m %H:%M")
        textos.append(f"[{i}] De: {m['de']} | Assunto: {m['assunto']} | Recebido: {hora}"
                      f"{' | NÃO LIDO' if m.get('nao_lido') else ''}\n{m['texto']}")
    cliente = anthropic.Anthropic(api_key=chave, timeout=60.0, max_retries=2)
    try:
        resp = cliente.messages.create(
            model=modelo,
            max_tokens=2000,
            system=[{"type": "text", "text": INSTRUCOES, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": "E-mails recebidos:\n\n" + "\n\n".join(textos)}],
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        )
    except anthropic.AuthenticationError as exc:
        raise net.ApiError("Claude", "chave recusada; confira em Configurações > Chaves de API") from exc
    except anthropic.APIError as exc:
        raise net.ApiError("Claude", f"não deu para resumir agora ({exc.__class__.__name__})") from exc
    if resp.stop_reason == "refusal":
        return simples(mensagens, "a IA não quis resumir estes e-mails")
    texto = next((b.text for b in resp.content if b.type == "text"), "{}")
    dados = json.loads(texto)
    dados["fonte"] = "ia"
    return dados


def resumir(conta, mensagens, chave="", modelo="claude-opus-5-5"):
    """Resumo da caixa 'conta'. Reaproveita o anterior se os e-mails não mudaram."""
    if not mensagens:
        return {"resumo": "Nenhum e-mail nas últimas 24 h.", "pontos": [], "fonte": "simples",
                "gerado": datetime.now().strftime("%H:%M")}
    if not chave:
        r = simples(mensagens, "coloque a chave do Claude nas Configurações para o resumo com IA")
    else:
        cache = _ler_cache()
        sig = assinatura(mensagens, modelo)
        if cache.get(conta, {}).get("assinatura") == sig:
            return cache[conta]["resultado"]               # nada mudou: sem nova chamada
        try:
            r = chamar_claude(mensagens, chave, modelo)
        except net.ApiError as exc:
            r = simples(mensagens, str(exc))
        if r.get("fonte") == "ia":
            r["gerado"] = datetime.now().strftime("%H:%M")
            cache[conta] = {"assinatura": sig, "resultado": r}
            CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            return r
    r["gerado"] = datetime.now().strftime("%H:%M")
    return r
