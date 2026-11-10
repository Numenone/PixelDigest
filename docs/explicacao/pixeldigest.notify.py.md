# `pixeldigest/notify.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/notify.py)

Envia as notificações para o Discord e para o celular ao mesmo tempo. Se um envio falhar, a mensagem é guardada e reenviada depois.

### Linhas 1 a 8

```python
"""Notificações: Discord (webhook) e celular (ntfy) AO MESMO TEMPO.

- Discord: POST de um "embed" (cartão colorido) no webhook do canal.
- Celular: POST no ntfy (app grátis no Android). Chega como notificação normal.

Resiliência: os dois envios rodam em paralelo; se um falhar (sem internet, 5xx),
a mensagem vai para data/pendentes.json e é reenviada depois.
"""
```

Docstring: Discord recebe um cartão colorido (embed) por webhook; o celular recebe pelo ntfy. Os dois envios são paralelos e quem falhar vai para `data/pendentes.json`.

### Linha 9

```python
import json
```

Importa `json` (fila de pendentes).

### Linha 10

```python
import logging
```

Importa `logging`.

### Linha 11

```python
from concurrent.futures import ThreadPoolExecutor
```

Importa `ThreadPoolExecutor`, um grupo de threads prontas para executar tarefas em paralelo e devolver o resultado depois.

### Linha 12

```python
from datetime import datetime, timezone
```

Importa `datetime` e `timezone` (o Discord pede a data em UTC).

### Linha 14

```python
from . import net
```

Importa `net` (todas as chamadas passam pelo cliente resiliente).

### Linha 15

```python
from .config import DATA, cor_rgb, env
```

Importa a pasta `data/`, o conversor de cor e a leitura de variáveis de ambiente.

### Linha 17

```python
log = logging.getLogger(__name__)
```

Logger do módulo.

### Linha 18

```python
PENDENTES = DATA / "pendentes.json"
```

Caminho da fila de pendentes.

### Linha 21

```python
class Notificador:
```

Classe do notificador.

### Linhas 22 a 23

```python
    def __init__(self, cfg):
        n = cfg["notificacoes"]
```

Construtor; atalho para as opções de notificação.

### Linha 24

```python
        self.discord_url = env("DISCORD_WEBHOOK_URL", obrigatorio=False) if n["discord"] else ""
```

URL do webhook do Discord, lida do `.env`, só se o Discord estiver ligado nas Configurações.

### Linha 25

```python
        self.ntfy_topico = env("NTFY_TOPIC", obrigatorio=False) if n["celular"] else ""
```

Tópico do ntfy (o "canal" que o celular assina), só se o celular estiver ligado.

### Linha 26

```python
        self.ntfy_servidor = (env("NTFY_SERVER", obrigatorio=False) or "https://ntfy.sh").rstrip("/")
```

Servidor do ntfy: o configurado ou o público `https://ntfy.sh`. `rstrip("/")` tira a barra do fim para não ficar duplicada.

### Linha 27

```python
        self.ntfy_token = env("NTFY_TOKEN", obrigatorio=False)
```

Token do ntfy (opcional, para servidores com senha).

### Linha 28

```python
        self.client = None              # os testes trocam por um cliente falso
```

Cliente HTTP: `None` usa o compartilhado; os testes trocam por um cliente falso.

### Linha 29

```python
        self._pool = ThreadPoolExecutor(max_workers=2)
```

Grupo com 2 threads, uma para cada canal.

### Linhas 31 a 32

```python
    def ativo(self):
        return bool(self.discord_url or self.ntfy_topico)
```

Está ativo se pelo menos um canal tiver configuração.

### Linha 34

```python
    # ---------- montagem dos payloads (JSON) ----------
```

Comentário: montagem do conteúdo (payload) em JSON.

### Linha 35

```python
    def payload_discord(self, titulo, texto, cor, campos, url):
```

Monta o JSON do Discord.

### Linhas 36 a 40

```python
        embed = {
            "title": titulo[:256], "description": texto[:4000], "color": int("%02x%02x%02x" % cor_rgb(cor), 16),
            "fields": [{"name": nome[:256], "value": (valor or "-")[:1024], "inline": False} for nome, valor in (campos or [])][:25],
            "footer": {"text": "PixelDigest"}, "timestamp": datetime.now(timezone.utc).isoformat(),
        }
```

O embed (cartão) tem: título (o Discord aceita até 256 caracteres, por isso o corte `[:256]`), descrição (até 4000), cor (o Discord quer a cor como número inteiro: a cor vira RGB, depois texto hexadecimal "3fa7ff" e depois inteiro na base 16), campos (um por empresa; limites de 256 no nome, 1024 no valor e 25 campos; valor vazio vira "-"), rodapé e data em UTC no formato ISO.

### Linhas 41 a 42

```python
        if url:
            embed["url"] = url
```

Se houver link, o título do cartão vira clicável.

### Linha 43

```python
        return {"username": "PixelDigest", "embeds": [embed]}
```

Devolve o corpo final: nome do remetente e a lista de embeds.

### Linha 45

```python
    def payload_ntfy(self, titulo, texto, campos, tags, prioridade, url):
```

Monta o JSON do ntfy.

### Linhas 46 a 48

```python
        corpo = texto
        for nome, valor in campos or []:
            corpo += f"\n\n{nome}\n{valor}"
```

O ntfy não tem campos separados, então os campos são acrescentados ao texto, cada um com o nome numa linha e o valor na outra.

### Linhas 49 a 50

```python
        p = {"topic": self.ntfy_topico, "title": titulo, "message": corpo[:3500],
             "tags": tags or [], "priority": prioridade}
```

Corpo do ntfy: tópico, título, mensagem (cortada em 3500 caracteres), tags (viram emojis na notificação) e prioridade (1 a 5; 4 e 5 fazem o celular tocar mais forte).

### Linhas 51 a 52

```python
        if url:
            p["click"] = url
```

Se houver link, tocar na notificação abre o link (`click`).

### Linha 53

```python
        return p
```

Devolve.

### Linha 55

```python
    # ---------- envio ----------
```

Comentário: envio.

### Linha 56

```python
    def _enviar(self, canal, payload):
```

Envia um payload para um canal.

### Linhas 57 a 58

```python
        if canal == "discord":
            net.request("Discord", "POST", self.discord_url, json=payload, client=self.client)
```

Discord: POST com o JSON no webhook.

### Linhas 59 a 61

```python
        else:
            headers = {"Authorization": f"Bearer {self.ntfy_token}"} if self.ntfy_token else {}
            net.request("ntfy", "POST", self.ntfy_servidor, json=payload, headers=headers, client=self.client)
```

ntfy: se houver token, monta o cabeçalho `Authorization: Bearer ...`; senão, sem cabeçalho. POST com o JSON no servidor (o tópico vai dentro do JSON).

### Linha 63

```python
    def enviar(self, titulo, texto, cor="#5ab0ff", campos=None, tags=None, prioridade=3, url=""):
```

Função pública de envio, com valores padrão para os parâmetros opcionais.

### Linha 64

```python
        """Manda para Discord e celular em paralelo. Devolve {canal: True/False}."""
```

Docstring: manda em paralelo e devolve um dicionário com o resultado de cada canal.

### Linhas 65 a 69

```python
        envios = {}
        if self.discord_url:
            envios["discord"] = self.payload_discord(titulo, texto, cor, campos, url)
        if self.ntfy_topico:
            envios["celular"] = self.payload_ntfy(titulo, texto, campos, tags, prioridade, url)
```

Monta o payload de cada canal configurado.

### Linhas 70 a 71

```python
        futuros = {canal: self._pool.submit(self._enviar, "discord" if canal == "discord" else "ntfy", p)
                   for canal, p in envios.items()}
```

Envia cada um numa thread do grupo. `submit` devolve um "futuro", um objeto que vai ter o resultado quando a tarefa terminar.

### Linha 72

```python
        resultado = {}
```

Resultado por canal.

### Linhas 73 a 76

```python
        for canal, futuro in futuros.items():
            try:
                futuro.result(timeout=40)
                resultado[canal] = True
```

Espera cada envio terminar (até 40 segundos). Se não houve erro, marca `True`.

### Linhas 77 a 80

```python
            except Exception as exc:
                log.warning("notificação por %s falhou: %s (guardada para reenviar)", canal, exc)
                self._guardar(canal, envios[canal])
                resultado[canal] = False
```

Se falhou: registra, guarda para reenviar e marca `False`.

### Linha 81

```python
        return resultado
```

Devolve o resultado.

### Linhas 83 a 86

```python
    def _guardar(self, canal, payload):
        fila = self._ler_pendentes()
        fila.append({"canal": canal, "payload": payload})
        PENDENTES.write_text(json.dumps(fila[-100:], ensure_ascii=False), encoding="utf-8")
```

Acrescenta o envio que falhou na fila do arquivo, mantendo só os últimos 100.

### Linhas 88 a 92

```python
    def _ler_pendentes(self):
        try:
            return json.loads(PENDENTES.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
```

Lê a fila; se não existir ou estiver corrompida, devolve lista vazia.

### Linha 94

```python
    def reenviar_pendentes(self):
```

Reenvia o que falhou antes.

### Linha 95

```python
        """Tenta de novo o que falhou antes (roda a cada 5 minutos)."""
```

Docstring: roda a cada 5 minutos (agendado no motor).

### Linhas 96 a 98

```python
        fila = self._ler_pendentes()
        if not fila:
            return 0
```

Se a fila estiver vazia, não faz nada e devolve 0.

### Linhas 99 a 104

```python
        sobrou = []
        for item in fila:
            try:
                self._enviar("discord" if item["canal"] == "discord" else "ntfy", item["payload"])
            except Exception:
                sobrou.append(item)
```

Tenta cada item. O que falhar de novo vai para a lista `sobrou`.

### Linha 105

```python
        PENDENTES.write_text(json.dumps(sobrou, ensure_ascii=False), encoding="utf-8")
```

Grava de volta só o que sobrou.

### Linha 106

```python
        return len(fila) - len(sobrou)
```

Devolve quantos foram reenviados com sucesso.
