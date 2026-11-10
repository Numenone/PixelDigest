# `pixeldigest/digest.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/digest.py)

Monta o resumo do dia: junta os itens de todas as fontes, ordena por importância, gera o texto das notificações e salva o arquivo JSON do dia.

### Linhas 1 a 5

```python
"""Monta o resumo do dia: coleta de todas as fontes, ordena e formata.

Se uma fonte falhar (Slack fora do ar, token vencido...), o resumo sai mesmo
assim com as outras, e a falha aparece na lista de erros.
"""
```

Docstring: o ponto principal é a tolerância a falhas. Uma fonte com problema não impede o resumo; ela só aparece na lista de erros.

### Linha 6

```python
import json
```

Importa `json` para salvar e ler os resumos.

### Linha 7

```python
import logging
```

Importa `logging`.

### Linha 8

```python
from datetime import datetime, timedelta
```

Importa `datetime` e `timedelta`.

### Linha 10

```python
from . import net
```

Importa o nosso `net` para reconhecer o `ApiError`.

### Linha 11

```python
from .config import DATA, ConfigError
```

Importa a pasta `data/` e o erro de configuração.

### Linha 12

```python
from .models import ALTA, URGENTE, Digest, Item
```

Importa as prioridades `ALTA` e `URGENTE` e as classes `Digest` e `Item`.

### Linha 14

```python
log = logging.getLogger(__name__)
```

Logger do módulo.

### Linha 15

```python
ICONES = {"tarefa": "☑", "mensagem": "💬", "email": "✉", "evento": "📅"}
```

Dicionário com um símbolo para cada tipo de item, usado no texto enviado ao Discord e ao celular.

### Linha 18

```python
def ordenar(itens):
```

Função que ordena os itens.

### Linha 19

```python
    """Mais urgente primeiro; empate: o que acontece/vence antes."""
```

Docstring: mais urgente primeiro; em caso de empate, o que acontece ou vence antes.

### Linha 20

```python
    longe = datetime.max.replace(tzinfo=None)
```

Data "infinita" (o maior `datetime` possível) para os itens sem data irem para o fim. `replace(tzinfo=None)` tira o fuso, porque o Python não compara datas com e sem fuso.

### Linha 21

```python
    return sorted(itens, key=lambda i: (-i.prioridade, i.quando.replace(tzinfo=None) if i.quando else longe))
```

`sorted` com uma chave de ordenação que devolve uma tupla. Tuplas são comparadas elemento por elemento: primeiro `-prioridade` (o sinal negativo inverte a ordem, então a prioridade 3 vem antes da 0), depois a data (sem fuso) ou a data infinita.

### Linha 24

```python
def coletar(conectores, clima=None):
```

Função que coleta de uma lista de conectores e monta o `Digest`. Usada nos testes e em ferramentas; o motor tem uma versão própria por fonte.

### Linha 25

```python
    itens, erros = [], []
```

Começa com duas listas vazias.

### Linhas 26 a 28

```python
    for c in conectores:
        try:
            itens += c.coletar()
```

Para cada conector, chama `coletar()` e soma os itens na lista (`+=` em listas acrescenta todos os elementos).

### Linhas 29 a 31

```python
        except (net.ApiError, ConfigError) as exc:
            erros.append(f"{c.nome}: {exc}")
            log.warning("fonte com erro: %s", exc)
```

Erros esperados (de API ou de configuração): guarda a mensagem com o nome da fonte e registra um aviso.

### Linhas 32 a 34

```python
        except Exception as exc:  # nunca deixa uma fonte derrubar o resumo inteiro
            log.exception("erro inesperado em %s", c.nome)
            erros.append(f"{c.nome}: erro inesperado ({exc})")
```

Qualquer outro erro: registra com o rastro completo e guarda uma mensagem genérica. O comentário explica a regra: uma fonte nunca derruba o resumo inteiro.

### Linha 35

```python
    return Digest(gerado_em=datetime.now(), itens=ordenar(itens), clima=clima, erros=erros)
```

Devolve o resumo com a hora atual, os itens ordenados, o clima e os erros.

### Linha 38

```python
def quando_txt(dt, agora):
```

Converte uma data num texto curto e amigável.

### Linhas 39 a 40

```python
    if not dt:
        return ""
```

Sem data, devolve vazio.

### Linha 41

```python
    dias = (dt.date() - agora.date()).days
```

Diferença em dias entre a data do item e hoje.

### Linhas 42 a 43

```python
    if dias == 0:
        return dt.strftime("%H:%M")
```

Hoje: só a hora ("14:30").

### Linhas 44 a 45

```python
    if dias == 1:
        return "amanhã " + dt.strftime("%H:%M")
```

Amanhã: "amanhã 14:30".

### Linhas 46 a 47

```python
    if dias == -1:
        return "ontem"
```

Ontem: "ontem".

### Linha 48

```python
    return dt.strftime("%d/%m")
```

Outros dias: dia e mês ("12/11").

### Linha 51

```python
def linha(item, agora):
```

Monta uma linha de texto para um item.

### Linha 52

```python
    marca = "‼️ " if item.prioridade >= URGENTE else ("❗ " if item.prioridade >= ALTA else "")
```

Marca de urgência: dois pontos de exclamação para urgente, um para alta, nada para o resto. São dois `if` de uma linha encadeados.

### Linhas 53 a 54

```python
    quando = quando_txt(item.quando, agora)
    quando = f" ({quando})" if quando else ""
```

Texto da data. Se existir, coloca entre parênteses com um espaço antes.

### Linha 55

```python
    return f"{marca}{ICONES.get(item.tipo, '•')} {item.titulo}{quando}"
```

Junta marca, ícone do tipo (ou um ponto se o tipo não estiver no dicionário), título e data.

### Linha 58

```python
def texto_resumo(digest, nome, por_empresa=4):
```

Gera o texto do resumo para o Discord e o celular. `por_empresa=4` limita a 4 itens por empresa para a mensagem não ficar enorme.

### Linha 59

```python
    """Texto para Discord e celular. Devolve (título, corpo, campos por empresa)."""
```

Docstring dizendo o que a função devolve.

### Linha 60

```python
    agora = datetime.now().astimezone()
```

Hora atual com o fuso do computador (`astimezone()`).

### Linha 61

```python
    titulo = f"☀️ Bom dia, {nome}! Seu resumo de {agora:%d/%m}"
```

Título com o nome do usuário e a data no formato dia/mês.

### Linha 62

```python
    partes = []
```

Lista das partes do corpo da mensagem.

### Linhas 63 a 66

```python
    if digest.clima:
        c = digest.clima
        partes.append(f"🌡️ {c.cidade}: {c.temperatura:.0f}°C, {c.descricao} "
                      f"(mín {c.minima:.0f}° / máx {c.maxima:.0f}°, chuva {c.prob_chuva}%)")
```

Se há clima, acrescenta uma linha com cidade, temperatura sem casas decimais (`:.0f`), descrição, mínima, máxima e chance de chuva.

### Linha 67

```python
    urgentes = sum(1 for i in digest.itens if i.prioridade >= URGENTE)
```

Conta os itens urgentes. `sum(1 for ...)` soma 1 para cada item que passa no filtro.

### Linha 68

```python
    partes.append(f"📌 {len(digest.itens)} itens, {urgentes} urgentes")
```

Linha com o total de itens e de urgentes.

### Linha 69

```python
    campos = []
```

Lista de campos (um por empresa), que viram blocos separados no Discord.

### Linhas 70 a 71

```python
    for empresa, itens in digest.por_empresa().items():
        linhas = [linha(i, agora) for i in itens[:por_empresa]]
```

Para cada empresa, monta as linhas dos primeiros 4 itens (`itens[:4]` pega do início até o quarto).

### Linhas 72 a 73

```python
        if len(itens) > por_empresa:
            linhas.append(f"... e mais {len(itens) - por_empresa}")
```

Se houver mais itens, avisa quantos ficaram de fora.

### Linha 74

```python
        campos.append((empresa, "\n".join(linhas)))
```

Guarda a tupla (empresa, texto com as linhas separadas por quebra de linha).

### Linhas 75 a 76

```python
    if digest.erros:
        partes.append("⚠️ Fontes com problema: " + "; ".join(digest.erros))
```

Se alguma fonte falhou, acrescenta o aviso com os erros separados por ponto e vírgula.

### Linha 77

```python
    return titulo, "\n".join(partes), campos
```

Devolve título, corpo e campos.

### Linhas 80 a 81

```python
def texto_fim(digest, nome):
    """Resumo das 18h: o que ficou para amanhã."""
```

Gera o texto das 18:00, com o que ficou para amanhã.

### Linha 82

```python
    amanha = datetime.now().date() + timedelta(days=1)
```

Data de amanhã.

### Linha 83

```python
    pendentes = [i for i in digest.itens if i.tipo == "tarefa"]
```

Tarefas ainda abertas.

### Linha 84

```python
    eventos_amanha = [i for i in digest.itens if i.tipo == "evento" and i.quando and i.quando.date() == amanha]
```

Eventos marcados para amanhã (precisa ter data e a data ser amanhã).

### Linha 85

```python
    corpo = [f"✅ Expediente encerrado, {nome}! Bom descanso."]
```

Primeira linha da mensagem.

### Linhas 86 a 87

```python
    if pendentes:
        corpo.append(f"☑ {len(pendentes)} tarefas abertas: " + ", ".join(i.titulo for i in pendentes[:3]))
```

Se há tarefas abertas, mostra quantas e os títulos das três primeiras. `", ".join(...)` junta os textos com vírgula.

### Linhas 88 a 89

```python
    if eventos_amanha:
        corpo.append("📅 Amanhã: " + ", ".join(f"{i.quando:%H:%M} {i.titulo}" for i in eventos_amanha[:4]))
```

Se há eventos amanhã, mostra hora e título dos quatro primeiros.

### Linha 90

```python
    return "🌙 Fim do expediente", "\n".join(corpo)
```

Devolve o título e o corpo.

### Linhas 93 a 94

```python
def salvar(digest):
    """Grava o resumo em data/digest-AAAA-MM-DD.json (o 'artefato' de cada dia)."""
```

Salva o resumo num arquivo JSON por dia.

### Linha 95

```python
    caminho = DATA / f"digest-{digest.gerado_em:%Y-%m-%d}.json"
```

Nome do arquivo com a data do resumo, ex.: `digest-2026-11-06.json`.

### Linha 96

```python
    caminho.write_text(json.dumps(digest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
```

Converte para JSON e grava. `ensure_ascii=False` mantém os acentos legíveis; `indent=2` deixa o arquivo formatado.

### Linha 97

```python
    return caminho
```

Devolve o caminho do arquivo.

### Linhas 100 a 101

```python
def carregar_hoje():
    """O último resumo salvo hoje (para aparecer na hora ao abrir, antes da busca)."""
```

Lê o último resumo salvo hoje. Serve para a tela mostrar algo na hora em que o programa abre, antes da busca completa terminar.

### Linha 102

```python
    caminho = DATA / f"digest-{datetime.now():%Y-%m-%d}.json"
```

Caminho do arquivo de hoje.

### Linhas 103 a 104

```python
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
```

Lê e converte o JSON.

### Linhas 105 a 108

```python
        itens = []
        for d in dados.get("itens", []):
            d["quando"] = datetime.fromisoformat(d["quando"]) if d.get("quando") else None
            itens.append(Item(**d))
```

Recria cada `Item`: converte a data de texto para `datetime` e passa o dicionário como argumentos nomeados com `**d`.

### Linha 109

```python
        return Digest(gerado_em=datetime.fromisoformat(dados["gerado_em"]), itens=itens, erros=dados.get("erros", []))
```

Recria o `Digest` com a data de geração, os itens e os erros.

### Linhas 110 a 111

```python
    except (OSError, ValueError, KeyError, TypeError):
        return None
```

Se o arquivo não existir ou estiver com formato errado (qualquer um desses quatro erros), devolve `None`; o programa segue e faz a busca normal.

### Linhas 114 a 115

```python
class Vistos:
    """Lembra quais itens urgentes já foram avisados, para não repetir notificação."""
```

Classe que lembra quais itens urgentes já geraram notificação, para não avisar duas vezes.

### Linhas 117 a 118

```python
    def __init__(self, arquivo=None):
        self.arquivo = arquivo or DATA / "vistos.json"
```

Construtor. O arquivo pode ser trocado (os testes usam um arquivo temporário); o padrão é `data/vistos.json`.

### Linhas 119 a 120

```python
        try:
            self.chaves = set(json.loads(self.arquivo.read_text(encoding="utf-8")))
```

Carrega as chaves já vistas para um `set`.

### Linhas 121 a 122

```python
        except (OSError, ValueError):
            self.chaves = set()
```

Se não der para ler, começa vazio.

### Linha 124

```python
    def novos(self, itens, prioridade_minima=URGENTE):
```

Devolve só os itens novos com prioridade mínima (padrão: urgente).

### Linha 125

```python
        novos = [i for i in itens if i.prioridade >= prioridade_minima and i.chave() not in self.chaves]
```

Filtra: prioridade suficiente e chave ainda não vista.

### Linhas 126 a 128

```python
        if novos:
            self.chaves.update(i.chave() for i in novos)
            self.arquivo.write_text(json.dumps(sorted(self.chaves)[-2000:]), encoding="utf-8")
```

Se houver novos, acrescenta as chaves ao conjunto e grava no arquivo. Guarda só as últimas 2000 (`[-2000:]`) para o arquivo não crescer para sempre.

### Linha 129

```python
        return novos
```

Devolve os novos.
