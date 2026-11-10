# `run.bat`

[Voltar ao índice](README.md) · [Ver o arquivo](../../run.bat)

Atalho para Windows: na primeira vez prepara o Python e as bibliotecas; depois só abre o programa. Basta dar dois cliques.

### Linha 1

```bat
@echo off
```

`@echo off` faz o Windows não mostrar cada comando antes de executar. O `@` esconde até esta própria linha.

### Linhas 2 a 5

```bat
rem PixelDigest: prepara o Python na primeira vez e abre o programa.
rem Tudo e configurado dentro do programa (botao Configurar ou F10).
rem Uso: run.bat            abre o programa
rem      run.bat --demo     abre com empresas de exemplo
```

Comentários (`rem`): o que o script faz e como usar.

### Linha 6

```bat
cd /d "%~dp0"
```

Entra na pasta do próprio script. `%~dp0` é a pasta onde o `.bat` está e `/d` permite trocar também de disco.

### Linha 7

```bat
set PYTHONUTF8=1
```

Liga o modo UTF-8 do Python, para os acentos saírem certos no terminal do Windows.

### Linha 8

```bat
if not exist .venv\Scripts\python.exe (
```

Se o ambiente virtual ainda não existe.

### Linha 9

```bat
  echo Preparando o PixelDigest pela primeira vez...
```

Avisa.

### Linha 10

```bat
  py -3 -m venv .venv 2>nul || python -m venv .venv
```

Cria o ambiente virtual com o lançador `py` (Python 3). Se não houver `py`, tenta `python`. `2>nul` esconde a mensagem de erro do primeiro e `||` só roda o segundo se o primeiro falhar.

### Linha 11

```bat
  if errorlevel 1 ( echo Instale o Python 3.12+ em python.org e rode de novo. & pause & exit /b 1 )
```

Se nenhum funcionou, explica como instalar o Python, espera uma tecla e sai com erro.

### Linha 12

```bat
  .venv\Scripts\python -m pip install -q --upgrade pip
```

Atualiza o `pip` do ambiente novo, em modo silencioso (`-q`).

### Linha 13

```bat
)
```

Fim do bloco do `if`.

### Linha 14

```bat
rem instala as bibliotecas de novo so quando o requirements.txt mudar
```

Comentário: só reinstala as bibliotecas quando o `requirements.txt` muda.

### Linha 15

```bat
fc /b requirements.txt .venv\req.ok >nul 2>&1 || (
```

`fc /b` compara os bytes do `requirements.txt` com a cópia guardada em `.venv\req.ok`. Se forem diferentes (ou a cópia não existir), roda o bloco depois do `||`.

### Linha 16

```bat
  echo Instalando bibliotecas...
```

Avisa.

### Linha 17

```bat
  .venv\Scripts\python -m pip install -q -r requirements.txt && copy /y requirements.txt .venv\req.ok >nul
```

Instala as bibliotecas e, se deu certo (`&&`), guarda a cópia do `requirements.txt` para a próxima comparação.

### Linha 18

```bat
)
```

Fim do bloco.

### Linha 19

```bat
.venv\Scripts\python -m pixeldigest %*
```

Abre o programa repassando os argumentos recebidos (`%*`), como `--demo`.

### Linha 20

```bat
if errorlevel 1 pause
```

Se o programa terminou com erro, espera uma tecla para a mensagem não sumir.
