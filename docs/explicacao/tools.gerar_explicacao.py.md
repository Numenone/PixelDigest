# `tools/gerar_explicacao.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../tools/gerar_explicacao.py)

Script que monta esta própria documentação: junta o código de cada arquivo com as notas escritas em `docs/explicacao/_notas/`, gera o índice e confere se nenhuma linha ficou sem explicação.

### Linhas 1 a 21

```python
"""Monta a explicação linha por linha do código (pasta docs/explicacao/).

Cada arquivo do projeto tem um arquivo de notas em docs/explicacao/_notas/.
O formato das notas é simples:

    = pixeldigest/net.py          <- primeira linha: qual arquivo é explicado
    Texto de introdução do arquivo (opcional).
    @1-7                          <- intervalo de linhas do código
    Explicação dessas linhas.
    @8
    Explicação da linha 8.

Este script junta cada trecho de código (copiado direto do arquivo, então nunca
fica desatualizado no texto) com a explicação, gera um .md por arquivo e o
índice docs/explicacao/README.md.

Ele também confere a cobertura: se alguma linha com código ficou sem explicação,
mostra qual é e termina com erro. Assim dá para garantir que TODA linha foi explicada.

Uso: python tools/gerar_explicacao.py
"""
```

Docstring com o formato das notas (primeira linha com o arquivo explicado, depois blocos `@início-fim` com a explicação) e o uso.

### Linha 22

```python
import re
```

Importa `re` (reconhecer as linhas `@1-7`).

### Linha 23

```python
import sys
```

Importa `sys` (código de saída).

### Linha 24

```python
from pathlib import Path
```

Importa `Path`.

### Linha 26

```python
RAIZ = Path(__file__).resolve().parent.parent
```

Raiz do projeto (duas pastas acima deste arquivo).

### Linhas 27 a 28

```python
PASTA = RAIZ / "docs" / "explicacao"
NOTAS = PASTA / "_notas"
```

Pasta de saída e pasta das notas.

### Linha 29

```python
LINGUAGEM = {".py": "python", ".yaml": "yaml", ".bat": "bat", ".txt": "text", ".example": "bash"}
```

Linguagem do bloco de código conforme a extensão do arquivo, para o GitHub colorir a sintaxe.

### Linhas 30 a 47

```python
TOPO_INDICE = """# Explicação do código, linha por linha

Cada arquivo do PixelDigest tem uma página aqui. Em cada página, o código aparece
em trechos (copiados direto do arquivo, com o número das linhas) e, logo abaixo de
cada trecho, o que ele faz e por que está ali. Nenhuma linha com código ficou de
fora: o script `tools/gerar_explicacao.py` confere isso toda vez que gera as páginas.

Ordem sugerida de leitura: comece pelo `__main__.py` (onde o programa começa),
depois `config.py`, `net.py`, `models.py` e `core.py` (o Motor). Em seguida os
conectores (cada API), e por último a interface (`ui/`) e os testes.

Os arquivos `pixeldigest/__init__.py` e `pixeldigest/ui/__init__.py` estão vazios:
eles só existem para o Python tratar a pasta como um pacote (e permitir os imports
com ponto, como `from . import config`).

| Arquivo | Linhas | O que faz |
|---|---:|---|
"""
```

Texto fixo do começo do índice (`README.md` desta pasta): como ler as páginas, a ordem sugerida, por que os `__init__.py` vazios não têm página, e o cabeçalho da tabela. As três aspas permitem um texto de várias linhas.

### Linha 50

```python
def ler_notas(caminho):
```

Lê um arquivo de notas.

### Linha 51

```python
    """Lê um arquivo de notas e devolve (arquivo explicado, introdução, [(ini, fim, texto)])."""
```

Docstring.

### Linha 52

```python
    linhas = caminho.read_text(encoding="utf-8").splitlines()
```

Lê todas as linhas.

### Linhas 53 a 54

```python
    if not linhas or not linhas[0].startswith("= "):
        raise SystemExit(f"{caminho.name}: a primeira linha precisa ser '= caminho/do/arquivo'")
```

A primeira linha precisa começar com "= ".

### Linha 55

```python
    alvo = linhas[0][2:].strip()
```

Caminho do arquivo explicado.

### Linha 56

```python
    intro, blocos, atual = [], [], None
```

Introdução, lista de blocos e o bloco atual.

### Linha 57

```python
    for linha in linhas[1:]:
```

Para cada linha depois da primeira.

### Linha 58

```python
        m = re.fullmatch(r"@(\d+)(?:-(\d+))?\s*", linha)
```

Confere se é uma linha de intervalo, como `@12` ou `@12-18`. O segundo número é opcional.

### Linhas 59 a 63

```python
        if m:
            ini = int(m.group(1))
            fim = int(m.group(2) or ini)
            atual = [ini, fim, []]
            blocos.append(atual)
```

Se for, cria um bloco novo com início, fim (igual ao início quando não há segundo número) e uma lista de linhas de texto.

### Linhas 64 a 65

```python
        elif atual is None:
            intro.append(linha)
```

Antes do primeiro bloco, o texto é a introdução.

### Linhas 66 a 67

```python
        else:
            atual[2].append(linha)
```

Depois, o texto pertence ao bloco atual.

### Linha 68

```python
    return alvo, "\n".join(intro).strip(), [(i, f, "\n".join(t).strip()) for i, f, t in blocos]
```

Devolve o arquivo, a introdução e os blocos com o texto juntado.

### Linhas 71 a 73

```python
def nome_saida(alvo):
    """'pixeldigest/ui/app.py' -> 'pixeldigest.ui.app.py.md' ('.env.example' -> 'env.example.md')."""
    return alvo.replace("/", ".").lstrip(".") + ".md"
```

Nome do arquivo gerado: troca as barras por pontos, tira o ponto do começo (para `.env.example` não virar um arquivo oculto) e acrescenta ".md".

### Linha 76

```python
def gerar(caminho_notas):
```

Gera a explicação de um arquivo.

### Linha 77

```python
    alvo, intro, blocos = ler_notas(caminho_notas)
```

Lê as notas.

### Linha 78

```python
    fonte = (RAIZ / alvo).read_text(encoding="utf-8").splitlines()
```

Lê o código do arquivo explicado.

### Linha 79

```python
    ling = LINGUAGEM.get(Path(alvo).suffix, "")
```

Linguagem do bloco de código.

### Linha 80

```python
    coberto = set()
```

Conjunto das linhas já explicadas.

### Linha 81

```python
    partes = [f"# `{alvo}`", "", f"[Voltar ao índice](README.md) · [Ver o arquivo]({'../../' + alvo})", ""]
```

Começo da página: título e links para o índice e para o arquivo.

### Linhas 82 a 83

```python
    if intro:
        partes += [intro, ""]
```

Introdução, se houver.

### Linha 84

```python
    for ini, fim, texto in blocos:
```

Para cada bloco.

### Linhas 85 a 86

```python
        if ini < 1 or fim > len(fonte) or ini > fim:
            raise SystemExit(f"{alvo}: intervalo @{ini}-{fim} fora do arquivo ({len(fonte)} linhas)")
```

Confere se o intervalo existe no arquivo.

### Linhas 87 a 89

```python
        sobrepostas = coberto & set(range(ini, fim + 1))
        if sobrepostas:
            raise SystemExit(f"{alvo}: linha {min(sobrepostas)} explicada duas vezes")
```

Confere se alguma linha foi explicada duas vezes.

### Linha 90

```python
        coberto.update(range(ini, fim + 1))
```

Marca as linhas como explicadas.

### Linha 91

```python
        titulo = f"Linha {ini}" if ini == fim else f"Linhas {ini} a {fim}"
```

Título do bloco ("Linha 8" ou "Linhas 12 a 18").

### Linha 92

```python
        trecho = "\n".join(fonte[ini - 1:fim]).replace("``​`", "``​`")
```

Copia o trecho do código. Se o código tiver três crases seguidas, coloca um caractere invisível no meio para não fechar o bloco do Markdown antes da hora.

### Linha 93

```python
        partes += [f"### {titulo}", "", f"``​`{ling}", trecho, "``​`", "", texto, ""]
```

Acrescenta título, bloco de código e explicação.

### Linha 94

```python
    faltando = [n for n, linha in enumerate(fonte, 1) if linha.strip() and n not in coberto]
```

Lista as linhas com código (não vazias) que ficaram sem explicação.

### Linha 95

```python
    (PASTA / nome_saida(alvo)).write_text("\n".join(partes), encoding="utf-8")
```

Grava a página.

### Linha 96

```python
    resumo = intro.split(". ")[0].rstrip(".") + "." if intro else ""
```

Resumo de uma frase para o índice: a primeira frase da introdução.

### Linha 97

```python
    return alvo, len(fonte), faltando, resumo
```

Devolve o arquivo, o total de linhas, as que faltaram e o resumo.

### Linha 100

```python
def main():
```

Função principal.

### Linha 101

```python
    PASTA.mkdir(parents=True, exist_ok=True)
```

Garante que a pasta exista.

### Linha 102

```python
    resultados = [gerar(p) for p in sorted(NOTAS.glob("*.txt"))]
```

Gera todas as páginas, na ordem dos arquivos de notas (os números no nome definem a ordem).

### Linhas 103 a 105

```python
    indice = TOPO_INDICE + "".join(f"| [`{alvo}`]({nome_saida(alvo)}) | {total} | {resumo} |\n"
                                   for alvo, total, _, resumo in resultados)
    (PASTA / "README.md").write_text(indice, encoding="utf-8")
```

Monta e grava o índice: o texto fixo mais uma linha da tabela por arquivo, com link, quantidade de linhas e resumo.

### Linhas 106 a 110

```python
    problemas = 0
    for alvo, total, faltando, _ in resultados:
        if faltando:
            problemas += 1
            print(f"FALTA explicar {alvo}: linhas {faltando[:15]}{' ...' if len(faltando) > 15 else ''}")
```

Mostra cada arquivo com linhas faltando.

### Linhas 111 a 112

```python
    total_linhas = sum(total for _, total, _, _ in resultados)
    print(f"{len(resultados)} arquivos ({total_linhas} linhas) gerados em {PASTA.relative_to(RAIZ)}")
```

Total de arquivos e de linhas.

### Linha 113

```python
    sys.exit(1 if problemas else 0)
```

Termina com código 1 se faltou alguma explicação (útil para conferir automaticamente).

### Linhas 116 a 117

```python
if __name__ == "__main__":
    main()
```

Roda o `main` quando o script é executado direto.
