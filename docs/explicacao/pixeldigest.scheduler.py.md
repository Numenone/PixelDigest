# `pixeldigest/scheduler.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/scheduler.py)

Agendador de tarefas por tempo: são os gatilhos de horário do projeto (07:00, 18:00 e as tarefas que repetem a cada N segundos).

### Linhas 1 a 7

```python
"""Agendador simples de tarefas (os gatilhos de tempo do requisito 5).

- Diario: roda uma vez por dia num horário (07:00 resumo, 18:00 fim do expediente).
  Se o PC ligar atrasado (até 2 h depois), ainda roda. Lembra o último dia em
  data/agenda.json para não repetir se o programa reiniciar.
- Intervalo: roda a cada N segundos (clima, resumo, Teams, reenvio de notificações).
"""
```

Docstring: explica os dois tipos de tarefa. A diária tem tolerância de 2 horas (se o PC ligar às 08:30, o bom dia ainda sai) e lembra o último dia em que rodou num arquivo, para não repetir se o programa for reaberto.

### Linha 8

```python
import json
```

Importa `json` para ler e gravar o arquivo de estado.

### Linha 9

```python
import logging
```

Importa `logging` para registrar quando uma tarefa falha.

### Linha 10

```python
from datetime import datetime, timedelta
```

Importa `datetime` e `timedelta` para as contas de horário.

### Linha 12

```python
from .config import DATA
```

Importa a pasta `data/` definida em `config.py`.

### Linha 14

```python
log = logging.getLogger(__name__)
```

Logger deste módulo.

### Linha 15

```python
ESTADO = DATA / "agenda.json"
```

Caminho do arquivo que guarda o último dia de cada tarefa diária: `data/agenda.json`. O operador `/` junta caminhos em objetos `Path`.

### Linha 18

```python
def _ler_estado():
```

Função interna (o `_` no começo do nome indica que é de uso interno) que lê o estado salvo.

### Linhas 19 a 20

```python
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
```

Lê o arquivo como texto UTF-8 e converte o JSON para dicionário.

### Linhas 21 a 22

```python
    except (OSError, ValueError):
        return {}
```

Se o arquivo não existe (`OSError`) ou está corrompido (`ValueError`, que inclui erro de JSON), devolve um dicionário vazio em vez de quebrar.

### Linha 25

```python
class Diario:
```

Classe da tarefa diária.

### Linha 26

```python
    def __init__(self, nome, hora, funcao, tolerancia_h=2):
```

Construtor: nome da tarefa, hora (`datetime.time`), a função a executar e a tolerância em horas.

### Linha 27

```python
        self.nome, self.hora, self.funcao = nome, hora, funcao
```

Guarda os três valores de uma vez com atribuição múltipla.

### Linha 28

```python
        self.tolerancia = timedelta(hours=tolerancia_h)
```

Converte a tolerância para `timedelta` (para somar em datas).

### Linha 29

```python
        self.ultima = _ler_estado().get(nome)        # "2026-11-06"
```

Lê do arquivo o último dia em que essa tarefa rodou (ex.: "2026-11-06"), ou `None` se nunca rodou.

### Linha 31

```python
    def na_hora(self, agora):
```

Método que responde se a tarefa deve rodar agora.

### Linha 32

```python
        alvo = datetime.combine(agora.date(), self.hora, agora.tzinfo)
```

Monta o horário-alvo de hoje: a data de hoje com a hora da tarefa, no mesmo fuso de `agora`.

### Linha 33

```python
        return alvo <= agora <= alvo + self.tolerancia and self.ultima != agora.date().isoformat()
```

Roda se: já passou do horário-alvo, ainda está dentro da tolerância, e ainda não rodou hoje. As comparações encadeadas `a <= b <= c` funcionam em Python.

### Linha 35

```python
    def marcar(self, agora):
```

Marca que a tarefa rodou hoje.

### Linha 36

```python
        self.ultima = agora.date().isoformat()
```

Atualiza na memória.

### Linhas 37 a 39

```python
        estado = _ler_estado()
        estado[self.nome] = self.ultima
        ESTADO.write_text(json.dumps(estado), encoding="utf-8")
```

Atualiza no arquivo: lê o estado atual, troca só a entrada desta tarefa e grava de novo em JSON.

### Linha 42

```python
class Intervalo:
```

Classe da tarefa por intervalo (ex.: clima a cada 30 min).

### Linha 43

```python
    def __init__(self, nome, segundos, funcao, ja=False):
```

Construtor. O parâmetro `ja=True` faz a tarefa rodar logo na primeira verificação.

### Linha 44

```python
        self.nome, self.segundos, self.funcao = nome, segundos, funcao
```

Guarda nome, intervalo em segundos e função.

### Linha 45

```python
        self.proxima = None if ja else datetime.now().astimezone() + timedelta(seconds=segundos)
```

Próxima execução: `None` (rodar já) ou agora mais o intervalo. O `x if condição else y` é o "if de uma linha" do Python.

### Linhas 47 a 48

```python
    def na_hora(self, agora):
        return self.proxima is None or agora >= self.proxima
```

Está na hora se nunca rodou ou se o horário atual passou da próxima execução.

### Linhas 50 a 51

```python
    def marcar(self, agora):
        self.proxima = agora + timedelta(seconds=self.segundos)
```

Depois de rodar, agenda a próxima para daqui a N segundos.

### Linhas 54 a 56

```python
class Agenda:
    def __init__(self):
        self.tarefas = []
```

Classe `Agenda`: só uma lista de tarefas.

### Linhas 58 a 59

```python
    def adicionar(self, tarefa):
        self.tarefas.append(tarefa)
```

Adiciona uma tarefa (diária ou por intervalo; as duas têm os mesmos métodos `na_hora` e `marcar`, então a agenda trata as duas igual).

### Linha 61

```python
    def tick(self, agora):
```

`tick` é chamado pelo motor a cada segundo com a hora atual.

### Linha 62

```python
        """Roda o que estiver na hora. Um erro numa tarefa não para as outras."""
```

Docstring: um erro numa tarefa não impede as outras.

### Linhas 63 a 65

```python
        for t in self.tarefas:
            if t.na_hora(agora):
                t.marcar(agora)
```

Para cada tarefa que está na hora, primeiro marca (assim, se a tarefa falhar, ela não fica tentando de novo a cada segundo).

### Linhas 66 a 69

```python
                try:
                    t.funcao()
                except Exception:
                    log.exception("tarefa '%s' falhou", t.nome)
```

Executa a função. Se der qualquer erro, `log.exception` grava a mensagem com o rastro completo do erro (traceback) e o laço continua com a próxima tarefa.
