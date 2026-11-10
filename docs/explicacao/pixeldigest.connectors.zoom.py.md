# `pixeldigest/connectors/zoom.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/connectors/zoom.py)

Conector do Zoom: lê as reuniões agendadas para hoje e amanhã.

### Linhas 1 a 9

```python
"""Zoom: reuniões agendadas para hoje e amanhã (o "calendário do Zoom").

Autenticação: app "Server-to-Server OAuth" criado em marketplace.zoom.us
(Develop > Build App > Server-to-Server OAuth). Ele dá três valores:
Account ID, Client ID e Client Secret. O token (vale 1 h) é pedido com Basic Auth.
Escopo necessário: meeting:read:list_meetings:admin (ou meeting:read:admin).

A agenda do Zoom muda pouco, então é relida a cada 30 minutos.
"""
```

Docstring com o passo a passo da autenticação: um app "Server-to-Server OAuth" no marketplace do Zoom dá três valores (Account ID, Client ID e Client Secret); o token vale 1 hora e é pedido com Basic Auth. Diz também o escopo necessário e que a agenda é relida a cada 30 minutos.

### Linha 10

```python
import base64
```

Importa `base64`, usado para montar o cabeçalho Basic Auth.

### Linha 11

```python
import time
```

Importa `time` para controlar a validade do token.

### Linha 12

```python
from datetime import datetime
```

Importa `datetime`.

### Linhas 14 a 16

```python
from .. import net
from ..models import ALTA, Item
from .base import Conector
```

Importa `net`, a prioridade `ALTA`, a classe `Item` e a base.

### Linha 18

```python
API = "https://api.zoom.us/v2/"
```

Endereço base da API v2 do Zoom.

### Linhas 21 a 22

```python
class ZoomConector(Conector):
    tipo = "zoom"
```

Classe do conector, tipo "zoom".

### Linhas 24 a 25

```python
    def __init__(self, empresa, opcoes, cfg):
        super().__init__(empresa, opcoes, cfg)
```

Construtor; chama o da base.

### Linhas 26 a 28

```python
        self.account_id = self.opcao("account_id")
        self.client_id = self.opcao("client_id")
        self.client_secret = self.opcao("client_secret")
```

Lê as três credenciais (do `.env`).

### Linha 29

```python
        self.usuario = self.opcao("email", obrigatorio=False) or "me"   # e-mail da sua conta Zoom
```

E-mail da conta Zoom; se vazio, usa "me" (o dono do app).

### Linha 30

```python
        self._acesso, self._expira = None, 0
```

Token de acesso atual e o momento em que expira. Começam vazios.

### Linha 32

```python
    def _token(self):
```

Devolve um token válido, pedindo um novo quando precisa.

### Linhas 33 a 34

```python
        if self._acesso and time.time() < self._expira - 60:
            return self._acesso
```

Se já existe token e ainda falta mais de 1 minuto para expirar, reaproveita.

### Linha 35

```python
        basico = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
```

Monta o Basic Auth: "client_id:client_secret" codificado em Base64 (é o padrão do HTTP para esse tipo de autenticação).

### Linhas 36 a 38

```python
        r = net.request("Zoom", "POST", "https://zoom.us/oauth/token", client=self.client,
                        params={"grant_type": "account_credentials", "account_id": self.account_id},
                        headers={"Authorization": f"Basic {basico}"})
```

Pede o token com `grant_type=account_credentials` (o fluxo Server-to-Server) e o Account ID.

### Linhas 39 a 40

```python
        dados = r.json()
        self._acesso, self._expira = dados["access_token"], time.time() + int(dados.get("expires_in", 3600))
```

Guarda o token e calcula a expiração (agora mais `expires_in` segundos, padrão 3600).

### Linha 41

```python
        return self._acesso
```

Devolve o token.

### Linha 43

```python
    def coletar(self):
```

Coleta as reuniões.

### Linhas 44 a 46

```python
        dados = net.get_json("Zoom", API + f"users/{self.usuario}/meetings", client=self.client,
                             params={"type": "upcoming", "page_size": 50},
                             headers={"Authorization": f"Bearer {self._token()}"})
```

Chama `users/{email}/meetings` pedindo as próximas reuniões (`upcoming`), até 50, com o token no cabeçalho `Bearer`.

### Linha 47

```python
        inicio, fim = self.inicio_do_dia(), self.fim_de_amanha()
```

Janela de interesse: do começo de hoje ao fim de amanhã.

### Linha 48

```python
        itens = []
```

Lista de itens.

### Linha 49

```python
        for r in dados.get("meetings", []):
```

Para cada reunião.

### Linhas 50 a 51

```python
            if not r.get("start_time"):
                continue                                   # reunião sem horário fixo
```

Pula reuniões sem horário fixo (reuniões recorrentes sem data definida).

### Linha 52

```python
            quando = datetime.fromisoformat(r["start_time"].replace("Z", "+00:00")).astimezone(self.fuso)
```

Converte o horário. O Zoom manda em UTC com "Z" no fim; o `fromisoformat` precisa de "+00:00", por isso a troca. Depois converte para o fuso do usuário.

### Linhas 53 a 54

```python
            if not inicio <= quando < fim:
                continue
```

Ignora o que estiver fora da janela.

### Linhas 55 a 59

```python
            itens.append(Item(
                empresa=self.empresa, fonte="zoom", tipo="evento", titulo=r.get("topic") or "Reunião Zoom",
                detalhe=f"Zoom · {r.get('duration', 0)} min", quando=quando,
                url=r.get("join_url", ""), prioridade=ALTA, id=str(r.get("id")),
            ))
```

Cria o `Item` do tipo evento com o tema, a duração, o link para entrar e prioridade alta.

### Linha 60

```python
        return itens
```

Devolve os itens.
