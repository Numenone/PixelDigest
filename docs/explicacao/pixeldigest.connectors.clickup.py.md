# `pixeldigest/connectors/clickup.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/connectors/clickup.py)

Conector do ClickUp: busca as tarefas atribuídas a você que vencem até amanhã, incluindo as atrasadas.

### Linhas 1 a 5

```python
"""ClickUp: tarefas atribuídas a mim que vencem até amanhã (inclui as atrasadas).

Autenticação: token pessoal (pk_...) no header Authorization (sem "Bearer").
Datas do ClickUp vêm em milissegundos desde 1970, como texto.
"""
```

Docstring: autenticação por token pessoal no cabeçalho, sem a palavra "Bearer". As datas do ClickUp vêm em milissegundos desde 1970, como texto.

### Linha 6

```python
from datetime import datetime
```

Importa `datetime`.

### Linha 8

```python
from .. import net
```

Importa `net`.

### Linha 9

```python
from ..models import ALTA, BAIXA, NORMAL, URGENTE, Item
```

Importa as prioridades e a classe `Item`.

### Linha 10

```python
from .base import Conector
```

Importa a classe base.

### Linha 12

```python
API = "https://api.clickup.com/api/v2/"
```

Endereço base da API v2 do ClickUp.

### Linhas 13 a 14

```python
# Prioridade do ClickUp (1 urgente ... 4 baixa) -> a nossa
PRIORIDADES = {"1": URGENTE, "2": ALTA, "3": NORMAL, "4": BAIXA}
```

Converte a prioridade do ClickUp (1 urgente até 4 baixa, como texto) para a nossa escala.

### Linhas 17 a 18

```python
class ClickUpConector(Conector):
    tipo = "clickup"
```

Classe do conector, filha de `Conector`, com tipo "clickup".

### Linhas 20 a 21

```python
    def __init__(self, empresa, opcoes, cfg):
        super().__init__(empresa, opcoes, cfg)
```

Construtor: primeiro chama o da classe base com `super().__init__`.

### Linha 22

```python
        self.token = self.opcao("token")
```

Lê o token (do `.env`). Se faltar, `opcao` lança `ConfigError`.

### Linha 23

```python
        self.equipe = self.opcao("equipe_id")
```

Lê o id do workspace (no ClickUp a API chama de "team").

### Linha 24

```python
        self._meu_id = None
```

Id do usuário, descoberto na primeira vez que for preciso.

### Linhas 26 a 28

```python
    def _get(self, caminho, **params):
        return net.get_json("ClickUp", API + caminho, client=self.client, params=params,
                            headers={"Authorization": self.token})
```

Atalho para GET na API do ClickUp com o token no cabeçalho. `**params` recebe os parâmetros da URL.

### Linhas 30 a 33

```python
    def meu_id(self):
        if self._meu_id is None:
            self._meu_id = self._get("user")["user"]["id"]
        return self._meu_id
```

Descobre o id do usuário dono do token (endpoint `/user`) só uma vez e guarda. Técnica chamada de cache preguiçoso (lazy).

### Linha 35

```python
    def coletar(self):
```

Coleta as tarefas.

### Linha 36

```python
        limite_ms = int(self.fim_de_amanha().timestamp() * 1000)
```

Limite de vencimento em milissegundos: fim de amanhã convertido em timestamp (segundos) vezes 1000.

### Linhas 37 a 40

```python
        dados = self._get(f"team/{self.equipe}/task", **{
            "assignees[]": self.meu_id(), "due_date_lt": limite_ms,
            "include_closed": "false", "subtasks": "true", "order_by": "due_date",
        })
```

Chama `/team/{id}/task` com os filtros: atribuídas a mim (`assignees[]`), vencendo antes do limite, sem as fechadas, incluindo subtarefas e ordenadas por vencimento. O `**{...}` é necessário porque `assignees[]` tem colchetes e não pode ser um nome de argumento comum.

### Linhas 41 a 42

```python
        agora = self.agora()
        itens = []
```

Hora atual e lista de itens.

### Linha 43

```python
        for t in dados.get("tasks", []):
```

Para cada tarefa da resposta.

### Linhas 44 a 45

```python
            if not t.get("due_date"):
                continue
```

Pula tarefas sem data de vencimento.

### Linha 46

```python
            vence = datetime.fromtimestamp(int(t["due_date"]) / 1000, self.fuso)
```

Converte milissegundos (texto) para `datetime` no fuso do usuário: texto para inteiro, divide por 1000 para virar segundos.

### Linha 47

```python
            prio = PRIORIDADES.get(str((t.get("priority") or {}).get("id", "3")), NORMAL)
```

Prioridade da tarefa: lê o id dentro de `priority` (que pode vir `null`, por isso o `or {}`), com "3" (normal) como padrão, e traduz pelo dicionário.

### Linhas 48 a 50

```python
            atrasada = vence < agora
            if atrasada:
                prio = URGENTE
```

Se o vencimento já passou, a tarefa está atrasada e vira urgente.

### Linhas 51 a 56

```python
            itens.append(Item(
                empresa=self.empresa, fonte="clickup", tipo="tarefa",
                titulo=t["name"],
                detalhe=("ATRASADA" if atrasada else t.get("status", {}).get("status", "")),
                quando=vence, url=t.get("url", ""), prioridade=prio, id=t["id"],
            ))
```

Cria o `Item`: tipo tarefa, título da tarefa, detalhe "ATRASADA" ou o status atual, data de vencimento, link, prioridade e id.

### Linha 57

```python
        return itens
```

Devolve os itens.
