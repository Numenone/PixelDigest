# `pixeldigest/models.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/models.py)

Define os formatos de dados comuns do programa. Cada conector converte o JSON da sua API para estes objetos; o resto do código (resumo, tela, notificações) só conhece estes formatos e não precisa saber se algo veio do Slack ou do Gmail.

### Linhas 1 a 6

```python
"""Formatos de dados que circulam no programa.

Todo conector (Slack, ClickUp, Gmail, Outlook, Teams...) converte o JSON da sua API
para estes mesmos formatos. Assim o resto do programa não precisa saber de onde
cada coisa veio.
"""
```

Docstring explicando a ideia do formato comum.

### Linha 7

```python
from dataclasses import asdict, dataclass, field
```

Importa ferramentas de `dataclasses`: o decorador `dataclass` (cria automaticamente construtor, `repr` e comparação a partir dos campos), `asdict` (converte o objeto em dicionário) e `field` (para valores padrão especiais, como listas).

### Linha 8

```python
from datetime import datetime
```

Importa `datetime` para os campos de data e hora.

### Linhas 10 a 11

```python
# Prioridades usadas para ordenar o resumo
BAIXA, NORMAL, ALTA, URGENTE = 0, 1, 2, 3
```

Constantes de prioridade. A atribuição múltipla dá 0, 1, 2 e 3 para BAIXA, NORMAL, ALTA e URGENTE. Números permitem ordenar (maior aparece primeiro).

### Linha 14

```python
@dataclass
```

O decorador `@dataclass` transforma a classe abaixo numa classe de dados.

### Linhas 15 a 16

```python
class Item:
    """Uma coisa que merece atenção: tarefa, mensagem, e-mail ou evento da agenda."""
```

Classe `Item`: qualquer coisa que merece atenção (tarefa, mensagem, e-mail ou evento).

### Linhas 17 a 20

```python
    empresa: str
    fonte: str            # slack, clickup, gmail, google_agenda, outlook, teams, agenda
    tipo: str             # tarefa, mensagem, email, evento
    titulo: str
```

Campos obrigatórios (sem valor padrão): empresa, fonte (de qual serviço veio), tipo e título. A anotação `: str` indica o tipo esperado.

### Linha 21

```python
    detalhe: str = ""
```

Detalhe opcional (ex.: "ATRASADA", nome do canal). Padrão: texto vazio.

### Linha 22

```python
    quando: datetime | None = None
```

Quando acontece (prazo, horário do evento, hora da mensagem). `datetime | None` quer dizer "um datetime ou nada".

### Linha 23

```python
    url: str = ""
```

Link para abrir o item na ferramenta original.

### Linha 24

```python
    prioridade: int = NORMAL
```

Prioridade, com padrão NORMAL.

### Linha 25

```python
    id: str = ""          # identificador na origem (usado para não avisar duas vezes)
```

Identificador do item na origem. Serve para não avisar duas vezes sobre a mesma coisa.

### Linhas 27 a 28

```python
    def chave(self):
        return f"{self.fonte}:{self.id or self.titulo}"
```

Método `chave`: monta um texto único para o item, como "slack:1699999.123". Se não houver id, usa o título. É usado para lembrar o que já foi avisado ou apagado.

### Linhas 30 a 33

```python
    def to_dict(self):
        d = asdict(self)
        d["quando"] = self.quando.isoformat() if self.quando else None
        return d
```

Converte o item em dicionário para salvar em JSON. O JSON não entende `datetime`, então a data é convertida para texto no padrão ISO ("2026-11-06T07:00:00").

### Linhas 36 a 38

```python
@dataclass
class Clima:
    """Clima atual e do dia (vem do Open-Meteo)."""
```

Classe de dados do clima, preenchida com o que vem da API Open-Meteo.

### Linhas 39 a 48

```python
    cidade: str
    temperatura: float
    minima: float
    maxima: float
    chuva_mm: float           # chuva na última hora
    prob_chuva: int           # % de chance de chuva na próxima hora
    nuvens: int               # % do céu coberto
    codigo: int               # código WMO do tempo
    descricao: str
    vento_kmh: float
```

Campos do clima: cidade, temperatura atual, mínima e máxima do dia, chuva da última hora em milímetros, chance de chuva, porcentagem de nuvens, código WMO (padrão internacional: 0 céu limpo, 61 chuva, 95 trovoada etc.), descrição em português e vento.

### Linhas 49 a 50

```python
    nascer: datetime | None = None
    por_do_sol: datetime | None = None
```

Horários de nascer e pôr do sol (opcionais). O cenário usa para decidir quando é dia e noite.

### Linha 51

```python
    proximas: list = field(default_factory=list)   # próximas horas: [(hora, temp, código, % chuva)]
```

Previsão das próximas horas. `field(default_factory=list)` cria uma lista nova para cada objeto. Não dá para escrever `= []` direto, porque todos os objetos acabariam dividindo a mesma lista.

### Linhas 53 a 57

```python
    @property
    def intensidade_chuva(self):
        """0 = seco, 1 = tempestade. Controla a quantidade de gotas e o escuro da tela."""
        from .connectors.weather import intensidade
        return intensidade(self.codigo, self.chuva_mm)
```

`@property` deixa chamar `clima.intensidade_chuva` sem parênteses, como se fosse um campo, mas o valor é calculado: um número de 0 (seco) a 1 (tempestade) a partir do código e dos milímetros. O import fica dentro da função para evitar import circular (o módulo weather também importa este).

### Linhas 59 a 61

```python
    @property
    def trovoada(self):
        return self.codigo >= 95
```

Outra propriedade: é trovoada quando o código WMO é 95 ou mais.

### Linhas 63 a 68

```python
    def to_dict(self):
        d = asdict(self)
        d["nascer"] = self.nascer.isoformat() if self.nascer else None
        d["por_do_sol"] = self.por_do_sol.isoformat() if self.por_do_sol else None
        d["intensidade_chuva"] = round(self.intensidade_chuva, 2)
        return d
```

Converte o clima em dicionário para o JSON: datas viram texto ISO e a intensidade calculada é incluída, arredondada para 2 casas.

### Linhas 71 a 76

```python
@dataclass
class Horario:
    """Um horário livre sugerido para reunião."""
    inicio: datetime
    fim: datetime
    confianca: float = 100.0
```

Classe `Horario`: um horário livre sugerido para reunião, com início, fim e a confiança (o Microsoft Graph devolve uma porcentagem de chance de todos poderem).

### Linhas 79 a 87

```python
@dataclass
class PedidoReuniao:
    """Alguém pediu reunião no Teams."""
    empresa: str
    chat_id: str
    pessoa: str
    email: str
    texto: str
    horarios: list = field(default_factory=list)
```

Classe `PedidoReuniao`: guarda um pedido de reunião recebido no Teams: empresa, conversa, nome e e-mail da pessoa, o texto da mensagem e os horários sugeridos.

### Linhas 90 a 96

```python
@dataclass
class Digest:
    """O resumo do dia inteiro: itens de todas as empresas + clima + falhas."""
    gerado_em: datetime
    itens: list
    clima: Clima | None = None
    erros: list = field(default_factory=list)   # fontes que falharam (o resumo sai mesmo assim)
```

Classe `Digest`: o resumo do dia inteiro. Tem a hora em que foi gerado, a lista de itens, o clima e a lista de erros. Os erros são as fontes que falharam; o resumo sai mesmo assim com o resto.

### Linhas 98 a 102

```python
    def por_empresa(self):
        grupos = {}
        for it in self.itens:
            grupos.setdefault(it.empresa, []).append(it)
        return grupos
```

Agrupa os itens por empresa num dicionário `{"Acme": [itens...]}`. `setdefault` cria a lista vazia na primeira vez que a empresa aparece.

### Linhas 104 a 110

```python
    def to_dict(self):
        return {
            "gerado_em": self.gerado_em.isoformat(),
            "clima": self.clima.to_dict() if self.clima else None,
            "erros": self.erros,
            "itens": [i.to_dict() for i in self.itens],
        }
```

Converte o resumo inteiro para dicionário (é isso que vai para o arquivo `data/digest-AAAA-MM-DD.json`). Cada item e o clima usam o próprio `to_dict`.
