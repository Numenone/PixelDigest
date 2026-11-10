# `pixeldigest/connectors/slack.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/connectors/slack.py)

Conector do Slack: busca as mensagens das últimas 24 horas nos canais escolhidos, nas DMs e nos grupos, marcando como urgente quando alguém menciona você.

### Linhas 1 a 14

```python
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
```

Docstring: explica a diferença entre token de usuário (xoxp, recomendado, lê como você e vê canais privados e DMs) e de bot (xoxb, limitado), os escopos necessários, a paginação por cursor e a particularidade de o Slack responder HTTP 200 mesmo em erro, com `"ok": false`.

### Linha 15

```python
import re
```

Importa `re` para limpar o texto das mensagens e detectar palavras urgentes.

### Linha 16

```python
from datetime import datetime, timedelta
```

Importa `datetime` e `timedelta`.

### Linhas 18 a 20

```python
from .. import net
from ..models import ALTA, NORMAL, URGENTE, Item
from .base import Conector
```

Importa `net`, as prioridades, a classe `Item` e a base.

### Linha 22

```python
API = "https://slack.com/api/"
```

Endereço base da Web API do Slack.

### Linha 23

```python
URGENTE_RE = re.compile(r"\b(urgente|asap|hoje|agora|importante|prazo)\b", re.I)
```

Expressão regular de palavras que indicam urgência ("urgente", "asap", "hoje", "agora", "importante", "prazo"). `re.I` ignora maiúsculas e minúsculas.

### Linhas 26 a 27

```python
class SlackConector(Conector):
    tipo = "slack"
```

Classe do conector, tipo "slack".

### Linhas 29 a 30

```python
    def __init__(self, empresa, opcoes, cfg):
        super().__init__(empresa, opcoes, cfg)
```

Construtor; chama o da base.

### Linha 31

```python
        self.token = self.opcao("token")
```

Lê o token do `.env`.

### Linha 32

```python
        self.meu_id = self.opcao("meu_id", obrigatorio=False)
```

Lê o id do seu usuário (opcional; com token de usuário ele é descoberto sozinho).

### Linha 33

```python
        self._nomes = {}      # cache: id do usuário -> nome
```

Cache de nomes de usuário, para não chamar `users.info` toda vez para a mesma pessoa.

### Linha 34

```python
        self.avisos = []      # canais pulados nesta coleta (apagados, sem acesso...)
```

Avisos da coleta atual (canais que não deu para ler).

### Linha 35

```python
        self._por_canal = {}  # mensagens já trazidas de cada canal (últimas 24 h)
```

Mensagens já trazidas de cada canal, para não baixar tudo de novo.

### Linha 36

```python
        self._ultimo = {}     # timestamp da mensagem mais nova de cada canal
```

Horário (timestamp) da mensagem mais nova de cada canal.

### Linha 38

```python
    def _api(self, metodo, **params):
```

Chama um método da API do Slack.

### Linhas 39 a 40

```python
        dados = net.get_json("Slack", API + metodo, client=self.client, params=params,
                             headers={"Authorization": f"Bearer {self.token}"})
```

GET com o token no cabeçalho `Bearer`.

### Linhas 41 a 42

```python
        if not dados.get("ok"):
            raise net.ApiError("Slack", f"{metodo} falhou: {dados.get('error', 'erro desconhecido')}")
```

Confere o `ok`; se for falso, lança `ApiError` com o nome do método e o código de erro do Slack (ex.: `channel_not_found`).

### Linha 43

```python
        return dados
```

Devolve os dados.

### Linha 45

```python
    def _paginar(self, metodo, chave, maximo=1000, **params):
```

Junta todas as páginas de uma lista.

### Linha 46

```python
        """Junta todas as páginas de uma lista do Slack (o Slack devolve aos pedaços)."""
```

Docstring.

### Linha 47

```python
        tudo, cursor = [], None
```

Lista acumulada e cursor.

### Linha 48

```python
        while len(tudo) < maximo:
```

Repete enquanto não passar do máximo.

### Linhas 49 a 50

```python
            if cursor:
                params["cursor"] = cursor
```

Se há cursor, pede a página seguinte.

### Linha 51

```python
            dados = self._api(metodo, **params)
```

Chama a API.

### Linha 52

```python
            tudo += dados.get(chave, [])
```

Acrescenta os itens da página (a chave varia: "channels", "members"...).

### Linha 53

```python
            cursor = (dados.get("response_metadata") or {}).get("next_cursor")
```

Pega o cursor da próxima página.

### Linhas 54 a 55

```python
            if not cursor:
                break
```

Sem cursor, acabou.

### Linha 56

```python
        return tudo[:maximo]
```

Devolve no máximo `maximo` itens.

### Linha 58

```python
    def _nome(self, user_id):
```

Descobre o nome de um usuário pelo id.

### Linhas 59 a 62

```python
        if user_id not in self._nomes:
            try:
                u = self._api("users.info", user=user_id)["user"]
                self._nomes[user_id] = u.get("profile", {}).get("display_name") or u.get("real_name") or user_id
```

Se ainda não está no cache, chama `users.info` e usa o nome de exibição, ou o nome real, ou o próprio id.

### Linhas 63 a 64

```python
            except net.ApiError:
                self._nomes[user_id] = user_id
```

Se falhar, guarda o id mesmo, para não tentar de novo.

### Linha 65

```python
        return self._nomes[user_id]
```

Devolve o nome.

### Linha 67

```python
    def limpar(self, texto):
```

Deixa o texto da mensagem legível.

### Linha 68

```python
        """Troca <@U123> por @nome e <http://x|rótulo> por rótulo."""
```

Docstring com os dois formatos que o Slack usa: menção `<@U123>` e link `<http://x|rótulo>`.

### Linha 69

```python
        texto = re.sub(r"<@(\w+)>", lambda m: "@" + self._nome(m.group(1)), texto)
```

Troca cada menção pelo "@nome". A função `lambda` recebe o resultado da busca e devolve o texto substituto.

### Linha 70

```python
        texto = re.sub(r"<([^|>]+)\|([^>]+)>", r"\2", texto)
```

Troca links com rótulo pelo rótulo (`\2` é o segundo grupo da expressão).

### Linha 71

```python
        texto = re.sub(r"<(https?://[^>]+)>", r"\1", texto)
```

Troca links sem rótulo pela URL.

### Linha 72

```python
        return " ".join(texto.split())
```

Junta tudo numa linha com espaços simples.

### Linha 74

```python
    def canais(self):
```

Monta a lista de conversas a ler.

### Linha 75

```python
        """Lista de (id, nome) a ler: os canais do config + DMs se incluir_dms: true."""
```

Docstring.

### Linha 76

```python
        lista = []
```

Lista de (id, nome).

### Linhas 77 a 82

```python
        for cid in self.opcoes.get("canais", []):
            try:
                nome = "#" + self._api("conversations.info", channel=cid)["channel"]["name"]
            except net.ApiError:
                nome = cid
            lista.append((cid, nome))
```

Para cada canal escolhido no config, pega o nome com `conversations.info` e coloca "#" na frente. Se falhar (canal apagado), usa o id.

### Linha 83

```python
        if self.opcoes.get("incluir_dms"):
```

Se as DMs estão ligadas.

### Linha 84

```python
            # users.conversations = conversas de que EU participo (precisa de token xoxp)
```

Comentário: `users.conversations` lista as conversas de que você participa.

### Linhas 85 a 87

```python
            try:
                conversas = self._paginar("users.conversations", "channels", 150, types="im,mpim",
                                          exclude_archived="true", limit=200)
```

Busca as DMs (`im`) e grupos de DM (`mpim`), até 150, sem arquivadas.

### Linhas 88 a 91

```python
            except net.ApiError as exc:
                motivo = "precisa do token de usuário (xoxp-)" if "missing_scope" in str(exc) else str(exc)
                self.avisos.append(f"DMs: {motivo}")
                conversas = []
```

Se falhar: com token de bot o erro é `missing_scope`, então a mensagem explica que precisa do token de usuário. Guarda como aviso e segue sem DMs.

### Linhas 92 a 93

```python
            # o Slack dá uma "prioridade" para cada conversa: lê só as 40 mais importantes,
            # para não estourar o limite de chamadas da API (HTTP 429)
```

Comentário: lê só as 40 conversas mais importantes, para não estourar o limite de chamadas (HTTP 429).

### Linha 94

```python
            conversas = [c for c in conversas if not c.get("is_user_deleted")]
```

Tira conversas com usuários apagados.

### Linha 95

```python
            conversas.sort(key=lambda c: c.get("priority") or 0, reverse=True)
```

Ordena pela prioridade que o próprio Slack dá a cada conversa, da maior para a menor (`reverse=True`).

### Linhas 96 a 100

```python
            for c in conversas[:40]:
                if c.get("is_im"):
                    lista.append((c["id"], "DM " + self._nome(c.get("user", ""))))
                else:
                    lista.append((c["id"], "Grupo " + c.get("name", "").replace("mpdm-", "")[:30]))
```

Para as 40 primeiras: se for DM, o nome é "DM" e o nome da pessoa; se for grupo, "Grupo" e o nome (sem o prefixo "mpdm-" e com até 30 caracteres).

### Linha 101

```python
        return lista
```

Devolve a lista.

### Linha 103

```python
    def coletar(self):
```

Coleta as mensagens.

### Linha 104

```python
        desde = (datetime.now() - timedelta(hours=24)).timestamp()
```

Timestamp de 24 horas atrás.

### Linhas 105 a 106

```python
        if not self.meu_id and self.token.startswith("xoxp-"):
            self.meu_id = self._api("auth.test").get("user_id", "")     # token de usuário: descobre quem sou eu
```

Se não sabemos seu id e o token é de usuário, descobre com `auth.test`.

### Linha 107

```python
        itens, self.avisos = [], []
```

Começa a coleta com listas vazias de itens e avisos.

### Linha 108

```python
        for cid, nome_canal in self.canais():   # canais() pode acrescentar avisos (ex.: DMs sem permissão)
```

Para cada conversa. O comentário lembra que `canais()` pode acrescentar avisos.

### Linhas 109 a 110

```python
            # só pede o que chegou depois da última mensagem que já temos deste canal
            a_partir = max(desde, self._ultimo.get(cid, 0))
```

Pede só o que chegou depois da última mensagem já conhecida deste canal (ou das últimas 24 horas, o que for mais recente). É o que evita baixar tudo de novo.

### Linhas 111 a 112

```python
            try:
                msgs = self._api("conversations.history", channel=cid, oldest=f"{a_partir:.6f}", limit=50)["messages"]
```

`conversations.history` com o canal, `oldest` (com 6 casas decimais, o formato do Slack) e até 50 mensagens.

### Linhas 113 a 117

```python
            except net.ApiError as exc:
                # um canal apagado ou sem acesso não pode derrubar o resumo inteiro: pula e avisa
                self.avisos.append(f"{nome_canal}: {str(exc).split('falhou: ')[-1]}")
                itens += [i for i in self._por_canal.get(cid, []) if i.quando.timestamp() >= desde]
                continue
```

Se o canal falhar: guarda o aviso só com o código de erro (o que vem depois de "falhou: "), mantém as mensagens antigas desse canal que ainda estão dentro das 24 horas e passa para o próximo canal com `continue`.

### Linha 118

```python
            novos = []
```

Lista das mensagens novas deste canal.

### Linhas 119 a 122

```python
            for m in msgs:
                # Ignora entradas de sistema (alguém entrou no canal etc.) e mensagens minhas
                if m.get("subtype") or not m.get("text") or m.get("user") == self.meu_id:
                    continue
```

Para cada mensagem: ignora mensagens de sistema (têm `subtype`, como "fulano entrou no canal"), sem texto, ou enviadas por você.

### Linhas 123 a 124

```python
                texto = m["text"]
                prioridade = NORMAL
```

Texto e prioridade inicial normal.

### Linhas 125 a 126

```python
                if self.meu_id and f"<@{self.meu_id}>" in texto:
                    prioridade = URGENTE          # me marcaram
```

Se a mensagem tem `<@seu_id>`, alguém te marcou: urgente.

### Linhas 127 a 128

```python
                elif nome_canal.startswith(("DM", "Grupo")):
                    prioridade = ALTA
```

Se é DM ou grupo, alta.

### Linhas 129 a 130

```python
                elif URGENTE_RE.search(texto):
                    prioridade = ALTA
```

Se tem palavra de urgência, alta.

### Linhas 131 a 137

```python
                novos.append(Item(
                    empresa=self.empresa, fonte="slack", tipo="mensagem",
                    titulo=f"{self._nome(m.get('user', ''))}: {self.limpar(texto)[:90]}",
                    detalhe=nome_canal,
                    quando=datetime.fromtimestamp(float(m["ts"]), self.fuso),
                    prioridade=prioridade, id=f"{cid}:{m['ts']}",
                ))
```

Cria o `Item`: título com o nome de quem mandou e os primeiros 90 caracteres do texto limpo, detalhe com o nome do canal, data convertida do `ts` do Slack (segundos com casas decimais) e id único "canal:ts".

### Linhas 138 a 139

```python
            if msgs:
                self._ultimo[cid] = max(float(m["ts"]) for m in msgs) + 0.000001
```

Guarda o horário da mensagem mais nova deste canal, somando um microssegundo para a próxima busca não trazer a mesma mensagem de novo.

### Linha 140

```python
            # junta as novas com as antigas e descarta o que passou de 24 h
```

Comentário: junta as novas com as antigas e descarta as mais velhas que 24 horas.

### Linha 141

```python
            ja = {i.id for i in novos}
```

Conjunto dos ids novos.

### Linha 142

```python
            juntas = novos + [i for i in self._por_canal.get(cid, []) if i.id not in ja and i.quando.timestamp() >= desde]
```

Junta as novas com as antigas que ainda valem e que não estão repetidas.

### Linhas 143 a 144

```python
            self._por_canal[cid] = juntas
            itens += juntas
```

Guarda para a próxima vez e soma ao resultado.

### Linha 145

```python
        return itens
```

Devolve os itens.
