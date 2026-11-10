# `pixeldigest/phone.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/phone.py)

Escuta o alarme do celular. O MacroDroid (Android) detecta o alarme e publica no ntfy; este módulo fica conectado no tópico recebendo os eventos em tempo real.

### Linhas 1 a 9

```python
"""Ouve o alarme do celular.

Como funciona: no Android, o app MacroDroid detecta o alarme tocando e faz um
POST no ntfy (ex.: https://ntfy.sh/<NTFY_TOPIC_ALARME>). Este módulo fica
conectado nesse tópico recebendo os eventos em tempo real (streaming JSON,
uma linha por mensagem). Não precisa abrir porta no roteador.

Se a conexão cair, reconecta sozinho com espera crescente (5 s, 10 s ... até 60 s).
"""
```

Docstring com o caminho completo: alarme toca, MacroDroid faz POST no ntfy, o PC recebe por streaming (uma linha JSON por mensagem). Não precisa abrir porta no roteador, porque é o PC que se conecta ao ntfy. Se cair, reconecta com espera crescente.

### Linha 10

```python
import json
```

Importa `json` para ler cada linha do streaming.

### Linha 11

```python
import logging
```

Importa `logging`.

### Linha 12

```python
import threading
```

Importa `threading`: o ouvinte é uma thread separada.

### Linha 13

```python
import time
```

Importa `time` para guardar a hora do último alarme.

### Linha 15

```python
import httpx
```

Importa `httpx`, usado direto aqui porque precisamos do modo streaming (a resposta chega aos poucos e nunca termina).

### Linha 17

```python
from .config import env
```

Importa a leitura de variáveis de ambiente.

### Linha 19

```python
log = logging.getLogger(__name__)
```

Logger do módulo.

### Linha 22

```python
class OuvinteAlarme(threading.Thread):
```

O ouvinte herda de `Thread`, como o motor.

### Linhas 23 a 24

```python
    def __init__(self, ao_receber):
        super().__init__(daemon=True, name="alarme")
```

Construtor; a thread é `daemon` (morre com o programa) e se chama "alarme".

### Linha 25

```python
        self.ao_receber = ao_receber      # função chamada com (titulo, mensagem)
```

Guarda a função que deve ser chamada quando o alarme tocar.

### Linha 26

```python
        self.topico = env("NTFY_TOPIC_ALARME", obrigatorio=False)
```

Tópico do alarme no ntfy, lido do `.env`.

### Linha 27

```python
        self.servidor = (env("NTFY_SERVER", obrigatorio=False) or "https://ntfy.sh").rstrip("/")
```

Servidor do ntfy (padrão público).

### Linha 28

```python
        self.token = env("NTFY_TOKEN", obrigatorio=False)
```

Token opcional.

### Linha 29

```python
        self.parar = threading.Event()
```

Sinal de parada.

### Linha 30

```python
        self.conectado = False         # a bolinha "Alarme" no topo fica verde só quando True
```

Indica se está conectado; a tela mostra uma bolinha verde quando está.

### Linha 31

```python
        self.ultima = None             # (hora, mensagem) do último alarme recebido
```

Último alarme recebido (hora e mensagem), mostrado na tela.

### Linhas 33 a 34

```python
    def configurado(self):
        return bool(self.topico)
```

Está configurado se existe um tópico.

### Linha 36

```python
    def run(self):
```

Código que a thread executa.

### Linha 37

```python
        espera = 5
```

Espera inicial de reconexão: 5 segundos.

### Linha 38

```python
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
```

Cabeçalho de autenticação, se houver token.

### Linha 39

```python
        url = f"{self.servidor}/{self.topico}/json"
```

URL de streaming do ntfy: o sufixo `/json` faz o servidor mandar cada mensagem como uma linha JSON.

### Linha 40

```python
        while not self.parar.is_set():
```

Repete até mandarem parar.

### Linhas 41 a 44

```python
            try:
                # A conexão fica aberta; o ntfy manda um "keepalive" a cada ~45 s.
                # Se ficar 2 min sem nada, consideramos caída e reconectamos.
                with httpx.stream("GET", url, headers=headers, timeout=httpx.Timeout(10, read=120)) as resp:
```

Abre a conexão em modo streaming. O comentário explica o tempo limite: o ntfy manda um sinal de vida (keepalive) a cada 45 segundos; se passar 2 minutos (`read=120`) sem nada, a conexão é considerada caída. `connect` tem limite de 10 segundos. O `with` fecha a conexão ao sair do bloco.

### Linha 45

```python
                    resp.raise_for_status()
```

Se o servidor respondeu com erro (4xx ou 5xx), lança exceção.

### Linhas 46 a 47

```python
                    self.conectado = True
                    espera = 5
```

Conectou: liga a bolinha verde e volta a espera para 5 segundos.

### Linha 48

```python
                    for linha in resp.iter_lines():
```

Lê a resposta linha por linha conforme as linhas chegam (o laço fica esperando a próxima).

### Linhas 49 a 50

```python
                        if self.parar.is_set():
                            return
```

Se mandaram parar, sai da função.

### Linhas 51 a 52

```python
                        if not linha.strip():
                            continue
```

Ignora linhas vazias.

### Linha 53

```python
                        evento = json.loads(linha)
```

Converte a linha de JSON para dicionário.

### Linha 54

```python
                        if evento.get("event") == "message":
```

Só interessa o evento do tipo "message" (os outros são "open" e "keepalive").

### Linha 55

```python
                            self.ultima = (time.strftime("%H:%M"), evento.get("message") or "")
```

Guarda a hora e o texto do alarme.

### Linha 56

```python
                            self.ao_receber(evento.get("title") or "Alarme", evento.get("message") or "")
```

Chama a função do motor com o título (ou "Alarme") e a mensagem.

### Linhas 57 a 58

```python
            except (httpx.HTTPError, ValueError) as exc:
                self.conectado = False
```

Se der erro de HTTP ou de JSON, marca como desconectado.

### Linha 59

```python
                log.warning("ouvinte do alarme desconectado (%s); tentando em %ss", exc, espera)
```

Registra o problema e quanto tempo vai esperar.

### Linha 60

```python
                self.parar.wait(espera)
```

Espera antes de reconectar. `self.parar.wait(espera)` é melhor que `time.sleep`: se mandarem parar no meio da espera, a thread acorda na hora.

### Linha 61

```python
                espera = min(espera * 2, 60)
```

Dobra a espera a cada falha (5, 10, 20, 40), com teto de 60 segundos.
