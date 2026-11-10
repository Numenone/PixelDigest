# `pixeldigest/meetings.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/meetings.py)

Agendador de reuniões. Reconhece pedidos de reunião em mensagens do Teams, interpreta comandos digitados como "reunião com Ana amanhã 45min sobre orçamento" e calcula as janelas de expediente em que a reunião pode acontecer.

### Linhas 1 a 9

```python
"""Agendador de reuniões (Teams/Outlook).

Dois caminhos:
1. Alguém escreve no Teams "podemos marcar uma reunião?" -> eh_pedido() reconhece,
   o Agendador busca horários livres para os dois e sugere (na tela, no celular,
   no Discord e, se ligado, respondendo no próprio chat).
2. Você digita "reunião com Ana amanhã 45min sobre orçamento" -> interpretar()
   separa pessoa, dia, duração e assunto; o Agendador acha a pessoa e os horários.
"""
```

Docstring com os dois caminhos de uso: pedido recebido no Teams e comando digitado na tela.

### Linha 10

```python
import re
```

Importa `re` (expressões regulares), que é a base de toda a interpretação de texto deste arquivo.

### Linha 11

```python
import unicodedata
```

Importa `unicodedata`, usado para tirar acentos.

### Linha 12

```python
from datetime import date, datetime, time, timedelta
```

Importa `date` (só data), `datetime` (data e hora), `time` (só hora) e `timedelta` (diferença).

### Linha 14

```python
from . import net
```

Importa `net` para reconhecer o `ApiError`.

### Linha 15

```python
from .models import Horario, PedidoReuniao
```

Importa as classes `Horario` e `PedidoReuniao`.

### Linha 17

```python
DIAS_SEMANA = {"segunda": 0, "terca": 1, "quarta": 2, "quinta": 3, "sexta": 4, "sabado": 5, "domingo": 6}
```

Dicionário dos dias da semana (sem acento) para o número usado pelo Python, onde segunda é 0 e domingo é 6.

### Linha 18

```python
NOMES_DIA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
```

Abreviações dos dias, na mesma ordem, para mostrar os horários.

### Linhas 19 a 20

```python
INTENCAO = re.compile(r"\b(podemos|podemo|vamos|bora|consegue|conseguimos|pode|poderia|tem (um )?tempo|"
                      r"marcar|agendar|disponivel|livre|horario)\b")
```

Expressão regular pré-compilada (`re.compile`, mais rápida quando usada muitas vezes) com palavras que indicam intenção de marcar algo: "podemos", "vamos", "bora", "consegue", "marcar", "agendar", "livre", "horario" etc. O `\b` exige limite de palavra (não pega "marcar" dentro de "desmarcaram", por exemplo). `(um )?` torna o "um" opcional em "tem um tempo". As duas strings `r"..."` seguidas são juntadas automaticamente pelo Python.

### Linha 23

```python
def normalizar(texto):
```

Função que normaliza um texto para comparação.

### Linha 24

```python
    """Minúsculas e sem acento, para comparar palavras: 'Reunião' -> 'reuniao'."""
```

Docstring com exemplo.

### Linha 25

```python
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
```

`normalize("NFKD", ...)` separa a letra do acento ("ã" vira "a" + til). Depois `encode("ascii", "ignore")` joga fora tudo o que não é ASCII (os acentos soltos) e `decode()` volta para texto.

### Linha 26

```python
    return " ".join(sem_acento.lower().split())
```

Passa para minúsculas e junta as palavras com um espaço só (`split()` sem argumento separa por qualquer espaço e ignora espaços repetidos).

### Linha 29

```python
def eh_pedido(texto, palavras):
```

Decide se uma mensagem é um pedido de reunião.

### Linhas 30 a 35

```python
    """True se a mensagem parece um pedido de reunião.

    Precisa ter uma palavra de reunião (configurável no YAML) E uma intenção
    (pergunta ou verbo como 'marcar', 'podemos'). Assim 'a reunião foi ótima'
    não dispara, mas 'podemos fazer uma call?' dispara.
    """
```

Docstring explicando a regra dupla: precisa de uma palavra de reunião e de uma intenção. Com exemplos do que dispara e do que não dispara.

### Linha 36

```python
    t = normalizar(texto)
```

Normaliza a mensagem.

### Linha 37

```python
    tem_palavra = any(re.search(rf"\b{re.escape(normalizar(p))}\b", t) for p in palavras)
```

`any(...)` devolve `True` se ao menos uma das palavras configuradas aparece como palavra inteira. `re.escape` protege caracteres especiais da palavra e `rf"..."` é uma string bruta com f-string, para montar a expressão com `\b` em volta.

### Linha 38

```python
    tem_intencao = "?" in texto or bool(INTENCAO.search(t))
```

Tem intenção se a mensagem original tem ponto de interrogação ou se a expressão de intenção encontrou algo. `bool(...)` converte o resultado da busca (objeto ou `None`) para `True`/`False`.

### Linha 39

```python
    return tem_palavra and tem_intencao
```

É pedido só se as duas condições forem verdadeiras.

### Linha 42

```python
def _plano(texto):
```

Função interna que tira acentos mantendo o tamanho do texto.

### Linhas 43 a 46

```python
    """Tira acentos SEM mudar o tamanho do texto (cada letra continua no mesmo lugar).

    Assim dá para procurar 'amanha' no texto plano e cortar a mesma posição do original.
    """
```

Docstring explicando o motivo: procuramos padrões no texto sem acento, mas cortamos o texto original nas mesmas posições. Para isso, cada letra precisa continuar no mesmo lugar.

### Linha 47

```python
    return "".join(unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode() or c for c in texto).lower()
```

Trata letra por letra: tira o acento de cada uma; se a letra sumir por inteiro (algum símbolo sem versão ASCII), o `or c` mantém a original. Junta tudo e passa para minúsculas.

### Linhas 50 a 51

```python
def _cortar(texto, m):
    return texto[:m.start()] + " " + texto[m.end():]
```

Remove do texto o trecho encontrado pela busca `m`, colocando um espaço no lugar. `m.start()` e `m.end()` são as posições de início e fim do trecho.

### Linha 54

```python
def _dia_semana(hoje, numero):
```

Calcula a próxima data de um dia da semana.

### Linha 55

```python
    """Próxima ocorrência do dia da semana (se hoje é quinta, 'quinta' = semana que vem)."""
```

Docstring: se hoje é quinta e o comando diz "quinta", vale a quinta da semana que vem.

### Linha 56

```python
    return hoje + timedelta(days=(numero - hoje.weekday()) % 7 or 7)
```

`(numero - hoje.weekday()) % 7` dá quantos dias faltam (o resto da divisão por 7 resolve a volta da semana). Se der 0 (é hoje), o `or 7` troca por 7.

### Linha 59

```python
def _data(hoje, m):
```

Converte uma data no formato "12/11" encontrada no texto.

### Linha 60

```python
    dia = date(hoje.year, int(m.group(2)), int(m.group(1)))
```

Monta a data com o ano atual, o mês (grupo 2) e o dia (grupo 1).

### Linha 61

```python
    return dia if dia >= hoje else date(hoje.year + 1, dia.month, dia.day)
```

Se a data já passou este ano, usa a mesma data no ano que vem.

### Linhas 64 a 72

```python
# (padrão no texto sem acento, como calcular o dia)
PADROES_DIA = [
    (r"\bdepois de amanha\b", lambda hoje, m: hoje + timedelta(days=2)),
    (r"\bamanha\b", lambda hoje, m: hoje + timedelta(days=1)),
    (r"\bhoje\b", lambda hoje, m: hoje),
    (r"\b(\d{1,2})/(\d{1,2})\b", _data),
    (r"\b(?:na |no |nesta |nessa |proxima |proximo )?(segunda|terca|quarta|quinta|sexta|sabado|domingo)(?:-feira| feira)?\b",
     lambda hoje, m: _dia_semana(hoje, DIAS_SEMANA[m.group(1)])),
]
```

Lista de padrões de dia, cada um com a função que calcula a data. A ordem importa: "depois de amanhã" vem antes de "amanhã", senão o "amanhã" seria encontrado primeiro. As funções `lambda hoje, m: ...` recebem a data de hoje e o resultado da busca. O último padrão aceita formas como "na sexta", "próxima segunda-feira", e o `(?:...)` é um grupo que não captura (só agrupa).

### Linha 75

```python
def interpretar(comando, hoje, duracao_padrao=30):
```

Interpreta o comando digitado e devolve um dicionário com pessoa, dia, hora, duração e assunto.

### Linhas 76 a 79

```python
    """'reunião com Ana amanhã 45min sobre orçamento' -> dict com os pedaços.

    Devolve None se não for um comando de reunião.
    """
```

Docstring com exemplo; devolve `None` se o texto não for um comando de reunião.

### Linha 80

```python
    m = re.match(r"^\s*(?:marcar\s+|agendar\s+)?(?:uma\s+)?(?:reuniao|call|meet)\s+com\s+", _plano(comando))
```

Confere se o texto começa com "reunião com", "call com", "meet com", aceitando antes "marcar", "agendar" e "uma". `re.match` só procura no começo do texto. `\s+` é um ou mais espaços.

### Linhas 81 a 82

```python
    if not m:
        return None
```

Se não começa assim, não é comando.

### Linha 83

```python
    resto = comando[m.end():]
```

Guarda o resto do texto, depois do "com ". Usa o texto original (com acentos), cortando na posição encontrada no texto plano.

### Linha 85

```python
    # assunto: tudo depois de "sobre"
```

Comentário: primeiro tiramos o assunto.

### Linhas 86 a 89

```python
    assunto = ""
    s = re.search(r"\s+sobre\s+", _plano(resto))
    if s:
        resto, assunto = resto[:s.start()], resto[s.end():]
```

Procura " sobre ". Se achar, o que vem antes continua em `resto` e o que vem depois é o assunto. Tirar o assunto primeiro evita confundir palavras dele com dia ou duração.

### Linha 91

```python
    # horário exato: "às 14h", "as 9:30", "às 15h30"
```

Comentário com exemplos de horário exato.

### Linhas 92 a 93

```python
    hora = None
    h = re.search(r"\b(?:as|a partir das)\s+(\d{1,2})(?:[:h](\d{2}))?h?\b", _plano(resto))
```

Procura "às 14h", "as 9:30", "a partir das 15h30". O grupo 1 é a hora e o grupo 2 (opcional) são os minutos.

### Linhas 94 a 96

```python
    if h and int(h.group(1)) < 24:
        hora = time(int(h.group(1)), int(h.group(2) or 0))
        resto = _cortar(resto, h)
```

Se achou e a hora é válida (menor que 24), cria o `time` (minutos 0 se não vieram) e remove o trecho do texto.

### Linha 98

```python
    # duração: "45min", "1h", "90 minutos"
```

Comentário com exemplos de duração.

### Linha 99

```python
    duracao = duracao_padrao
```

Começa com a duração padrão da configuração.

### Linha 100

```python
    d = re.search(r"\b(\d+)\s*(min|minutos?|m|h|horas?)\b", _plano(resto))
```

Procura um número seguido de unidade: "45min", "1h", "90 minutos", "2 horas".

### Linhas 101 a 104

```python
    if d:
        valor = int(d.group(1))
        duracao = valor * 60 if d.group(2).startswith("h") else valor
        resto = _cortar(resto, d)
```

Se achou: se a unidade começa com "h", multiplica por 60 para virar minutos; senão usa o número como minutos. Remove o trecho.

### Linha 106

```python
    # dia: hoje, amanhã, depois de amanhã, 12/11, sexta-feira...
```

Comentário dos formatos de dia aceitos.

### Linhas 107 a 113

```python
    dia = None
    for padrao, calcular in PADROES_DIA:
        achou = re.search(padrao, _plano(resto))
        if achou:
            dia = calcular(hoje, achou)
            resto = _cortar(resto, achou)
            break
```

Testa cada padrão de dia na ordem. No primeiro que encontrar, calcula a data, remove o trecho e para o laço com `break`.

### Linha 115

```python
    # O que sobrou é o nome da pessoa (tira preposições soltas no fim)
```

Comentário: o que sobrou é o nome da pessoa.

### Linha 116

```python
    pessoa = " ".join(resto.split())
```

Junta as palavras restantes com um espaço só.

### Linha 117

```python
    pessoa = re.sub(r"\s+(de|da|do|na|no|para|pra|as|às|em)$", "", pessoa, flags=re.I).strip(" ,.")
```

Remove preposições soltas no fim (ex.: "Ana de" vira "Ana"). `flags=re.I` ignora maiúsculas e minúsculas. `strip(" ,.")` tira espaços, vírgulas e pontos das pontas.

### Linhas 118 a 119

```python
    if not pessoa:
        return None
```

Se não sobrou nome, o comando está incompleto.

### Linhas 120 a 121

```python
    return {"pessoa": pessoa, "dia": dia, "hora": hora, "duracao": duracao,
            "assunto": assunto.strip() or f"Reunião com {pessoa}"}
```

Devolve o dicionário. Se o assunto estiver vazio, usa "Reunião com <pessoa>".

### Linha 124

```python
def janelas(cfg, fuso, agora, dias=3, dia_especifico=None):
```

Calcula as janelas de expediente onde a reunião pode acontecer.

### Linhas 125 a 128

```python
    """Janelas de expediente onde a reunião pode acontecer.

    Pula fim de semana e nunca sugere nada a menos de 30 minutos de agora.
    """
```

Docstring: pula fim de semana e nunca sugere nada a menos de 30 minutos de agora.

### Linha 129

```python
    ini_exp, fim_exp = cfg["horarios"]["expediente"]
```

Pega o início e o fim do expediente.

### Linha 130

```python
    candidatos = [dia_especifico] if dia_especifico else [agora.date() + timedelta(days=i) for i in range(14)]
```

Se foi pedido um dia específico, só ele; senão, os próximos 14 dias.

### Linha 131

```python
    resultado = []
```

Lista de janelas.

### Linhas 132 a 134

```python
    for dia in candidatos:
        if dia.weekday() >= 5 and not dia_especifico:
            continue
```

Pula sábado (5) e domingo (6), a menos que o dia tenha sido pedido explicitamente.

### Linha 135

```python
        ini = max(datetime.combine(dia, ini_exp, fuso), agora + timedelta(minutes=30))
```

O início da janela é o mais tarde entre o começo do expediente e "agora mais 30 minutos". `datetime.combine` junta data, hora e fuso.

### Linha 136

```python
        fim = datetime.combine(dia, fim_exp, fuso)
```

Fim da janela: fim do expediente.

### Linhas 137 a 139

```python
        # arredonda o início para o próximo múltiplo de 30 min
        if ini.minute % 30 or ini.second:
            ini = ini.replace(second=0, microsecond=0) + timedelta(minutes=30 - ini.minute % 30)
```

Se o início não cai num múltiplo de 30 minutos, arredonda para cima (ex.: 14:07 vira 14:30). Primeiro zera segundos e microssegundos e depois soma o que falta.

### Linhas 140 a 141

```python
        if ini < fim:
            resultado.append((ini, fim))
```

Só guarda a janela se ainda sobrar tempo no dia.

### Linhas 142 a 143

```python
        if len(resultado) == dias:
            break
```

Para quando já tem a quantidade de dias pedida.

### Linha 144

```python
    return resultado
```

Devolve as janelas.

### Linhas 147 a 149

```python
def rotulo(h: Horario, hoje=None):
    """Horario -> 'qui 07/11 14:30'."""
    return f"{NOMES_DIA[h.inicio.weekday()]} {h.inicio:%d/%m %H:%M}"
```

Formata um horário como "qui 07/11 14:30": abreviação do dia pela posição na lista e data e hora formatadas. A anotação `h: Horario` só documenta o tipo esperado.

### Linha 152

```python
class Agendador:
```

Classe que junta tudo para marcar reuniões.

### Linhas 153 a 156

```python
    def __init__(self, cfg, conector):
        self.cfg = cfg
        self.conector = conector      # MicrosoftConector (ou DemoConector)
        self.r = cfg["reunioes"]
```

Guarda a configuração, o conector (Microsoft de verdade ou o da demonstração; os dois têm os mesmos métodos) e a parte de reuniões da configuração.

### Linha 158

```python
    def _horarios(self, email, duracao, dia=None, hora=None):
```

Busca horários livres para a pessoa.

### Linha 159

```python
        agora = self.conector.agora()
```

Hora atual no fuso do conector.

### Linhas 160 a 162

```python
        if hora:
            # Pediu horário exato: testa só aquele horário; se alguém estiver ocupado,
            # cai para os horários livres do mesmo dia.
```

Se foi pedida uma hora exata, testa só aquele horário. O comentário explica o plano B.

### Linha 163

```python
            inicio = datetime.combine(dia or agora.date(), hora, self.conector.fuso)
```

Monta o início com o dia pedido (ou hoje) e a hora.

### Linhas 164 a 165

```python
            try:
                return self.conector.horarios_livres(email, duracao, [(inicio, inicio + timedelta(minutes=duracao))], 1)
```

Pede ao conector para conferir só esse intervalo, devolvendo no máximo 1 horário.

### Linhas 166 a 167

```python
            except net.ApiError:
                dia = inicio.date()
```

Se o horário estiver ocupado (o conector lança erro), cai para os horários livres desse mesmo dia.

### Linha 168

```python
        jan = janelas(self.cfg, self.conector.fuso, agora, self.r["dias_para_frente"], dia)
```

Calcula as janelas.

### Linhas 169 a 170

```python
        if not jan:
            raise ValueError("esse dia já passou ou não tem horário de expediente")
```

Sem janelas, explica o motivo.

### Linha 171

```python
        return self.conector.horarios_livres(email, duracao, jan)
```

Pede ao conector os horários livres dos dois dentro das janelas.

### Linha 173

```python
    def de_comando(self, texto):
```

Trata um comando digitado.

### Linha 174

```python
        """Comando digitado na tela -> proposta com 3 horários."""
```

Docstring.

### Linha 175

```python
        pedido = interpretar(texto, self.conector.agora().date(), self.r["duracao_padrao"])
```

Interpreta o texto usando a data de hoje e a duração padrão.

### Linhas 176 a 177

```python
        if not pedido:
            raise ValueError("não entendi. Exemplo: reunião com Ana amanhã 45min sobre orçamento")
```

Se não entendeu, mostra um exemplo do formato certo.

### Linha 178

```python
        pessoas = self.conector.buscar_pessoa(pedido["pessoa"])
```

Procura a pessoa pelo nome nos contatos do Teams.

### Linhas 179 a 180

```python
        if not pessoas:
            raise ValueError(f"não achei '{pedido['pessoa']}' nos seus contatos do Teams")
```

Se não achou, avisa.

### Linha 181

```python
        nome, email = pessoas[0]
```

Pega nome e e-mail do primeiro resultado (desempacotando a tupla).

### Linha 182

```python
        horarios = self._horarios(email, pedido["duracao"], pedido["dia"], pedido["hora"])
```

Busca os horários com a duração, o dia e a hora pedidos.

### Linhas 183 a 184

```python
        return {"pessoa": nome, "email": email, "assunto": pedido["assunto"],
                "duracao": pedido["duracao"], "horarios": horarios, "chat_id": None}
```

Devolve a proposta para a tela.

### Linha 186

```python
    def de_mensagem(self, msg):
```

Trata uma mensagem do Teams reconhecida como pedido.

### Linha 187

```python
        """Mensagem do Teams reconhecida como pedido -> PedidoReuniao com sugestões."""
```

Docstring.

### Linha 188

```python
        email = self.conector.email_de(msg["user_id"])
```

Descobre o e-mail de quem mandou a mensagem.

### Linha 189

```python
        horarios = self._horarios(email, self.r["duracao_padrao"])
```

Busca horários com a duração padrão.

### Linha 190

```python
        pedido = PedidoReuniao(self.conector.empresa, msg["chat_id"], msg["nome"], email, msg["texto"], horarios)
```

Cria o objeto do pedido.

### Linhas 191 a 192

```python
        if self.r["responder_no_teams"] and horarios:
            self.conector.responder(msg["chat_id"], self.texto_sugestao(msg["nome"], horarios))
```

Se a resposta automática estiver ligada e houver horários, responde no próprio chat do Teams.

### Linha 193

```python
        return pedido
```

Devolve o pedido.

### Linha 195

```python
    def texto_sugestao(self, nome, horarios):
```

Monta o texto da resposta automática (em HTML, que é o formato aceito pelo chat do Teams).

### Linha 196

```python
        primeiro = nome.split()[0] if nome else ""
```

Primeiro nome da pessoa.

### Linha 197

```python
        opcoes = "".join(f"<li>{rotulo(h)}</li>" for h in horarios)
```

Lista HTML com um item por horário.

### Linhas 198 a 199

```python
        return (f"<p>Oi {primeiro}! Olhei a nossa agenda e esses horários estão livres para nós dois:</p>"
                f"<ul>{opcoes}</ul><p>Qual fica melhor? (sugestão automática do PixelDigest)</p>")
```

Mensagem completa, deixando claro que é uma sugestão automática.

### Linhas 201 a 202

```python
    def confirmar(self, email, nome, horario, assunto):
        return self.conector.agendar(email, nome, horario, assunto)
```

Confirma: pede ao conector para criar a reunião e devolve o link.
