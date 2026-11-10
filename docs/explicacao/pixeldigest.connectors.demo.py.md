# `pixeldigest/connectors/demo.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/connectors/demo.py)

Modo demonstração: dados inventados, sem nenhuma conta real. Serve para o GitHub público e para a apresentação, mostrando o programa inteiro funcionando sem expor dados de empresa nenhuma.

### Linhas 1 a 5

```python
"""Modo demonstração: dados inventados, sem nenhuma conta real.

Serve para o GitHub público e para a apresentação: mostra tudo funcionando sem
expor clientes nem mensagens de empresa nenhuma. Ative com --demo.
"""
```

Docstring: para que serve e como ativar (`--demo`).

### Linha 6

```python
from datetime import datetime, timedelta
```

Importa `datetime` e `timedelta`.

### Linhas 8 a 9

```python
from ..models import ALTA, NORMAL, URGENTE, Horario, Item
from .base import Conector
```

Importa as prioridades, `Horario`, `Item` e a base.

### Linhas 11 a 16

```python
EMPRESAS_DEMO = [
    {"nome": "Acme Ltda", "cor": "#4fa3ff",
     "conectores": [{"tipo": "slack"}, {"tipo": "clickup"}, {"tipo": "gmail"}]},
    {"nome": "Contoso", "cor": "#7ad67a",
     "conectores": [{"tipo": "microsoft", "agendador": True}]},
]
```

Duas empresas fictícias: "Acme Ltda" (Slack, ClickUp, Gmail) e "Contoso" (Microsoft com agendador). Os nomes são exemplos clássicos usados em documentação.

### Linhas 19 a 20

```python
class DemoConector(Conector):
    """Finge ser um conector real do tipo pedido."""
```

Classe que finge ser o conector do tipo pedido.

### Linhas 22 a 23

```python
    def __init__(self, empresa, opcoes, cfg):
        super().__init__(empresa, opcoes, cfg)
```

Construtor; chama o da base.

### Linha 24

```python
        self.tipo = opcoes.get("tipo", "demo")
```

O tipo vem das opções ("slack", "gmail"...), então o resto do programa trata o conector como se fosse o real.

### Linha 25

```python
        self.usar = {"agendador": opcoes.get("agendador", self.tipo == "microsoft")}
```

O agendador fica ligado no tipo Microsoft.

### Linha 26

```python
        self.email = f"voce@{empresa.split()[0].lower()}.example" if self.tipo == "gmail" else ""
```

E-mail fictício para o tipo Gmail, como "voce@acme.example" (o domínio `.example` é reservado para exemplos e não existe).

### Linha 27

```python
        agora = datetime.now().timestamp()
```

Hora atual em segundos.

### Linhas 28 a 38

```python
        # e-mails de exemplo para o "resumo dos e-mails" da demonstração
        self.mensagens = [
            {"id": "d1", "de": "Financeiro", "assunto": "Nota fiscal de outubro", "quando": agora - 3600,
             "texto": "Oi! Segue a nota fiscal de outubro. Precisamos da aprovação até sexta para pagar o fornecedor.",
             "nao_lido": True, "importante": True},
            {"id": "d2", "de": "Cliente Atlas", "assunto": "Proposta revisada", "quando": agora - 7200,
             "texto": "Recebemos a proposta, mas queremos rever o prazo de entrega. Podemos conversar amanhã?",
             "nao_lido": True, "importante": True},
            {"id": "d3", "de": "Newsletter", "assunto": "Novidades da semana", "quando": agora - 9000,
             "texto": "As 10 notícias mais lidas da semana.", "nao_lido": False, "importante": False},
        ] if self.tipo == "gmail" else []
```

Três e-mails de exemplo (só no tipo Gmail) para o resumo de e-mails da demonstração: nota fiscal com prazo, cliente pedindo conversa e uma newsletter. O formato é o mesmo que o conector real do Gmail produz.

### Linha 40

```python
    def coletar(self):
```

Itens de exemplo.

### Linha 41

```python
        hoje = self.inicio_do_dia()
```

Meia-noite de hoje.

### Linha 42

```python
        h = lambda horas, minutos=0: hoje + timedelta(hours=horas, minutes=minutos)  # noqa: E731
```

Função curta que devolve hoje mais X horas e Y minutos. O comentário `noqa: E731` silencia o aviso do verificador de estilo sobre atribuir `lambda` a uma variável.

### Linha 43

```python
        e = self.empresa
```

Atalho para o nome da empresa.

### Linhas 44 a 64

```python
        dados = {
            "slack": [
                Item(e, "slack", "mensagem", "Marina: @voce consegue revisar o fluxo de onboarding hoje?", "#operacoes", h(8, 42), prioridade=URGENTE, id="s1"),
                Item(e, "slack", "mensagem", "Rafael: subi a nova versão do relatório", "#dados", h(9, 10), id="s2"),
            ],
            "clickup": [
                Item(e, "clickup", "tarefa", "Enviar proposta para o cliente Atlas", "ATRASADA", h(-6), prioridade=URGENTE, id="c1"),
                Item(e, "clickup", "tarefa", "Configurar automação de boas-vindas", "em andamento", h(17), prioridade=ALTA, id="c2"),
                Item(e, "clickup", "tarefa", "Atualizar planilha de métricas", "a fazer", h(40), id="c3"),
            ],
            "gmail": [
                Item(e, "gmail", "email", "Financeiro: nota fiscal de outubro", "Segue em anexo a nota...", h(7, 55), prioridade=ALTA, id="g1"),
                Item(e, "gmail", "email", "Newsletter: novidades da semana", "", h(6, 30), prioridade=NORMAL, id="g2"),
            ],
            "microsoft": [
                Item(e, "outlook", "evento", "Daily do time", "Teams", h(9, 30), prioridade=ALTA, id="o1"),
                Item(e, "outlook", "evento", "Planejamento do trimestre", "Teams", h(15), prioridade=ALTA, id="o2"),
                Item(e, "teams", "mensagem", "Beatriz: vamos marcar uma call pra alinhar o projeto?", "chat", h(10, 5), prioridade=URGENTE, id="t1"),
                Item(e, "outlook", "email", "RH: confirmação do benefício", "", h(8, 15), id="o3"),
            ],
        }
```

Dicionário com os itens de cada tipo: mensagens do Slack (uma com menção, urgente), tarefas do ClickUp (uma atrasada), e-mails do Gmail e eventos, mensagem e e-mail da Microsoft. Os campos são passados na ordem da classe `Item` (empresa, fonte, tipo, título, detalhe, quando).

### Linha 65

```python
        return dados.get(self.tipo, [])
```

Devolve os itens do tipo deste conector.

### Linha 67

```python
    # ----- mesmas funções do MicrosoftConector, com respostas falsas -----
```

Comentário: as mesmas funções do conector Microsoft, com respostas falsas, para o agendador funcionar na demonstração.

### Linhas 68 a 69

```python
    def precisa_login(self):
        return False
```

Nunca precisa de login.

### Linhas 71 a 72

```python
    def mensagens_novas(self, desde):
        return []
```

Nenhuma mensagem nova no Teams (o pedido da demonstração é disparado por tecla).

### Linhas 74 a 75

```python
    def email_de(self, user_id):
        return "beatriz@contoso.example"
```

E-mail fixo de quem pediu reunião.

### Linhas 77 a 79

```python
    def buscar_pessoa(self, nome):
        nome = nome.strip().title()
        return [(f"{nome} Souza", f"{nome.lower().split()[0]}@contoso.example")]
```

Busca de pessoa: devolve o nome digitado com "Souza" e um e-mail fictício.

### Linha 81

```python
    def horarios_livres(self, email, minutos, janelas, maximo=3):
```

Finge a resposta do `findMeetingTimes`.

### Linha 82

```python
        """Finge a resposta do Outlook: horários dentro das janelas pedidas."""
```

Docstring.

### Linhas 83 a 88

```python
        if not janelas:      # sem janelas (só usado para imagens): próximo dia útil
            dia = self.agora() + timedelta(days=1)
            while dia.weekday() >= 5:
                dia += timedelta(days=1)
            base = dia.replace(hour=9, minute=0, second=0, microsecond=0)
            janelas = [(base, base.replace(hour=18))]
```

Sem janelas (caso usado só para gerar imagens): usa o próximo dia útil das 9h às 18h. O `while` pula sábado e domingo.

### Linha 89

```python
        candidatos = []
```

Lista de candidatos.

### Linhas 90 a 91

```python
        for n, (ini, fim) in enumerate(janelas):
            opcoes = [(60, 330, 150), (330, 150, 60), (150, 60, 330)][n % 3]   # varia o horário de cada dia
```

Para cada janela, escolhe deslocamentos em minutos que variam de um dia para o outro (resto da divisão por 3), para as sugestões não ficarem sempre no mesmo horário.

### Linha 92

```python
            for desloc in ((0,) if len(janelas) == 1 and fim - ini <= timedelta(hours=4) else opcoes):
```

Se foi pedida uma hora exata (uma janela curta só), usa só o início dela.

### Linhas 93 a 95

```python
                inicio = ini + timedelta(minutes=desloc)
                if inicio + timedelta(minutes=minutos) <= fim:
                    candidatos.append(Horario(inicio, inicio + timedelta(minutes=minutos)))
```

Se a reunião cabe na janela, vira um candidato.

### Linhas 96 a 98

```python
        if not candidatos:
            from .. import net
            raise net.ApiError("Microsoft", "nenhum horário livre (demo)")
```

Sem candidatos, simula o erro do Outlook.

### Linhas 99 a 100

```python
        from .microsoft import espalhar
        return espalhar(candidatos, maximo)
```

Usa a mesma função `espalhar` do conector real.

### Linhas 102 a 103

```python
    def agendar(self, email, nome, horario, assunto):
        return "https://teams.microsoft.com/l/meetup-join/demo"
```

Agendar devolve um link fictício do Teams.

### Linhas 105 a 106

```python
    def responder(self, chat_id, texto_html):
        pass
```

Responder não faz nada (`pass`).

### Linhas 109 a 112

```python
def pedido_demo(agora: datetime):
    """Mensagem falsa de alguém pedindo reunião (tecla F4 na demonstração)."""
    return {"chat_id": "demo-chat", "user_id": "demo-user", "nome": "Beatriz Lima",
            "texto": "Oi! Podemos marcar uma reunião essa semana pra alinhar o projeto?"}
```

Monta a mensagem falsa de alguém pedindo reunião, usada no atalho da demonstração. Tem o mesmo formato das mensagens reais que o conector Microsoft devolve.
