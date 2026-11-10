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
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "docs" / "explicacao"
NOTAS = PASTA / "_notas"
LINGUAGEM = {".py": "python", ".yaml": "yaml", ".bat": "bat", ".txt": "text", ".example": "bash"}
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


def ler_notas(caminho):
    """Lê um arquivo de notas e devolve (arquivo explicado, introdução, [(ini, fim, texto)])."""
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    if not linhas or not linhas[0].startswith("= "):
        raise SystemExit(f"{caminho.name}: a primeira linha precisa ser '= caminho/do/arquivo'")
    alvo = linhas[0][2:].strip()
    intro, blocos, atual = [], [], None
    for linha in linhas[1:]:
        m = re.fullmatch(r"@(\d+)(?:-(\d+))?\s*", linha)
        if m:
            ini = int(m.group(1))
            fim = int(m.group(2) or ini)
            atual = [ini, fim, []]
            blocos.append(atual)
        elif atual is None:
            intro.append(linha)
        else:
            atual[2].append(linha)
    return alvo, "\n".join(intro).strip(), [(i, f, "\n".join(t).strip()) for i, f, t in blocos]


def nome_saida(alvo):
    """'pixeldigest/ui/app.py' -> 'pixeldigest.ui.app.py.md' ('.env.example' -> 'env.example.md')."""
    return alvo.replace("/", ".").lstrip(".") + ".md"


def gerar(caminho_notas):
    alvo, intro, blocos = ler_notas(caminho_notas)
    fonte = (RAIZ / alvo).read_text(encoding="utf-8").splitlines()
    ling = LINGUAGEM.get(Path(alvo).suffix, "")
    coberto = set()
    partes = [f"# `{alvo}`", "", f"[Voltar ao índice](README.md) · [Ver o arquivo]({'../../' + alvo})", ""]
    if intro:
        partes += [intro, ""]
    for ini, fim, texto in blocos:
        if ini < 1 or fim > len(fonte) or ini > fim:
            raise SystemExit(f"{alvo}: intervalo @{ini}-{fim} fora do arquivo ({len(fonte)} linhas)")
        sobrepostas = coberto & set(range(ini, fim + 1))
        if sobrepostas:
            raise SystemExit(f"{alvo}: linha {min(sobrepostas)} explicada duas vezes")
        coberto.update(range(ini, fim + 1))
        titulo = f"Linha {ini}" if ini == fim else f"Linhas {ini} a {fim}"
        trecho = "\n".join(fonte[ini - 1:fim]).replace("```", "``​`")
        partes += [f"### {titulo}", "", f"```{ling}", trecho, "```", "", texto, ""]
    faltando = [n for n, linha in enumerate(fonte, 1) if linha.strip() and n not in coberto]
    (PASTA / nome_saida(alvo)).write_text("\n".join(partes), encoding="utf-8")
    resumo = intro.split(". ")[0].rstrip(".") + "." if intro else ""
    return alvo, len(fonte), faltando, resumo


def main():
    PASTA.mkdir(parents=True, exist_ok=True)
    resultados = [gerar(p) for p in sorted(NOTAS.glob("*.txt"))]
    indice = TOPO_INDICE + "".join(f"| [`{alvo}`]({nome_saida(alvo)}) | {total} | {resumo} |\n"
                                   for alvo, total, _, resumo in resultados)
    (PASTA / "README.md").write_text(indice, encoding="utf-8")
    problemas = 0
    for alvo, total, faltando, _ in resultados:
        if faltando:
            problemas += 1
            print(f"FALTA explicar {alvo}: linhas {faltando[:15]}{' ...' if len(faltando) > 15 else ''}")
    total_linhas = sum(total for _, total, _, _ in resultados)
    print(f"{len(resultados)} arquivos ({total_linhas} linhas) gerados em {PASTA.relative_to(RAIZ)}")
    sys.exit(1 if problemas else 0)


if __name__ == "__main__":
    main()
