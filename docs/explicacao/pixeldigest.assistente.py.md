# `pixeldigest/assistente.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/assistente.py)

Funções chamadas pelos botões da tela de Configurações: buscar endereço, descobrir localização, testar Discord e ntfy, conectar Slack e ClickUp, testar a chave do Claude e cada serviço, e ligar o início junto com o Windows.

### Linhas 1 a 6

```python
"""Funções usadas pelos botões da tela de Configurações.

Cada uma faz uma chamada de rede curta e devolve um resultado simples (ou levanta
net.ApiError com uma mensagem para mostrar na tela). A tela roda tudo isso em
segundo plano para não travar.
"""
```

Docstring: cada função faz uma chamada curta e devolve um resultado simples ou lança `ApiError` com uma mensagem para a tela. A tela roda tudo em segundo plano.

### Linha 7

```python
import os
```

Importa `os` para ler a variável `APPDATA` do Windows.

### Linha 8

```python
import secrets
```

Importa `secrets`, que gera números aleatórios seguros (próprios para senhas).

### Linha 9

```python
import sys
```

Importa `sys` para saber o sistema e o caminho do Python.

### Linha 10

```python
from pathlib import Path
```

Importa `Path`.

### Linha 12

```python
from . import net
```

Importa `net`.

### Linha 13

```python
from .config import ROOT
```

Importa a raiz do projeto.

### Linha 15

```python
UA = {"User-Agent": "PixelDigest/1.0 (projeto academico de automacao)"}
```

Cabeçalho `User-Agent` que identifica o programa. O Nominatim (OpenStreetMap) exige que todo cliente se identifique; sem isso ele bloqueia.

### Linha 18

```python
# ---------- clima: endereço -> coordenadas ----------
```

Comentário da parte do clima.

### Linha 19

```python
def buscar_endereco(texto):
```

Busca um endereço e devolve uma lista de lugares com coordenadas.

### Linhas 20 a 24

```python
    """'Av. Paulista, 1000' -> lista de {local, lat, lon}.

    Usa o Nominatim (OpenStreetMap), que entende endereço completo, bairro ou cidade.
    Se ele falhar, tenta o geocoding do Open-Meteo (só cidades).
    """
```

Docstring: usa o Nominatim, que entende endereço completo, bairro ou cidade; se falhar, usa o geocoding do Open-Meteo, que só entende cidades.

### Linhas 25 a 27

```python
    texto = texto.strip()
    if not texto:
        raise net.ApiError("Busca", "digite um endereço, bairro ou cidade")
```

Tira espaços; se ficou vazio, pede para digitar algo.

### Linhas 28 a 29

```python
    try:
        from .connectors.weather import lugar_curto
```

Importa a função que monta o nome curto do lugar (ex.: "Centro, Pelotas").

### Linhas 30 a 31

```python
        dados = net.get_json("OpenStreetMap", "https://nominatim.openstreetmap.org/search", headers=UA, params={
            "q": texto, "format": "jsonv2", "limit": 5, "accept-language": "pt-BR", "addressdetails": 1})
```

Chama a busca do Nominatim: texto, formato JSON, até 5 resultados, nomes em português e com o endereço detalhado (`addressdetails`).

### Linhas 32 a 33

```python
        achados = [{"local": d["display_name"], "cidade": lugar_curto(d.get("address", {})),
                    "lat": round(float(d["lat"]), 4), "lon": round(float(d["lon"]), 4)} for d in dados]
```

Para cada resultado, monta um dicionário com o nome completo, o nome curto, e latitude e longitude convertidas para número e arredondadas em 4 casas (cerca de 10 metros de precisão).

### Linhas 34 a 35

```python
    except net.ApiError:
        achados = []
```

Se o Nominatim falhar, segue com a lista vazia.

### Linhas 36 a 38

```python
    if not achados:
        dados = net.get_json("Open-Meteo", "https://geocoding-api.open-meteo.com/v1/search",
                             params={"name": texto, "count": 5, "language": "pt", "format": "json"})
```

Se não achou nada, tenta o geocoding do Open-Meteo.

### Linhas 39 a 41

```python
        achados = [{"local": ", ".join(x for x in (r.get("name"), r.get("admin1"), r.get("country")) if x),
                    "lat": r["latitude"], "lon": r["longitude"], "fuso": r.get("timezone")}
                   for r in dados.get("results") or []]
```

Monta os resultados juntando nome, estado e país (pulando os que vierem vazios) e guarda também o fuso. `dados.get("results") or []` cobre o caso de não vir a chave.

### Linhas 42 a 43

```python
    if not achados:
        raise net.ApiError("Busca", f"não achei '{texto}'. Tente só o bairro e a cidade")
```

Se nenhum dos dois achou, sugere digitar só bairro e cidade.

### Linha 44

```python
    return achados
```

Devolve os lugares.

### Linha 47

```python
def minha_localizacao():
```

Localização aproximada pelo IP.

### Linha 48

```python
    """Localização aproximada pela internet (cidade do seu provedor)."""
```

Docstring: dá a cidade do provedor de internet.

### Linha 49

```python
    d = net.get_json("Localização", "https://ipwho.is/", headers=UA)
```

Chama o serviço gratuito `ipwho.is`.

### Linhas 50 a 51

```python
    if not d.get("success", True):
        raise net.ApiError("Localização", d.get("message", "não deu para descobrir"))
```

Se o serviço disser que falhou, lança erro com a mensagem dele.

### Linha 52

```python
    local = ", ".join(x for x in (d.get("city"), d.get("region"), d.get("country")) if x)
```

Junta cidade, estado e país.

### Linhas 53 a 54

```python
    return {"local": local, "cidade": d.get("city") or local, "lat": d["latitude"], "lon": d["longitude"],
            "fuso": (d.get("timezone") or {}).get("id")}
```

Devolve local, cidade, coordenadas e o fuso (o fuso vem dentro de outro objeto; o `or {}` evita erro se vier vazio).

### Linhas 57 a 61

```python
def fuso_do_local(lat, lon):
    """Pergunta ao Open-Meteo qual é o fuso horário daquelas coordenadas."""
    d = net.get_json("Open-Meteo", "https://api.open-meteo.com/v1/forecast",
                     params={"latitude": lat, "longitude": lon, "timezone": "auto", "current": "temperature_2m"})
    return d.get("timezone")
```

Pergunta ao Open-Meteo o fuso horário de umas coordenadas: com `timezone=auto`, a resposta traz o fuso do lugar.

### Linha 64

```python
# ---------- notificações ----------
```

Comentário das notificações.

### Linhas 65 a 67

```python
def novo_topico(prefixo="pixeldigest"):
    """Nome de tópico do ntfy difícil de adivinhar (funciona como senha)."""
    return f"{prefixo}-{secrets.token_hex(5)}"
```

Gera um nome de tópico do ntfy difícil de adivinhar, como "pixeldigest-a3f91c0b2e". No ntfy público, quem sabe o nome do tópico lê as mensagens, então o nome funciona como senha. `token_hex(5)` gera 10 caracteres hexadecimais aleatórios.

### Linha 70

```python
def testar_discord(url):
```

Testa o webhook do Discord.

### Linhas 71 a 72

```python
    if not url.startswith("https://discord.com/api/webhooks/") and not url.startswith("https://discordapp.com/api/webhooks/"):
        raise net.ApiError("Discord", "a URL do webhook começa com https://discord.com/api/webhooks/")
```

Confere se a URL tem o começo de um webhook do Discord.

### Linhas 73 a 74

```python
    net.request("Discord", "POST", url, json={"username": "PixelDigest", "embeds": [{
        "title": "🧪 Teste do PixelDigest", "description": "O Discord está conectado!", "color": 0xFFCC4D}]})
```

Manda uma mensagem de teste com um embed amarelo (`0xFFCC4D` é a cor em hexadecimal escrita como número).

### Linha 75

```python
    return "mensagem enviada! Confira o canal"
```

Mensagem de sucesso.

### Linha 78

```python
def testar_ntfy(servidor, topico, token="", titulo="🧪 Teste do PixelDigest", texto="O celular está conectado!"):
```

Testa o ntfy.

### Linhas 79 a 80

```python
    if not topico:
        raise net.ApiError("ntfy", "gere ou digite um tópico primeiro")
```

Precisa de um tópico.

### Linha 81

```python
    headers = {"Authorization": f"Bearer {token}"} if token else {}
```

Cabeçalho de autenticação, se houver token.

### Linhas 82 a 83

```python
    net.request("ntfy", "POST", (servidor or "https://ntfy.sh").rstrip("/"), headers=headers,
                json={"topic": topico, "title": titulo, "message": texto, "tags": ["tada"]})
```

Manda a notificação de teste.

### Linha 84

```python
    return "enviado! Confira o celular"
```

Mensagem de sucesso.

### Linhas 87 a 89

```python
def endereco_alarme(servidor, topico):
    """Endereço para o MacroDroid. Funciona com GET ou POST e já leva título e mensagem."""
    return f"{(servidor or 'https://ntfy.sh').rstrip('/')}/{topico}/publish?title=Alarme&message=Hora%20de%20acordar"
```

Monta o endereço que vai no MacroDroid. O `/publish` do ntfy aceita GET ou POST e recebe título e mensagem na própria URL (`%20` é o espaço codificado).

### Linha 92

```python
def ultimas_mensagens(servidor, topico, token=""):
```

Lê o que chegou no tópico do alarme nas últimas 24 horas, para conferir se o celular está publicando.

### Linha 93

```python
    """O que chegou no tópico do alarme nas últimas 24 h (para conferir se o celular está acertando)."""
```

Docstring.

### Linhas 94 a 95

```python
    import json
    from datetime import datetime
```

Imports usados só nesta função.

### Linhas 96 a 97

```python
    if not topico:
        raise net.ApiError("ntfy", "gere o tópico do alarme primeiro")
```

Precisa do tópico.

### Linha 98

```python
    headers = {"Authorization": f"Bearer {token}"} if token else {}
```

Cabeçalho de autenticação, se houver.

### Linhas 99 a 100

```python
    r = net.request("ntfy", "GET", f"{(servidor or 'https://ntfy.sh').rstrip('/')}/{topico}/json",
                    headers=headers, params={"poll": "1", "since": "24h"})
```

Pede ao ntfy as mensagens guardadas: `poll=1` devolve o que já existe e encerra (sem ficar conectado), e `since=24h` limita às últimas 24 horas.

### Linha 101

```python
    msgs = [json.loads(linha) for linha in r.text.splitlines() if linha.strip()]
```

Cada linha da resposta é um JSON; converte as linhas não vazias.

### Linha 102

```python
    msgs = [m for m in msgs if m.get("event") == "message"]
```

Mantém só os eventos de mensagem.

### Linhas 103 a 104

```python
    if not msgs:
        return "Nada chegou do celular nas últimas 24 h. Confira o endereço no MacroDroid (use o QR code)."
```

Se nada chegou, explica o que conferir.

### Linha 105

```python
    ultimas = [f"{datetime.fromtimestamp(m['time']):%d/%m %H:%M} \"{m.get('message', '')[:40]}\"" for m in msgs[-4:]]
```

Formata as quatro últimas com data, hora e o começo do texto.

### Linha 106

```python
    return f"{len(msgs)} mensagem(ns) em 24 h. Últimas: " + " · ".join(ultimas)
```

Devolve quantas chegaram e as últimas, separadas por um ponto.

### Linha 109

```python
# ---------- Slack e ClickUp: descobrir canais e workspaces a partir do token ----------
```

Comentário: descobrir canais e workspaces a partir do token.

### Linha 110

```python
def slack_conectar(token):
```

Conecta no Slack e lista os canais.

### Linhas 111 a 115

```python
    """Valida o token e lista os canais. Devolve (descrição, [(id, nome)], meu_id).

    Token de usuário (xoxp): lista os canais de que VOCÊ participa, inclusive privados.
    Token de bot (xoxb): lista os canais públicos e avisa que privados e DMs não aparecem.
    """
```

Docstring: diferença entre o token de usuário (xoxp, vê tudo o que você vê, inclusive privados) e o de bot (xoxb, só canais públicos e onde foi convidado).

### Linhas 116 a 117

```python
    if not token.startswith(("xoxb-", "xoxp-")):
        raise net.ApiError("Slack", "o token começa com xoxp- (usuário, recomendado) ou xoxb- (bot)")
```

Confere o começo do token. `startswith` aceita uma tupla de opções.

### Linha 118

```python
    h = {"Authorization": f"Bearer {token}"}
```

Cabeçalho com o token.

### Linha 119

```python
    eu = net.get_json("Slack", "https://slack.com/api/auth.test", headers=h)
```

`auth.test` confere se o token é válido e devolve o usuário e o workspace.

### Linhas 120 a 121

```python
    if not eu.get("ok"):
        raise net.ApiError("Slack", f"token recusado ({eu.get('error')})")
```

A API do Slack responde HTTP 200 mesmo em erro, com `ok: false`. Por isso conferimos o `ok`.

### Linha 122

```python
    usuario = token.startswith("xoxp-")
```

É token de usuário?

### Linha 123

```python
    metodo = "users.conversations" if usuario else "conversations.list"
```

Escolhe o método: `users.conversations` (canais de que você participa) para usuário, `conversations.list` (todos os públicos) para bot.

### Linha 124

```python
    canais, cursor = [], None
```

Lista de canais e o cursor da paginação.

### Linha 125

```python
    for _ in range(60):                     # o Slack devolve a lista em páginas
```

Até 60 páginas. O comentário explica: o Slack devolve a lista em páginas.

### Linha 126

```python
        params = {"types": "public_channel,private_channel", "exclude_archived": "true", "limit": 200}
```

Parâmetros: canais públicos e privados, sem os arquivados, até 200 por página.

### Linhas 127 a 128

```python
        if cursor:
            params["cursor"] = cursor
```

Se há cursor, pede a próxima página.

### Linha 129

```python
        d = net.get_json("Slack", "https://slack.com/api/" + metodo, headers=h, params=params)
```

Faz a chamada.

### Linhas 130 a 131

```python
        if not d.get("ok"):
            raise net.ApiError("Slack", f"não deu para listar canais ({d.get('error')}). Faltam escopos no app?")
```

Se não deu certo, provavelmente faltam permissões (escopos) no app do Slack.

### Linha 132

```python
        canais += d.get("channels", [])
```

Acrescenta os canais desta página.

### Linha 133

```python
        cursor = (d.get("response_metadata") or {}).get("next_cursor")
```

Pega o cursor da próxima página, que vem dentro de `response_metadata`.

### Linhas 134 a 135

```python
        if not cursor:
            break
```

Sem cursor, acabaram as páginas.

### Linha 136

```python
    lista = sorted(((c["id"], c["name"] + (" (privado)" if c.get("is_private") else "")) for c in canais), key=lambda c: c[1])
```

Monta a lista (id, nome) com "(privado)" nos canais privados e ordena pelo nome.

### Linhas 137 a 141

```python
    if usuario:
        texto = f"conectado como você no workspace {eu.get('team')} ({len(lista)} canais seus, inclusive privados)"
    else:
        texto = (f"conectado como bot no workspace {eu.get('team')}. Atenção: bot não vê canais privados nem DMs "
                 f"e só lê canais para onde foi convidado. Use o token de usuário (xoxp-)")
```

Texto explicativo: para usuário, quantos canais; para bot, o aviso das limitações.

### Linha 142

```python
    return texto, lista, (eu.get("user_id") if usuario else "")
```

Devolve o texto, a lista e o id do usuário (o programa usa para saber o que é menção a você).

### Linha 145

```python
def clickup_workspaces(token):
```

Valida o token do ClickUp e lista os workspaces.

### Linha 146

```python
    """Valida o token e lista os workspaces. Devolve [(id, nome)]."""
```

Docstring.

### Linhas 147 a 148

```python
    if not token.startswith("pk_"):
        raise net.ApiError("ClickUp", "o token pessoal começa com pk_")
```

O token pessoal do ClickUp começa com "pk_".

### Linha 149

```python
    d = net.get_json("ClickUp", "https://api.clickup.com/api/v2/team", headers={"Authorization": token})
```

Chama a API (o ClickUp usa o token direto no cabeçalho, sem a palavra Bearer).

### Linha 150

```python
    return [(str(t["id"]), t["name"]) for t in d.get("teams", [])]
```

Devolve a lista de (id, nome) dos workspaces.

### Linha 153

```python
def testar_claude(chave, modelo):
```

Confere a chave do Claude.

### Linha 154

```python
    """Chamada mínima para conferir a chave do Claude."""
```

Docstring.

### Linhas 155 a 156

```python
    if not chave.startswith("sk-ant-"):
        raise net.ApiError("Claude", "a chave começa com sk-ant-")
```

A chave começa com "sk-ant-".

### Linha 157

```python
    import anthropic
```

Importa o SDK.

### Linhas 158 a 160

```python
    try:
        anthropic.Anthropic(api_key=chave, timeout=30.0, max_retries=1).messages.create(
            model=modelo, max_tokens=16, messages=[{"role": "user", "content": "Responda só: ok"}])
```

Faz a menor chamada possível (16 tokens de resposta) só para ver se a chave funciona.

### Linhas 161 a 164

```python
    except anthropic.AuthenticationError as exc:
        raise net.ApiError("Claude", "chave recusada") from exc
    except anthropic.APIError as exc:
        raise net.ApiError("Claude", f"não respondeu ({exc.__class__.__name__})") from exc
```

Transforma os erros do SDK em `ApiError` com mensagens claras.

### Linha 165

```python
    return "funcionando! O resumo dos e-mails vai usar a IA"
```

Mensagem de sucesso.

### Linha 168

```python
def testar_servico(tipo, empresa, opcoes, cfg):
```

Testa um serviço de verdade com as opções que estão na tela.

### Linha 169

```python
    """Cria o conector com as opções da tela e tenta coletar de verdade."""
```

Docstring.

### Linha 170

```python
    from .connectors import TIPOS
```

Importa o dicionário de tipos de conector (tipo para classe).

### Linha 171

```python
    con = TIPOS[tipo](empresa, opcoes, cfg)
```

Cria o conector do tipo escolhido.

### Linhas 172 a 173

```python
    if con.precisa_login():
        raise net.ApiError(tipo, "falta fazer o login (botão Fazer login)")
```

Se ainda falta o login OAuth, avisa.

### Linha 174

```python
    itens = con.coletar()
```

Coleta de verdade.

### Linha 175

```python
    texto = f"funcionando! {len(itens)} itens encontrados agora"
```

Mensagem com quantos itens vieram.

### Linhas 176 a 178

```python
    avisos = getattr(con, "avisos", [])
    if avisos:
        texto += f". {len(avisos)} conversa(s) pulada(s): " + "; ".join(avisos[:3])
```

Se o conector anotou avisos (ex.: canais que não deu para ler), mostra até três.

### Linha 179

```python
    return texto
```

Devolve o texto.

### Linha 182

```python
# ---------- iniciar com o Windows ----------
```

Comentário: iniciar com o Windows.

### Linhas 183 a 185

```python
def _atalho_inicializar():
    pasta = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    return pasta / "PixelDigest.vbs"
```

Caminho do arquivo na pasta Inicializar do Windows (tudo o que está nela abre quando o usuário entra no Windows).

### Linhas 188 a 189

```python
def inicia_com_windows():
    return sys.platform == "win32" and _atalho_inicializar().exists()
```

Diz se o início automático está ligado: só no Windows e se o arquivo existir.

### Linha 192

```python
def definir_inicio_com_windows(ligar):
```

Liga ou desliga o início automático.

### Linha 193

```python
    """Cria (ou apaga) um atalho na pasta Inicializar que abre o PixelDigest sem janela preta."""
```

Docstring: cria um script que abre o programa sem a janela preta do terminal.

### Linhas 194 a 195

```python
    if sys.platform != "win32":
        return
```

Fora do Windows não faz nada.

### Linha 196

```python
    atalho = _atalho_inicializar()
```

Caminho do arquivo.

### Linhas 197 a 199

```python
    if not ligar:
        atalho.unlink(missing_ok=True)
        return
```

Para desligar, apaga o arquivo (`missing_ok=True` não reclama se ele já não existir).

### Linha 200

```python
    pythonw = Path(sys.executable).with_name("pythonw.exe")
```

Caminho do `pythonw.exe`, a versão do Python que roda sem abrir terminal. Fica na mesma pasta do Python atual.

### Linhas 201 a 204

```python
    atalho.write_text(
        'Set s = CreateObject("WScript.Shell")\r\n'
        f's.CurrentDirectory = "{ROOT}"\r\n'
        f's.Run """{pythonw}"" -m pixeldigest", 0, False\r\n', encoding="utf-8")
```

Grava um script VBScript de três linhas: cria o objeto de shell do Windows, entra na pasta do projeto e roda `pythonw -m pixeldigest`. O `0` esconde a janela e o `False` não espera terminar. As aspas triplas são o jeito do VBScript de pôr aspas dentro de texto (para caminhos com espaço). `\r\n` é a quebra de linha do Windows.
