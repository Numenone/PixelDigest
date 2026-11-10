# `pixeldigest/config.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/config.py)

Lê, completa com valores padrão, valida e salva a configuração. Atende aos requisitos de arquivo YAML (o que monitorar) e de `.env` (as chaves secretas ficam separadas e fora do GitHub).

### Linhas 1 a 9

```python
"""Carrega, valida e salva a configuração.

Tudo é configurado pela tela de Configurações do próprio app. Ela grava em dois arquivos:
- config.yaml: o que monitorar (empresas, serviços, horários, local do clima). Sem segredos.
- .env: as chaves de API e tokens (requisito 4). Nunca vai para o GitHub (.gitignore).

No config.yaml cada chave aparece só pelo NOME da variável (ex.: token_env: PD_MINHA_EMPRESA_SLACK_TOKEN).
O valor de verdade só existe no .env.
"""
```

Docstring: a configuração é feita pela tela do app e fica em dois arquivos. O `config.yaml` guarda só o nome da variável de cada chave; o valor de verdade fica no `.env`, que está no `.gitignore`.

### Linha 10

```python
import copy
```

Importa `copy` para fazer cópias profundas de dicionários (sem alterar o original).

### Linha 11

```python
import os
```

Importa `os` para ler e gravar variáveis de ambiente (`os.getenv`, `os.environ`).

### Linha 12

```python
import re
```

Importa `re` (expressões regulares), usado para montar o nome das variáveis secretas.

### Linha 13

```python
from datetime import time
```

Importa `time` do módulo `datetime` (um horário sem data, ex.: 07:00).

### Linha 14

```python
from pathlib import Path
```

Importa `Path`, que representa caminhos de arquivo de forma independente do sistema operacional.

### Linha 16

```python
import yaml
```

Importa `yaml` (biblioteca PyYAML) para ler e escrever o `config.yaml`.

### Linha 17

```python
from dotenv import load_dotenv, set_key
```

Importa da `python-dotenv`: `load_dotenv` (carrega o `.env` para as variáveis de ambiente) e `set_key` (grava uma chave no `.env`).

### Linha 19

```python
ROOT = Path(__file__).resolve().parent.parent
```

`ROOT` é a pasta raiz do projeto. `__file__` é o caminho deste arquivo; `.resolve()` deixa o caminho absoluto; `.parent.parent` sobe duas pastas (de `pixeldigest/config.py` para a raiz).

### Linhas 20 a 23

```python
DATA = ROOT / "data"
TOKENS = ROOT / "tokens"
ARQ_CONFIG = ROOT / "config.yaml"
ARQ_ENV = ROOT / ".env"
```

Caminhos usados no programa todo: `data/` (resumos e caches), `tokens/` (logins OAuth), o `config.yaml` e o `.env`.

### Linha 25

```python
TIPOS = {"slack", "clickup", "gmail", "microsoft", "zoom"}
```

Conjunto dos tipos de serviço aceitos. Qualquer outro tipo no YAML gera erro de validação.

### Linhas 27 a 38

```python
# Fusos do Brasil (IANA) -> nome usado pelo Outlook/Microsoft Graph
FUSOS = {
    "America/Sao_Paulo": "E. South America Standard Time",
    "America/Bahia": "Bahia Standard Time",
    "America/Fortaleza": "SA Eastern Standard Time",
    "America/Recife": "SA Eastern Standard Time",
    "America/Belem": "SA Eastern Standard Time",
    "America/Cuiaba": "Central Brazilian Standard Time",
    "America/Manaus": "SA Western Standard Time",
    "America/Rio_Branco": "SA Pacific Standard Time",
    "America/Noronha": "UTC-02",
}
```

Dicionário que traduz o fuso no padrão IANA (usado pelo Python) para o nome usado pelo Outlook/Microsoft Graph, que segue o padrão do Windows. Cobre os fusos do Brasil.

### Linhas 40 a 51

```python
PADRAO = {
    "demo": False,
    "usuario": {"nome": "", "fuso": "America/Sao_Paulo"},
    "clima": {"local": "São Paulo", "lat": None, "lon": None},
    "horarios": {"inicio_dia": "07:00", "fim_dia": "18:00", "expediente": ["09:00", "18:00"]},
    "notificacoes": {"discord": True, "celular": True, "ouvir_alarme": True},
    "ia": {"modelo": "claude-opus-5-5"},      # resumo dos e-mails com o Claude
    "tela": {"orientacao": "automatica", "resolucao": "1280x720", "tela_cheia": False},
    "reunioes": {"duracao_padrao": 30, "dias_para_frente": 3, "responder_no_teams": False,
                 "palavras": ["reunião", "reuniao", "call", "meet", "meeting", "conversar", "alinhar", "papo"]},
    "empresas": [],
}
```

`PADRAO` é a configuração padrão completa. Tudo o que faltar no `config.yaml` é completado com estes valores: modo demonstração, usuário e fuso, local do clima, horários do dia, quais notificações usar, modelo de IA dos resumos de e-mail, tela (orientação, resolução, tela cheia), regras de reunião (duração, quantos dias à frente, resposta automática e palavras que indicam pedido) e a lista de empresas (vazia).

### Linhas 54 a 55

```python
class ConfigError(Exception):
    pass
```

Exceção própria para erros de configuração. `pass` quer dizer que a classe não acrescenta nada além de herdar de `Exception`.

### Linha 58

```python
def env(nome, obrigatorio=True):
```

Função que lê uma variável de ambiente. Se `obrigatorio=False`, aceita vazio.

### Linha 59

```python
    """Lê uma variável do .env com mensagem clara quando falta."""
```

Docstring.

### Linha 60

```python
    valor = os.getenv(nome, "").strip()
```

Lê a variável (ou texto vazio se não existir) e tira espaços das pontas com `.strip()`.

### Linhas 61 a 62

```python
    if obrigatorio and not valor:
        raise ConfigError(f"falta a chave {nome} (preencha em Configurações > Chaves de API)")
```

Se for obrigatória e estiver vazia, lança `ConfigError` dizendo exatamente qual chave falta e onde preencher.

### Linha 63

```python
    return valor
```

Devolve o valor.

### Linhas 66 a 68

```python
def existe():
    """True se o usuário já salvou as configurações alguma vez."""
    return ARQ_CONFIG.exists()
```

Diz se o `config.yaml` já existe, ou seja, se o usuário já salvou as configurações alguma vez. Usado para abrir as Configurações na primeira vez.

### Linha 71

```python
def _mesclar(base, novo):
```

Função interna que mistura a configuração do arquivo com a padrão.

### Linha 72

```python
    """Completa o que faltar em 'novo' com os valores padrão."""
```

Docstring.

### Linha 73

```python
    saida = copy.deepcopy(base)
```

Começa de uma cópia profunda do padrão, para nunca alterar o `PADRAO` original.

### Linha 74

```python
    for k, v in (novo or {}).items():
```

Percorre cada chave e valor do que veio do arquivo. `novo or {}` trata o caso de o arquivo vir vazio (`None`).

### Linha 75

```python
        saida[k] = _mesclar(saida[k], v) if isinstance(v, dict) and isinstance(saida.get(k), dict) else v
```

Se o valor é um dicionário e o padrão também tem um dicionário nessa chave, mistura os dois chamando a própria função (recursão). Senão, o valor do arquivo substitui o padrão. Assim, se o arquivo só tiver `clima: {local: Pelotas}`, os campos `lat` e `lon` continuam vindo do padrão.

### Linha 76

```python
    return saida
```

Devolve o resultado.

### Linha 79

```python
def carregar_bruto(caminho=None):
```

Lê o `config.yaml` do jeito que está no arquivo, com os horários ainda como texto. É a versão que a tela de Configurações edita.

### Linha 80

```python
    """config.yaml do jeito que está no arquivo (horários como texto), já com os padrões."""
```

Docstring.

### Linha 81

```python
    load_dotenv(ARQ_ENV, override=True)
```

Carrega o `.env` para as variáveis de ambiente. `override=True` faz valores novos do arquivo substituírem os antigos (importante depois que o usuário salva uma chave nova).

### Linha 82

```python
    caminho = Path(caminho) if caminho else ARQ_CONFIG
```

Usa o caminho recebido ou o padrão.

### Linha 83

```python
    dados = {}
```

Começa com um dicionário vazio.

### Linhas 84 a 86

```python
    if caminho.exists():
        with open(caminho, encoding="utf-8") as f:
            dados = yaml.safe_load(f) or {}
```

Se o arquivo existe, abre em UTF-8 e lê com `yaml.safe_load`. O `safe_load` só aceita dados simples, sem executar código, o que é mais seguro. `or {}` cobre o arquivo vazio.

### Linhas 87 a 89

```python
    # compatibilidade com a versão antiga, que usava "cidade"
    if "cidade" in dados and "clima" not in dados:
        dados["clima"] = {"local": dados.pop("cidade")}
```

Compatibilidade com a versão antiga do config, que tinha só `cidade:`. Se encontrar, converte para o formato novo `clima: {local: ...}`. `pop` lê e remove a chave antiga.

### Linha 90

```python
    return _mesclar(PADRAO, dados)
```

Mistura com o padrão e devolve.

### Linha 93

```python
def _hora(texto, campo):
```

Função interna que converte "07:00" em `time(7, 0)`.

### Linhas 94 a 96

```python
    try:
        h, m = str(texto).split(":")
        return time(int(h), int(m))
```

Separa o texto no ":" em hora e minuto, converte para inteiro e monta o `time`.

### Linhas 97 a 98

```python
    except ValueError:
        raise ConfigError(f"horário inválido em '{campo}': {texto} (use HH:MM)") from None
```

Se o texto não estiver no formato certo, lança `ConfigError` dizendo qual campo está errado. O `from None` esconde o erro técnico original e deixa só a mensagem clara.

### Linha 101

```python
def preparar(bruto, demo=False):
```

Converte o config bruto no formato usado pelo programa e valida.

### Linha 102

```python
    """Converte o config bruto no formato usado pelo programa e valida."""
```

Docstring.

### Linha 103

```python
    cfg = copy.deepcopy(bruto)
```

Trabalha numa cópia para não alterar o bruto (que a tela continua editando).

### Linha 104

```python
    u = cfg["usuario"]
```

Atalho para a parte do usuário.

### Linha 105

```python
    u["nome"] = u.get("nome") or "você"
```

Se o nome estiver vazio, usa "você" nas mensagens.

### Linha 106

```python
    u["fuso_windows"] = u.get("fuso_windows") or FUSOS.get(u["fuso"], "E. South America Standard Time")
```

Calcula o nome do fuso no padrão Windows a partir do dicionário `FUSOS`, com São Paulo como padrão.

### Linhas 107 a 110

```python
    h = cfg["horarios"]
    h["inicio_dia"] = _hora(h["inicio_dia"], "início do dia")
    h["fim_dia"] = _hora(h["fim_dia"], "fim do dia")
    h["expediente"] = (_hora(h["expediente"][0], "expediente"), _hora(h["expediente"][1], "expediente"))
```

Converte os horários de texto para `time`, usando a função `_hora`. O expediente vira uma tupla (início, fim).

### Linhas 111 a 113

```python
    for emp in cfg["empresas"]:
        if not emp.get("nome"):
            raise ConfigError("toda empresa precisa de um nome")
```

Valida cada empresa: toda empresa precisa de nome.

### Linha 114

```python
        emp.setdefault("cor", "#5ab0ff")
```

Se não tiver cor, usa um azul padrão.

### Linha 115

```python
        emp.setdefault("ativa", True)            # empresa desligada = nenhum serviço dela roda
```

Se não tiver o campo `ativa`, considera ligada. Empresa desligada não roda nenhum serviço.

### Linhas 116 a 118

```python
        for con in emp.setdefault("conectores", []):
            if con.get("tipo") not in TIPOS:
                raise ConfigError(f"{emp['nome']}: serviço '{con.get('tipo')}' não existe")
```

Para cada serviço da empresa (criando a lista vazia se não existir), confere se o tipo é um dos aceitos. Se não for, lança erro com o nome da empresa e do tipo.

### Linha 119

```python
    cfg["demo"] = bool(demo or cfg.get("demo"))
```

O modo demonstração fica ligado se veio pela linha de comando ou pelo arquivo. `bool()` garante que o valor seja `True` ou `False`.

### Linhas 120 a 121

```python
    DATA.mkdir(exist_ok=True)
    TOKENS.mkdir(exist_ok=True)
```

Garante que as pastas `data/` e `tokens/` existam.

### Linha 122

```python
    return cfg
```

Devolve o config pronto.

### Linhas 125 a 127

```python
def carregar(caminho=None, demo=False):
    """Atalho: lê o config.yaml + .env e devolve pronto para usar."""
    return preparar(carregar_bruto(caminho), demo)
```

Atalho: lê e prepara de uma vez.

### Linhas 130 a 133

```python
def nome_segredo(*partes):
    """('Minha Empresa', 'slack', 'token') -> 'PD_MINHA_EMPRESA_SLACK_TOKEN'."""
    texto = "_".join(partes)
    return "PD_" + re.sub(r"[^A-Z0-9]+", "_", texto.upper()).strip("_")
```

Monta o nome da variável secreta a partir das partes. Junta com "_", passa para maiúsculas, troca tudo o que não for letra ou número por "_" (a expressão regular `[^A-Z0-9]+`) e tira "_" das pontas. Exemplo: ("Minha Empresa", "slack", "token") vira `PD_MINHA_EMPRESA_SLACK_TOKEN`.

### Linha 136

```python
def salvar(bruto, segredos):
```

Salva a configuração e as chaves.

### Linhas 137 a 140

```python
    """Grava o config.yaml (sem segredos) e as chaves no .env.

    segredos: {NOME_DA_VARIAVEL: valor}. Valor vazio apaga a chave.
    """
```

Docstring: `segredos` é um dicionário `{NOME: valor}`; valor vazio apaga a chave.

### Linhas 141 a 143

```python
    with open(ARQ_CONFIG, "w", encoding="utf-8") as f:
        f.write("# Gerado pela tela de Configurações do PixelDigest. As chaves ficam no .env.\n")
        yaml.safe_dump(bruto, f, allow_unicode=True, sort_keys=False)
```

Abre o `config.yaml` para escrita, grava um comentário no topo e depois o YAML. `allow_unicode=True` mantém os acentos legíveis; `sort_keys=False` mantém a ordem original das chaves.

### Linha 144

```python
    ARQ_ENV.touch(exist_ok=True)
```

Cria o `.env` se ainda não existir (`touch`).

### Linhas 145 a 148

```python
    for nome, valor in segredos.items():
        valor = (valor or "").strip()
        set_key(str(ARQ_ENV), nome, valor, quote_mode="never")
        os.environ[nome] = valor
```

Para cada chave: tira espaços, grava no `.env` com `set_key` (sem aspas, `quote_mode="never"`) e atualiza a variável de ambiente do processo atual, para valer na hora sem reiniciar o programa.

### Linhas 151 a 154

```python
def cor_rgb(hexa):
    """'#3fa7ff' vira (63, 167, 255)."""
    hexa = hexa.lstrip("#")
    return tuple(int(hexa[i:i + 2], 16) for i in (0, 2, 4))
```

Converte uma cor hexadecimal em tupla RGB. Tira o "#", pega dois caracteres por vez (posições 0, 2 e 4) e converte de base 16 para inteiro.
