# `pixeldigest/connectors/base.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/connectors/base.py)

Classe base de todos os conectores. Usa herança: cada serviço (Slack, ClickUp, Gmail...) é uma classe filha que reaproveita o que está aqui e implementa o seu próprio `coletar()`.

### Linhas 1 a 6

```python
"""Classe base dos conectores.

Um conector sabe falar com UM serviço de UMA empresa e devolve uma lista de Item.
Para adicionar um serviço novo: crie uma classe filha, implemente coletar() e
registre o tipo em connectors/__init__.py.
"""
```

Docstring: um conector fala com um serviço de uma empresa e devolve uma lista de `Item`.

### Linha 7

```python
from datetime import datetime, timedelta
```

Importa `datetime` e `timedelta`.

### Linha 8

```python
from zoneinfo import ZoneInfo
```

Importa `ZoneInfo`, que representa um fuso horário pelo nome IANA (ex.: "America/Sao_Paulo"), já com as regras de horário de verão.

### Linha 11

```python
class Conector:
```

Classe base.

### Linha 12

```python
    tipo = "base"
```

Atributo de classe com o tipo. Cada filha troca pelo seu (ex.: `tipo = "slack"`).

### Linha 14

```python
    def __init__(self, empresa, opcoes, cfg):
```

Construtor comum a todos os conectores.

### Linhas 15 a 17

```python
        self.empresa = empresa            # nome da empresa (ex.: "Minha Empresa")
        self.opcoes = opcoes              # bloco do conector no config.yaml
        self.cfg = cfg                    # configuração inteira
```

Guarda o nome da empresa, o bloco de opções desse serviço no YAML e a configuração inteira.

### Linha 18

```python
        self.fuso = ZoneInfo(cfg["usuario"]["fuso"])
```

Cria o fuso do usuário.

### Linha 19

```python
        self.client = None                # os testes trocam por um httpx.Client falso
```

Cliente HTTP; os testes trocam por um cliente falso.

### Linha 21

```python
    def opcao(self, nome, obrigatorio=True):
```

Lê uma opção do conector.

### Linhas 22 a 26

```python
        """Lê uma opção do conector.

        Segredos vêm do .env (o config guarda só o nome da variável em '<nome>_env');
        o resto vem direto do config.yaml.
        """
```

Docstring: segredos vêm do `.env` (o YAML só tem o nome da variável numa chave terminada em `_env`); o resto vem direto do YAML.

### Linha 27

```python
        from ..config import ConfigError, env
```

Import dentro da função para evitar import circular.

### Linhas 28 a 29

```python
        if f"{nome}_env" in self.opcoes:
            return env(self.opcoes[f"{nome}_env"], obrigatorio)
```

Se existe, por exemplo, `token_env` nas opções, lê o valor da variável de ambiente com esse nome.

### Linha 30

```python
        valor = str(self.opcoes.get(nome) or "").strip()
```

Senão, lê o valor direto das opções, transformado em texto e sem espaços nas pontas (`or ""` cobre o valor ausente ou `None`).

### Linhas 31 a 32

```python
        if obrigatorio and not valor:
            raise ConfigError(f"falta '{nome}' do {self.tipo} (preencha em Configurações > Chaves de API)")
```

Se for obrigatório e estiver vazio, lança erro dizendo qual campo de qual serviço falta.

### Linha 33

```python
        return valor
```

Devolve o valor.

### Linhas 35 a 37

```python
    @property
    def nome(self):
        return f"{self.empresa} / {self.tipo}"
```

Propriedade `nome`, como "Minha Empresa / slack". Aparece nas mensagens de erro.

### Linhas 39 a 40

```python
    def agora(self):
        return datetime.now(self.fuso)
```

Hora atual no fuso do usuário.

### Linhas 42 a 43

```python
    def inicio_do_dia(self):
        return self.agora().replace(hour=0, minute=0, second=0, microsecond=0)
```

Meia-noite de hoje: a hora atual com hora, minuto, segundo e microssegundo zerados.

### Linhas 45 a 46

```python
    def fim_de_amanha(self):
        return self.inicio_do_dia() + timedelta(days=2)
```

Meia-noite de depois de amanhã, ou seja, o fim de amanhã. Usado para buscar o que vence ou acontece hoje e amanhã.

### Linhas 48 a 50

```python
    def coletar(self):
        """Devolve list[Item]. Pode levantar net.ApiError ou ConfigError."""
        raise NotImplementedError
```

Método que cada filha precisa implementar. Na base, lança `NotImplementedError` para avisar caso alguém esqueça.

### Linhas 52 a 54

```python
    def precisa_login(self):
        """Conectores com OAuth (Google, Microsoft) respondem True quando falta o login."""
        return False
```

Por padrão, não precisa de login. Google e Microsoft sobrescrevem este método.

### Linhas 56 a 57

```python
    def login(self):
        """Login interativo (roda pelo comando: python -m pixeldigest login)."""
```

Login interativo. Na base não faz nada (o corpo é só a docstring, o que é válido em Python).
