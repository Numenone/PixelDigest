# `pixeldigest/connectors/__init__.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/connectors/__init__.py)

Registro dos tipos de serviço e função que cria os conectores a partir da configuração. O `__init__.py` transforma a pasta `connectors` num pacote Python e roda quando alguém faz `from . import connectors`. Aqui fica o registro dos tipos de serviço e a função que cria os conectores a partir da configuração.

### Linhas 1 a 4

```python
"""Monta os conectores a partir do config.yaml.

Para adicionar um serviço novo, crie o arquivo do conector e registre o tipo aqui.
"""
```

Docstring: para adicionar um serviço novo basta criar o arquivo do conector e registrar o tipo neste arquivo.

### Linha 5

```python
from ..config import ConfigError
```

Importa o erro de configuração. Os dois pontos (`..`) sobem um nível: do pacote `connectors` para o pacote `pixeldigest`.

### Linhas 6 a 11

```python
from .clickup import ClickUpConector
from .demo import EMPRESAS_DEMO, DemoConector
from .google import GmailConector
from .microsoft import MicrosoftConector
from .slack import SlackConector
from .zoom import ZoomConector
```

Importa a classe de cada conector e as empresas de exemplo da demonstração.

### Linhas 13 a 19

```python
TIPOS = {
    "slack": SlackConector,
    "clickup": ClickUpConector,
    "gmail": GmailConector,
    "microsoft": MicrosoftConector,   # Outlook + Teams
    "zoom": ZoomConector,             # reuniões agendadas no Zoom
}
```

Dicionário que liga o nome do tipo (o que está no YAML) à classe que sabe falar com aquele serviço. Isso evita uma sequência enorme de `if tipo == ...`: basta procurar no dicionário.

### Linha 22

```python
def montar(cfg):
```

Função que monta os conectores.

### Linhas 23 a 27

```python
    """Devolve (conectores, erros). No modo demo, usa empresas inventadas.

    Um conector mal configurado (ex.: token faltando no .env) vira um erro na
    lista, mas não impede os outros de funcionarem.
    """
```

Docstring: devolve os conectores e os erros. Um conector mal configurado vira um erro na lista, mas os outros continuam funcionando.

### Linhas 28 a 30

```python
    if cfg.get("demo"):
        cfg["empresas"] = EMPRESAS_DEMO
        return [DemoConector(emp["nome"], con, cfg) for emp in EMPRESAS_DEMO for con in emp["conectores"]], []
```

No modo demonstração, troca as empresas pelas de exemplo e cria um `DemoConector` para cada serviço delas (comprehension com dois `for`). Não há erros possíveis, então devolve lista vazia de erros.

### Linha 31

```python
    conectores, erros = [], []
```

Começa as duas listas.

### Linhas 32 a 34

```python
    for emp in cfg["empresas"]:
        if emp.get("ativa", True) is False:      # empresa desligada nas Configurações
            continue
```

Pula empresas desligadas. O `is False` só pula quando o valor é exatamente `False`; se a chave não existir, o padrão `True` mantém a empresa.

### Linhas 35 a 37

```python
        for con in emp["conectores"]:
            try:
                conectores.append(TIPOS[con["tipo"]](emp["nome"], con, cfg))
```

Para cada serviço da empresa, procura a classe no dicionário `TIPOS` e cria o objeto com o nome da empresa, as opções do serviço e a configuração inteira.

### Linhas 38 a 39

```python
            except ConfigError as exc:
                erros.append(f"{emp['nome']} / {con['tipo']}: {exc}")
```

Se o construtor do conector lançar `ConfigError` (ex.: falta o token), guarda o erro com empresa e tipo, e segue para o próximo.

### Linha 40

```python
    return conectores, erros
```

Devolve as duas listas.
