# `pixeldigest/net.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/net.py)

Toda conversa com a internet passa por este arquivo. Ele é a peça principal do requisito de tratamento de erros: nenhuma chamada fica travada para sempre, falhas temporárias são tentadas de novo e todo erro vira uma mensagem clara com o nome do serviço.

### Linhas 1 a 7

```python
"""Cliente HTTP resiliente usado por todos os conectores.

Requisito 6 (tratamento de erros): toda chamada de rede passa por aqui e ganha
- tempo limite (timeout), para nada ficar travado esperando para sempre;
- novas tentativas com espera crescente em falha de rede, 429 e erros 5xx;
- erro claro (ApiError) com o nome do serviço, em vez de quebrar em silêncio.
"""
```

Docstring explicando o que o módulo garante: tempo limite, novas tentativas com espera crescente e um erro próprio (`ApiError`).

### Linha 8

```python
import logging
```

Importa `logging` para registrar avisos quando uma tentativa falha.

### Linha 9

```python
import threading
```

Importa `threading`, porque várias threads (motor, resumo dos e-mails, botões das Configurações) podem pedir o cliente HTTP ao mesmo tempo. Usamos uma trava (`Lock`) para não criar dois clientes.

### Linha 10

```python
import time
```

Importa `time` para esperar entre uma tentativa e outra.

### Linha 12

```python
import httpx
```

Importa o `httpx`, a biblioteca HTTP usada no projeto (parecida com o `requests`, mas com timeout, conexões reaproveitadas e um transporte falso para testes).

### Linha 14

```python
log = logging.getLogger(__name__)
```

Cria o "logger" deste módulo. `__name__` vale `pixeldigest.net`, e esse nome aparece no log.

### Linhas 16 a 17

```python
# Códigos que valem tentar de novo: excesso de requisições e falhas do servidor
RETRY_STATUS = {429, 500, 502, 503, 504}
```

Conjunto (`set`) dos códigos HTTP que valem tentar de novo: 429 (muitas requisições, o servidor pede para ir mais devagar) e 500, 502, 503 e 504 (falhas temporárias do servidor). Um `set` deixa a busca com `in` instantânea.

### Linha 20

```python
_cliente = None
```

Variável global que guarda o cliente HTTP único. Começa vazia (`None`) e é criada na primeira vez que alguém precisar.

### Linha 21

```python
_trava = threading.Lock()
```

Trava usada para que duas threads não criem o cliente ao mesmo tempo.

### Linha 24

```python
def cliente_compartilhado():
```

Define a função que devolve o cliente HTTP compartilhado.

### Linhas 25 a 29

```python
    """Um único httpx.Client para o programa todo (economiza RAM e é mais rápido).

    Criar um cliente por chamada recarregava os certificados HTTPS toda vez.
    O httpx.Client pode ser usado por várias threads ao mesmo tempo.
    """
```

Docstring: um único cliente para o programa todo economiza memória e é mais rápido, porque reaproveita conexões e não recarrega os certificados HTTPS a cada chamada. O `httpx.Client` aceita uso por várias threads.

### Linha 30

```python
    global _cliente
```

Diz que vamos alterar a variável global `_cliente`.

### Linha 31

```python
    with _trava:
```

`with _trava:` pega a trava e solta automaticamente no fim do bloco, mesmo se der erro. Enquanto uma thread está aqui dentro, as outras esperam.

### Linhas 32 a 33

```python
        if _cliente is None:
            _cliente = httpx.Client(timeout=15, limits=httpx.Limits(max_connections=10, max_keepalive_connections=5))
```

Se o cliente ainda não existe, cria. `timeout=15` limita cada chamada a 15 segundos. `Limits` limita a 10 conexões abertas e mantém até 5 vivas para reaproveitar.

### Linha 34

```python
        return _cliente
```

Devolve o cliente (novo ou já existente).

### Linha 37

```python
class ApiError(Exception):
```

Cria a exceção `ApiError`, herdando de `Exception`. Todos os conectores lançam esse mesmo tipo de erro, então quem chama só precisa tratar um tipo.

### Linha 38

```python
    """Falha ao falar com um serviço externo (já com mensagem amigável)."""
```

Docstring da classe.

### Linha 40

```python
    def __init__(self, service, message, status=None):
```

Construtor: recebe o nome do serviço, a mensagem e, opcionalmente, o código HTTP.

### Linha 41

```python
        super().__init__(f"{service}: {message}")
```

Chama o construtor da classe-mãe com o texto final, ex.: "Slack: acesso negado". É esse texto que aparece com `str(erro)`.

### Linhas 42 a 43

```python
        self.service = service
        self.status = status
```

Guarda o serviço e o status como atributos, para quem tratar o erro poder decidir com base neles (ex.: 401 significa token errado).

### Linha 46

```python
def request(service, method, url, *, retries=3, timeout=15, client=None, backoff=1.5, **kwargs):
```

Define `request`, a função que faz qualquer requisição. O `*` obriga os parâmetros seguintes a serem passados pelo nome (ex.: `retries=5`), o que deixa as chamadas mais legíveis. `**kwargs` recebe qualquer outro argumento do httpx (params, json, headers...).

### Linhas 47 a 52

```python
    """Faz uma requisição HTTP e devolve a resposta (status 2xx/3xx).

    service: nome que aparece nos erros e no log (ex.: "Slack").
    client:  um httpx.Client já pronto (os testes passam um cliente falso aqui).
    kwargs:  repassados ao httpx (params, json, headers, data...).
    """
```

Docstring explicando os parâmetros. O detalhe importante é o `client`: nos testes passamos um cliente falso, que responde sem internet.

### Linha 53

```python
    client = client or cliente_compartilhado()
```

Usa o cliente recebido ou, se nenhum foi passado, o compartilhado. O `or` devolve o primeiro valor "verdadeiro".

### Linha 54

```python
    kwargs.setdefault("timeout", timeout)
```

Se quem chamou não passou `timeout`, coloca o padrão de 15 segundos. `setdefault` só grava se a chave não existir.

### Linha 55

```python
    last_error = None
```

Guarda o último erro, para lançar no final se todas as tentativas falharem.

### Linha 56

```python
    for attempt in range(1, retries + 1):
```

Repete de 1 até `retries` (padrão 3 tentativas). `range(1, 4)` gera 1, 2 e 3.

### Linha 57

```python
        wait = backoff ** attempt
```

Espera crescente (backoff exponencial): 1,5 elevado ao número da tentativa, ou seja 1,5 s, 2,25 s, 3,4 s. Isso evita martelar um servidor que já está com problema.

### Linhas 58 a 59

```python
        try:
            resp = client.request(method, url, **kwargs)
```

Faz a requisição de fato.

### Linhas 60 a 61

```python
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            last_error = ApiError(service, f"sem resposta da rede ({type(exc).__name__})")
```

Se der timeout ou erro de rede (sem internet, DNS falhou), não quebra o programa: guarda um `ApiError` amigável com o nome técnico do erro e segue para a próxima tentativa.

### Linha 62

```python
        else:
```

O `else` de um `try` roda só se não houve exceção, ou seja, quando o servidor respondeu.

### Linhas 63 a 64

```python
            if resp.status_code in RETRY_STATUS:
                last_error = ApiError(service, f"HTTP {resp.status_code}", resp.status_code)
```

Se o código for um dos que valem repetir, guarda o erro e continua o laço.

### Linhas 65 a 68

```python
                # Se o servidor disser quanto esperar (Retry-After), respeitamos
                retry_after = resp.headers.get("Retry-After", "")
                if retry_after.isdigit():
                    wait = min(int(retry_after), 30)
```

Se o servidor mandou o cabeçalho `Retry-After` (quantos segundos esperar), respeitamos o pedido, com teto de 30 segundos. `isdigit()` confere se é um número antes de converter.

### Linhas 69 a 70

```python
            elif resp.status_code in (401, 403):
                raise ApiError(service, f"acesso negado (HTTP {resp.status_code}). Confira o token no .env", resp.status_code)
```

401 (não autenticado) ou 403 (proibido): token errado ou sem permissão. Não adianta tentar de novo, então lança o erro na hora, já dizendo onde conferir.

### Linhas 71 a 72

```python
            elif resp.status_code >= 400:
                raise ApiError(service, f"HTTP {resp.status_code}: {resp.text[:200]}", resp.status_code)
```

Qualquer outro erro 4xx (ex.: 404, 400): também não adianta repetir. Lança o erro com os primeiros 200 caracteres da resposta, que normalmente explicam o problema.

### Linhas 73 a 74

```python
            else:
                return resp
```

Código 2xx ou 3xx: deu certo, devolve a resposta.

### Linha 75

```python
        log.warning("%s (tentativa %d de %d)", last_error, attempt, retries)
```

Chegando aqui, a tentativa falhou: registra um aviso no log, ex.: "Slack: HTTP 503 (tentativa 1 de 3)".

### Linhas 76 a 77

```python
        if attempt < retries:
            time.sleep(wait)
```

Se ainda há tentativas, espera antes da próxima. Na última, não espera à toa.

### Linha 78

```python
    raise last_error
```

Todas as tentativas falharam: lança o último erro guardado para quem chamou tratar.

### Linhas 81 a 83

```python
def get_json(service, url, **kwargs):
    """Atalho: GET que já devolve o JSON."""
    return request(service, "GET", url, **kwargs).json()
```

Atalho para GET que já converte a resposta de JSON para dicionário Python (`.json()`).

### Linhas 86 a 89

```python
def post_json(service, url, payload, **kwargs):
    """Atalho: POST com corpo JSON que devolve o JSON da resposta (ou {} se vazio)."""
    resp = request(service, "POST", url, json=payload, **kwargs)
    return resp.json() if resp.content else {}
```

Atalho para POST com corpo JSON. Se a resposta vier vazia (alguns serviços respondem 204 sem corpo), devolve `{}` em vez de quebrar tentando ler JSON.
