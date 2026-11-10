# `pixeldigest/resumo_email.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/resumo_email.py)

Resume com IA (Claude, da Anthropic) os 10 e-mails mais recentes de cada conta. Só chama a IA quando a lista de e-mails muda e, sem chave, faz um resumo simples.

### Linhas 1 a 10

```python
"""Resumo dos e-mails com IA (Claude): os pontos importantes dos 10 e-mails mais recentes.

- Só chama o Claude quando a lista de e-mails muda (a "assinatura" são os IDs das
  mensagens). Se nada mudou, devolve o último resumo salvo em data/resumos-email.json.
- Sem a chave do Claude (ANTHROPIC_API_KEY), faz um resumo simples, sem IA.
- A resposta vem em JSON validado por um schema (output_config.format), então não
  precisa "adivinhar" o formato do texto.

Privacidade: o texto dos e-mails é enviado para a API da Anthropic para gerar o resumo.
"""
```

Docstring: explica o cache por assinatura, o plano B sem chave, a resposta em JSON validado por schema e o aviso de privacidade (o texto dos e-mails vai para a API da Anthropic).

### Linha 11

```python
import hashlib
```

Importa `hashlib` para calcular a assinatura (um hash SHA-1) da lista de e-mails.

### Linha 12

```python
import json
```

Importa `json`.

### Linha 13

```python
from datetime import datetime
```

Importa `datetime`.

### Linha 15

```python
from . import net
```

Importa `net` para lançar `ApiError`.

### Linha 16

```python
from .config import DATA
```

Importa a pasta `data/`.

### Linhas 18 a 19

```python
MODELOS = [("claude-opus-5-5", "Opus 5.5 (melhor)"), ("claude-sonnet-5-5", "Sonnet 5.5"),
           ("claude-haiku-5-5", "Haiku 5.5 (mais barato)")]
```

Lista de modelos que aparecem na tela de Configurações: o identificador usado na API e o nome mostrado.

### Linha 20

```python
CACHE = DATA / "resumos-email.json"
```

Arquivo do cache dos resumos.

### Linhas 22 a 40

```python
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
```

`SCHEMA` é um JSON Schema: descreve exatamente o formato que a resposta da IA precisa ter. Um objeto com `resumo` (texto) e `pontos` (lista). Cada ponto tem `titulo`, `detalhe`, `prioridade` (só pode ser "alta", "media" ou "baixa", por causa do `enum`) e `acao`. `required` lista os campos obrigatórios e `additionalProperties: False` proíbe campos extras. Com isso a API garante um JSON válido e o programa não precisa adivinhar o formato do texto.

### Linhas 42 a 52

```python
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
```

`INSTRUCOES` é o prompt de sistema: diz à IA o papel dela e as regras (no máximo 6 pontos, o que priorizar, juntar assuntos iguais, ignorar propaganda, tamanho dos textos, o que pôr em "acao" e não inventar nada). As strings entre parênteses são juntadas numa só.

### Linha 55

```python
def assinatura(mensagens, modelo):
```

Calcula a assinatura de uma lista de e-mails.

### Linha 56

```python
    ids = ",".join(m["id"] for m in mensagens)
```

Junta os ids das mensagens separados por vírgula.

### Linha 57

```python
    return hashlib.sha1(f"{modelo}|{ids}".encode()).hexdigest()
```

Calcula o SHA-1 do texto "modelo|ids" e devolve em hexadecimal. Se os e-mails ou o modelo mudarem, a assinatura muda.

### Linhas 60 a 64

```python
def _ler_cache():
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
```

Lê o cache; se não existir ou estiver corrompido, devolve dicionário vazio.

### Linha 67

```python
def simples(mensagens, motivo=""):
```

Resumo sem IA.

### Linha 68

```python
    """Resumo sem IA: remetente, assunto e o começo do texto."""
```

Docstring.

### Linhas 69 a 71

```python
    pontos = [{"titulo": f"{m['de']}: {m['assunto']}"[:60], "detalhe": m["texto"][:140],
               "prioridade": "alta" if m.get("importante") else ("media" if m.get("nao_lido") else "baixa"),
               "acao": ""} for m in mensagens[:6]]
```

Para os 6 primeiros e-mails, monta um ponto com "remetente: assunto" (até 60 caracteres), o começo do texto (até 140) e a prioridade: alta se o Gmail marcou como importante, média se não foi lido, baixa no resto.

### Linha 72

```python
    resumo = f"{len(mensagens)} e-mail(s) nas últimas 24 h." + (f" ({motivo})" if motivo else "")
```

Frase de resumo com a quantidade e, se houver, o motivo de não ter usado a IA.

### Linha 73

```python
    return {"resumo": resumo, "pontos": pontos, "fonte": "simples"}
```

Devolve no mesmo formato do resumo com IA, marcando a fonte como "simples".

### Linha 76

```python
def chamar_claude(mensagens, chave, modelo):
```

Chama o Claude.

### Linha 77

```python
    import anthropic                       # carregado só quando precisa (economiza RAM)
```

Importa o SDK oficial `anthropic` só aqui dentro. O comentário explica: a biblioteca é grande e só é carregada se for usada, economizando memória.

### Linhas 78 a 82

```python
    textos = []
    for i, m in enumerate(mensagens, 1):
        hora = datetime.fromtimestamp(m["quando"]).strftime("%d/%m %H:%M")
        textos.append(f"[{i}] De: {m['de']} | Assunto: {m['assunto']} | Recebido: {hora}"
                      f"{' | NÃO LIDO' if m.get('nao_lido') else ''}\n{m['texto']}")
```

Monta o texto de cada e-mail numerado: remetente, assunto, data (convertida de timestamp Unix para "dd/mm HH:MM"), uma marca se não foi lido e o corpo. `enumerate(mensagens, 1)` numera a partir de 1.

### Linha 83

```python
    cliente = anthropic.Anthropic(api_key=chave, timeout=60.0, max_retries=2)
```

Cria o cliente da API com a chave, tempo limite de 60 segundos e até 2 novas tentativas automáticas.

### Linhas 84 a 91

```python
    try:
        resp = cliente.messages.create(
            model=modelo,
            max_tokens=2000,
            system=[{"type": "text", "text": INSTRUCOES, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": "E-mails recebidos:\n\n" + "\n\n".join(textos)}],
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        )
```

Faz a chamada `messages.create`:
- `model`: o modelo escolhido nas Configurações.
- `max_tokens=2000`: limite do tamanho da resposta.
- `system`: as instruções. O `cache_control` "ephemeral" pede para a API guardar esse trecho em cache, deixando as próximas chamadas mais baratas e rápidas.
- `messages`: a mensagem do usuário com todos os e-mails.
- `output_config`: `effort: low` pede uma resposta direta, sem gastar raciocínio à toa (é uma tarefa simples), e `format` obriga a resposta a seguir o `SCHEMA`.

### Linhas 92 a 93

```python
    except anthropic.AuthenticationError as exc:
        raise net.ApiError("Claude", "chave recusada; confira em Configurações > Chaves de API") from exc
```

Chave inválida: transforma no nosso `ApiError` com uma mensagem que diz onde corrigir. O `from exc` mantém o erro original encadeado, útil no log.

### Linhas 94 a 95

```python
    except anthropic.APIError as exc:
        raise net.ApiError("Claude", f"não deu para resumir agora ({exc.__class__.__name__})") from exc
```

Outros erros da API (limite, servidor fora): `ApiError` com o nome do tipo de erro.

### Linhas 96 a 97

```python
    if resp.stop_reason == "refusal":
        return simples(mensagens, "a IA não quis resumir estes e-mails")
```

Se a IA se recusou a responder (`stop_reason == "refusal"`), usa o resumo simples.

### Linha 98

```python
    texto = next((b.text for b in resp.content if b.type == "text"), "{}")
```

A resposta vem em blocos; `next(...)` pega o texto do primeiro bloco do tipo "text" (ou "{}" se não houver nenhum).

### Linha 99

```python
    dados = json.loads(texto)
```

Converte o JSON para dicionário.

### Linhas 100 a 101

```python
    dados["fonte"] = "ia"
    return dados
```

Marca a fonte como "ia" e devolve.

### Linha 104

```python
def resumir(conta, mensagens, chave="", modelo="claude-opus-5-5"):
```

Função principal: resume a caixa de uma conta.

### Linha 105

```python
    """Resumo da caixa 'conta'. Reaproveita o anterior se os e-mails não mudaram."""
```

Docstring.

### Linhas 106 a 108

```python
    if not mensagens:
        return {"resumo": "Nenhum e-mail nas últimas 24 h.", "pontos": [], "fonte": "simples",
                "gerado": datetime.now().strftime("%H:%M")}
```

Sem e-mails: devolve um resumo vazio com a hora em que foi gerado.

### Linhas 109 a 110

```python
    if not chave:
        r = simples(mensagens, "coloque a chave do Claude nas Configurações para o resumo com IA")
```

Sem chave do Claude: resumo simples explicando como ligar a IA.

### Linhas 111 a 113

```python
    else:
        cache = _ler_cache()
        sig = assinatura(mensagens, modelo)
```

Com chave: lê o cache e calcula a assinatura atual.

### Linhas 114 a 115

```python
        if cache.get(conta, {}).get("assinatura") == sig:
            return cache[conta]["resultado"]               # nada mudou: sem nova chamada
```

Se a assinatura salva para essa conta é igual à atual, os e-mails não mudaram: devolve o resumo guardado sem chamar a API. `cache.get(conta, {})` evita erro se a conta ainda não estiver no cache.

### Linhas 116 a 119

```python
        try:
            r = chamar_claude(mensagens, chave, modelo)
        except net.ApiError as exc:
            r = simples(mensagens, str(exc))
```

Chama o Claude; se falhar, usa o resumo simples com a mensagem do erro.

### Linhas 120 a 124

```python
        if r.get("fonte") == "ia":
            r["gerado"] = datetime.now().strftime("%H:%M")
            cache[conta] = {"assinatura": sig, "resultado": r}
            CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            return r
```

Se veio da IA: anota a hora, guarda no cache com a assinatura, grava o arquivo e devolve.

### Linhas 125 a 126

```python
    r["gerado"] = datetime.now().strftime("%H:%M")
    return r
```

Para os resumos simples (que não vão para o cache), anota a hora e devolve.
