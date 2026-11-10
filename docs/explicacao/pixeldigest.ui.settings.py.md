# `pixeldigest/ui/settings.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/ui/settings.py)

A tela de Configurações. Tudo o que o programa precisa (local do clima, horários, notificações, empresas, chaves de API e reuniões) é configurado aqui, sem editar arquivo nenhum.

### Linhas 1 a 11

```python
"""Tela de Configurações: tudo o que o programa precisa, sem editar arquivo nenhum.

Abas: Início, Clima, Horários, Notificações, Empresas, Chaves de API, Reuniões.

A tela trabalha numa CÓPIA da configuração (self.cfg) e das chaves (self.chaves).
Nada é gravado até clicar em "Salvar e aplicar": aí config.salvar() escreve o
config.yaml (sem segredos) e o .env (com as chaves), e o app reinicia o Motor.

Botões que usam a internet (buscar endereço, conectar, testar, login) rodam em
segundo plano; o resultado volta por uma fila e aparece embaixo do botão.
"""
```

Docstring: lista as abas e explica que a tela trabalha numa cópia da configuração; nada é gravado até clicar em "Salvar e aplicar". Os botões que usam a internet rodam em segundo plano e o resultado volta por uma fila.

### Linha 12

```python
import copy
```

Importa `copy` (cópia profunda das opções de um serviço para o teste).

### Linha 13

```python
import json
```

Importa `json` (usado para tirar uma "foto" do estado e saber se algo mudou).

### Linha 14

```python
import os
```

Importa `os` (ler e gravar variáveis de ambiente).

### Linha 15

```python
import queue
```

Importa `queue` (fila de resultados dos botões).

### Linha 16

```python
import shutil
```

Importa `shutil` (copiar o arquivo de credenciais do Google).

### Linha 17

```python
import sys
```

Importa `sys` (saber se é Windows).

### Linha 18

```python
import threading
```

Importa `threading` (botões em segundo plano).

### Linha 19

```python
import webbrowser
```

Importa `webbrowser`, que abre um site no navegador padrão.

### Linha 21

```python
import pygame
```

Importa o pygame.

### Linha 23

```python
from .. import assistente, config, net
```

Importa as funções dos botões, a configuração e a rede.

### Linha 24

```python
from ..config import nome_segredo
```

Importa a função que monta o nome das variáveis secretas.

### Linha 25

```python
from ..connectors import weather
```

Importa o clima (botão "Ver o clima agora").

### Linha 26

```python
from . import font
```

Importa as fontes.

### Linha 27

```python
from .widgets import AMARELO, BRANCO, CINZA, PALETA, VERDE, VERMELHO, Form, copiar
```

Importa cores, a paleta, o `Form` e a função de copiar dos widgets.

### Linha 29

```python
ABAS = ["Início", "Clima", "Horários", "Notificações", "Empresas", "Chaves de API", "Reuniões"]
```

Nomes das abas.

### Linhas 30 a 32

```python
FUSOS = [("America/Sao_Paulo", "Brasília"), ("America/Manaus", "Manaus"), ("America/Cuiaba", "Cuiabá"),
         ("America/Fortaleza", "Fortaleza"), ("America/Recife", "Recife"), ("America/Bahia", "Salvador"),
         ("America/Belem", "Belém"), ("America/Rio_Branco", "Rio Branco"), ("America/Noronha", "Noronha")]
```

Fusos do Brasil oferecidos: nome IANA e nome mostrado.

### Linhas 33 a 34

```python
SERVICOS = [("slack", "Slack"), ("clickup", "ClickUp"), ("gmail", "Gmail + Agenda"), ("zoom", "Zoom (reuniões)"),
            ("microsoft", "Outlook + Teams")]
```

Serviços que uma empresa pode ligar.

### Linha 35

```python
GLOBAIS = ["DISCORD_WEBHOOK_URL", "NTFY_TOPIC", "NTFY_TOPIC_ALARME", "NTFY_SERVER", "NTFY_TOKEN", "ANTHROPIC_API_KEY"]
```

Variáveis globais do `.env` (não pertencem a uma empresa específica).

### Linha 36

```python
LARGURA = 900          # largura útil do conteúdo
```

Largura útil do conteúdo.

### Linha 39

```python
def servico_novo(tipo, empresa):
```

Opções iniciais de um serviço recém-ligado.

### Linha 40

```python
    """Opções iniciais de um serviço recém-ligado. Segredos apontam para uma variável do .env."""
```

Docstring: os segredos apontam para o nome de uma variável do `.env`.

### Linha 41

```python
    base = {"tipo": tipo}
```

Começa só com o tipo.

### Linhas 42 a 43

```python
    if tipo == "slack":
        base.update(token_env=nome_segredo(empresa, "slack", "token"), meu_id="", canais=[], incluir_dms=False)
```

Slack: nome da variável do token, id, canais e DMs desligadas.

### Linhas 44 a 45

```python
    elif tipo == "clickup":
        base.update(token_env=nome_segredo(empresa, "clickup", "token"), equipe_id="")
```

ClickUp: variável do token e workspace.

### Linhas 46 a 47

```python
    elif tipo == "gmail":
        base.update(credenciais="", conta=nome_segredo(empresa).lower()[3:], agenda=True, resumo_ia=True)
```

Gmail: arquivo de credenciais, nome da conta (o nome da variável sem o "pd_" do começo, em minúsculas), agenda e resumo com IA ligados.

### Linhas 48 a 49

```python
    elif tipo == "zoom":
        base.update(account_id="", client_id="", client_secret_env=nome_segredo(empresa, "zoom", "secret"), email="")
```

Zoom: Account ID, Client ID, variável do Client Secret e e-mail.

### Linhas 50 a 51

```python
    elif tipo == "microsoft":
        base.update(client_id="", tenant="organizations", email=True, agenda=True, teams=True, agendador=False)
```

Microsoft: client id, tenant e quais partes usar (agendador começa desligado).

### Linha 52

```python
    return base
```

Devolve.

### Linha 55

```python
class TelaConfig:
```

Classe da tela de Configurações.

### Linha 56

```python
    def __init__(self, app, primeira_vez=False, orientacao="horizontal"):
```

Construtor.

### Linhas 57 a 58

```python
        self.app = app
        self.primeira_vez = primeira_vez
```

Guarda o app e se é a primeira vez.

### Linhas 59 a 61

```python
        # as Configurações têm a própria tela: 1280x720 (abas na lateral) ou 960x1280 (abas em cima)
        self.vertical = orientacao == "vertical"
        self.superficie = pygame.Surface((960, 1280) if self.vertical else (1280, 720))
```

As Configurações têm a própria superfície: 1280x720 com abas na lateral, ou 960x1280 com abas em cima na vertical. O app amplia essa superfície para a janela.

### Linha 62

```python
        self.form = Form(self.superficie)
```

Cria o formulário que desenha nessa superfície.

### Linha 63

```python
        self.cfg = config.carregar_bruto()
```

Carrega a configuração bruta (é a cópia que a tela edita).

### Linha 64

```python
        self.chaves = {n: os.getenv(n, "") for n in GLOBAIS}
```

Lê as chaves globais do ambiente.

### Linhas 65 a 68

```python
        for emp in self.cfg["empresas"]:
            for con in emp["conectores"]:
                if con.get("token_env"):
                    self.chaves[con["token_env"]] = os.getenv(con["token_env"], "")
```

Lê também os tokens de cada serviço que tem `token_env`.

### Linha 69

```python
        self.chaves["NTFY_SERVER"] = self.chaves["NTFY_SERVER"] or "https://ntfy.sh"
```

Servidor do ntfy padrão.

### Linha 70

```python
        self._migrar()
```

Converte configurações antigas (ver `_migrar`).

### Linha 71

```python
        self.iniciar_windows = assistente.inicia_com_windows()
```

Lê se o início com o Windows está ligado.

### Linha 72

```python
        self.original = None           # foto tirada depois do 1º quadro (os campos completam padrões)
```

Foto do estado original, tirada depois do primeiro quadro (o comentário explica: os campos completam valores padrão no primeiro desenho).

### Linha 73

```python
        self.aba = 0
```

Aba atual.

### Linha 74

```python
        self.mensagens = {}            # id do botão -> (texto, cor)
```

Mensagens de resultado por botão.

### Linha 75

```python
        self.dados = {}                # resultados guardados (canais do Slack, workspaces, endereços...)
```

Resultados guardados (canais do Slack, workspaces, endereços...).

### Linha 76

```python
        self.codigos = {}              # login Microsoft: id -> (site, código)
```

Códigos de login da Microsoft.

### Linha 77

```python
        self.fila = queue.Queue()
```

Fila de resultados dos botões.

### Linha 78

```python
        self.busca = ""
```

Texto da busca de endereço.

### Linha 79

```python
        self.confirmar_remover = None
```

Empresa aguardando confirmação para remover.

### Linha 80

```python
        self.aberta = True
```

Se a tela está aberta.

### Linha 81

```python
        self.erro_salvar = ""
```

Erro ao salvar.

### Linha 83

```python
    # ---------- utilidades ----------
```

Comentário: utilidades.

### Linha 84

```python
    def _migrar(self):
```

Converte configurações antigas.

### Linhas 85 a 88

```python
        """Configs antigas guardavam campos comuns (ID, tenant, arquivo) no .env.

        A tela edita esses campos direto no config.yaml; só tokens continuam no .env.
        """
```

Docstring: antes, campos comuns (ids, tenant, arquivo) ficavam no `.env`; agora só os tokens ficam lá.

### Linhas 89 a 93

```python
        for emp in self.cfg["empresas"]:
            for con in emp["conectores"]:
                for campo in ("meu_id", "equipe_id", "credenciais", "client_id", "tenant"):
                    if f"{campo}_env" in con:
                        con[campo] = os.getenv(con.pop(f"{campo}_env"), "")
```

Para cada campo antigo terminado em `_env`, lê o valor do ambiente, guarda direto no campo e remove a chave antiga (`pop`).

### Linhas 95 a 96

```python
    def _foto(self):
        return json.dumps([self.cfg, self.chaves, self.iniciar_windows], sort_keys=True, default=str)
```

Foto do estado: transforma configuração, chaves e início com o Windows num texto JSON ordenado. Comparar textos é um jeito simples de saber se algo mudou.

### Linhas 98 a 99

```python
    def mudou(self):
        return self.original is not None and self._foto() != self.original
```

Mudou se a foto atual é diferente da original.

### Linha 101

```python
    def rodar(self, id_, funcao, *args, depois=None, aguarde="aguarde..."):
```

Roda uma função em segundo plano.

### Linha 102

```python
        """Roda funcao(*args) em segundo plano e mostra o resultado embaixo do botão."""
```

Docstring.

### Linha 103

```python
        self.mensagens[id_] = (aguarde, AMARELO)
```

Mostra "aguarde..." embaixo do botão.

### Linha 105

```python
        def trabalho():
```

Função que a thread executa.

### Linhas 106 a 107

```python
            try:
                self.fila.put((id_, True, funcao(*args), depois))
```

Chama a função e põe o resultado na fila com sucesso. `depois` é uma função opcional para tratar o resultado.

### Linhas 108 a 109

```python
            except (net.ApiError, config.ConfigError, ValueError) as exc:
                self.fila.put((id_, False, str(exc), None))
```

Erros esperados: põe a mensagem com falha.

### Linhas 110 a 111

```python
            except Exception as exc:  # erro inesperado: mostra em vez de quebrar
                self.fila.put((id_, False, f"erro: {exc}", None))
```

Erro inesperado: mostra em vez de quebrar a tela.

### Linha 112

```python
        threading.Thread(target=trabalho, daemon=True).start()
```

Começa a thread.

### Linha 114

```python
    def _resultados(self):
```

Lê os resultados que chegaram.

### Linhas 115 a 119

```python
        while True:
            try:
                id_, ok, resultado, depois = self.fila.get_nowait()
            except queue.Empty:
                return
```

Tira da fila sem esperar (`get_nowait`); quando a fila está vazia, termina.

### Linhas 120 a 122

```python
            if ok and depois:
                texto = depois(resultado)
                self.mensagens[id_] = (texto or "pronto!", VERDE)
```

Sucesso com `depois`: chama e mostra o texto que ela devolver (ou "pronto!") em verde.

### Linhas 123 a 124

```python
            elif ok:
                self.mensagens[id_] = (str(resultado), VERDE)
```

Sucesso sem `depois`: mostra o resultado em verde.

### Linhas 125 a 126

```python
            else:
                self.mensagens[id_] = (resultado, VERMELHO)
```

Falha: mostra em vermelho.

### Linhas 128 a 132

```python
    def _aplicar_chaves_no_ambiente(self):
        """Antes de testar, deixa as chaves digitadas visíveis para os conectores (sem gravar)."""
        for nome, valor in self.chaves.items():
            if valor:
                os.environ[nome] = valor.strip()
```

Antes de testar, coloca as chaves digitadas no ambiente (sem gravar no arquivo), para os conectores enxergarem.

### Linhas 134 a 136

```python
    def _cfg_pronto(self):
        self._aplicar_chaves_no_ambiente()
        return config.preparar(self.cfg)
```

Prepara uma configuração válida com as chaves digitadas, para os testes.

### Linha 138

```python
    # ---------- eventos ----------
```

Comentário: eventos.

### Linhas 139 a 142

```python
    def evento(self, ev):
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE and not self.form.foco:
            self.fechar()
            return
```

Esc sem campo em foco fecha a tela.

### Linha 143

```python
        self.form.evento(ev)
```

Os outros eventos vão para o formulário.

### Linhas 145 a 146

```python
    def fechar(self):
        self.aberta = False
```

Fecha.

### Linha 148

```python
    def salvar(self):
```

Salva.

### Linhas 149 a 153

```python
        try:
            config.preparar(self.cfg)          # valida antes de gravar
        except config.ConfigError as exc:
            self.erro_salvar = str(exc)
            return
```

Valida antes de gravar; se houver erro, mostra e não salva.

### Linha 154

```python
        config.salvar(self.cfg, self.chaves)
```

Grava o YAML e o `.env`.

### Linha 155

```python
        assistente.definir_inicio_com_windows(self.iniciar_windows)
```

Liga ou desliga o início com o Windows.

### Linhas 156 a 158

```python
        self.original = self._foto()
        self.erro_salvar = ""
        self.aberta = False
```

Atualiza a foto, limpa o erro e fecha.

### Linha 159

```python
        self.app.recarregar()
```

Pede ao app para recarregar tudo com a configuração nova.

### Linha 161

```python
    # ---------- desenho ----------
```

Comentário: desenho.

### Linha 162

```python
    def desenhar(self, fundo):
```

Desenha a tela inteira.

### Linha 163

```python
        """Desenha tudo na própria superfície; o app ajusta ela ao tamanho da janela."""
```

Docstring.

### Linha 164

```python
        self._resultados()
```

Processa os resultados dos botões.

### Linhas 165 a 166

```python
        tela = self.superficie
        largura, altura = tela.get_size()
```

Superfície e tamanho.

### Linha 167

```python
        pygame.transform.scale(fundo, (largura, altura), tela)      # o cenário aparece atrás
```

Copia o cenário ampliado para o fundo.

### Linhas 168 a 171

```python
        if not hasattr(self, "_escuro"):          # criado uma vez só (economiza memória)
            self._escuro = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
            self._escuro.fill((6, 8, 16, 215))
        tela.blit(self._escuro, (0, 0))
```

Escurece o fundo com uma camada criada uma vez só.

### Linhas 172 a 176

```python
        # cabeçalho: mesma barra do topo da tela principal
        topo = pygame.Surface((tela.get_width(), 76), pygame.SRCALPHA)
        topo.fill((10, 12, 22, 235))
        tela.blit(topo, (0, 0))
        pygame.draw.line(tela, (60, 70, 100), (0, 76), (tela.get_width(), 76), 2)
```

Barra do topo.

### Linha 177

```python
        tela.blit(font.render("CONFIGURAÇÕES", 4, BRANCO, shadow=(0, 0, 0), familia="titulo"), (40, 20))
```

Título.

### Linhas 178 a 180

```python
        if not self.vertical:
            sub = "Tudo do PixelDigest se ajusta aqui. Nada é gravado até você clicar em Salvar."
            tela.blit(font.render(sub, 1, CINZA), (largura - font.largura(sub, 1) - 40, 30))
```

Na horizontal, um subtítulo à direita.

### Linhas 182 a 183

```python
        f = self.form
        f.comecar(pygame.Rect(0, 0, largura, altura))
```

Começa a parte das abas.

### Linhas 184 a 190

```python
        if self.vertical:
            # abas em duas linhas no topo
            for i, nome in enumerate(ABAS):
                if f.botao(f"aba{i}", 20 + (i % 4) * 232, 92 + (i // 4) * 48, 220, nome,
                           VERDE if i == self.aba else (110, 116, 140), h=40):
                    self.aba, f.rolagem, f.foco = i, 0, None
            area = pygame.Rect(20, 200, 930, altura - 200 - 110)
```

Vertical: abas em duas linhas de 4 no topo. Clicar troca a aba, zera a rolagem e tira o foco. A área de conteúdo fica embaixo.

### Linhas 191 a 198

```python
        else:
            # abas na lateral (fora da área com rolagem)
            for i, nome in enumerate(ABAS):
                if f.botao(f"aba{i}", 40, 96 + i * 50, 210, nome, VERDE if i == self.aba else (110, 116, 140), h=40):
                    self.aba, f.rolagem, f.foco = i, 0, None
            if self.mudou():
                f.paragrafo(40, 470, "Você tem alterações que ainda não foram salvas.", 210, AMARELO)
            area = pygame.Rect(280, 90, 960, 540)
```

Horizontal: abas na lateral esquerda, aviso de alterações não salvas e área de conteúdo à direita.

### Linha 199

```python
        f.terminar()
```

Termina a parte das abas.

### Linha 201

```python
        # conteúdo da aba, com rolagem
```

Comentário: conteúdo com rolagem.

### Linhas 202 a 203

```python
        f.comecar(area, rolar=True)
        x, y = area.x + 10, area.y + 6
```

Começa a área com rolagem e a posição inicial.

### Linhas 204 a 205

```python
        desenhar_aba = [self.aba_inicio, self.aba_clima, self.aba_horarios, self.aba_notificacoes,
                        self.aba_empresas, self.aba_chaves, self.aba_reunioes][self.aba]
```

Lista das funções de cada aba; escolhe a da aba atual pelo índice.

### Linhas 206 a 207

```python
        fim = desenhar_aba(x, y)
        f.terminar(fim - area.y + 20)
```

Desenha a aba e informa a altura do conteúdo para limitar a rolagem.

### Linhas 208 a 211

```python
        if f.altura > area.h:      # barrinha de rolagem
            prop = area.h / f.altura
            barra = pygame.Rect(area.right + 8, area.y + int(f.rolagem * prop), 6, int(area.h * prop))
            pygame.draw.rect(tela, (90, 100, 130), barra)
```

Se o conteúdo é maior que a área, desenha uma barra de rolagem proporcional.

### Linha 213

```python
        # rodapé
```

Comentário: rodapé.

### Linhas 214 a 215

```python
        f.comecar(pygame.Rect(0, 0, largura, altura))
        rodape = altura - 70
```

Começa o rodapé.

### Linhas 216 a 219

```python
        if f.botao("salvar", largura - 280, rodape, 240, "Salvar e aplicar", VERDE, h=44):
            self.salvar()
        if f.botao("cancelar", largura - 450, rodape, 160, "Cancelar", (160, 160, 180), h=44):
            self.fechar()
```

Botões Salvar e Cancelar.

### Linhas 220 a 226

```python
        texto_w = largura - 520
        if self.erro_salvar:
            f.paragrafo(40, rodape + 6, self.erro_salvar, texto_w, VERMELHO)
        elif self.vertical and self.mudou():
            f.paragrafo(40, rodape + 12, "Alterações ainda não salvas.", texto_w, AMARELO)
        else:
            f.paragrafo(40, rodape + 12, "Esc fecha. Ctrl+V cola. Tab vai para o próximo campo.", texto_w, CINZA)
```

Texto do rodapé: erro ao salvar, aviso de não salvo (na vertical) ou as dicas de teclado.

### Linhas 227 a 228

```python
        f.terminar()
        f.fim_do_quadro()
```

Termina o rodapé e o quadro.

### Linhas 229 a 230

```python
        if self.original is None:
            self.original = self._foto()
```

Tira a foto original no primeiro quadro.

### Linha 232

```python
    # ---------- abas ----------
```

Comentário: abas.

### Linha 233

```python
    def aba_inicio(self, x, y):
```

Aba Início.

### Linhas 234 a 240

```python
        f = self.form
        if self.primeira_vez:
            y = f.secao(x, y, "Bem-vindo ao PixelDigest!", LARGURA)
            y = f.paragrafo(x, y, "Vamos deixar tudo pronto em poucos passos. Siga as abas da esquerda de cima para baixo: "
                                  "Clima, Horários, Notificações, Empresas e Chaves de API. Cada aba tem um botão para testar. "
                                  "No fim, clique em Salvar e aplicar.", LARGURA, BRANCO) + 16
            y = f.paragrafo(x, y, "Só quer ver funcionando? Ligue o Modo demonstração abaixo e salve.", LARGURA, AMARELO) + 20
```

Na primeira vez, mostra boas-vindas e o passo a passo.

### Linhas 241 a 244

```python
        y = f.secao(x, y, "Você", LARGURA)
        f.texto(x, y, "Seu nome (aparece no bom dia)")
        self.cfg["usuario"]["nome"] = f.campo("nome", x, y + 22, 420, self.cfg["usuario"]["nome"], dica="ex.: Felipe")
        y += 80
```

Campo do nome.

### Linhas 245 a 246

```python
        self.cfg["demo"] = f.alternar("demo", x, y, self.cfg["demo"], "Modo demonstração (empresas de exemplo, sem contas reais)")
        y += 40
```

Modo demonstração.

### Linhas 247 a 249

```python
        if sys.platform == "win32":
            self.iniciar_windows = f.alternar("win", x, y, self.iniciar_windows, "Abrir sozinho quando o Windows ligar")
            y += 40
```

No Windows, o interruptor de abrir com o Windows.

### Linha 250

```python
        y = self._tela(x, y)
```

Seção da tela (orientação e resolução).

### Linhas 251 a 253

```python
        y = f.secao(x, y + 10, "Fuso horário", LARGURA)
        y = f.paragrafo(x, y, "Ajustado sozinho quando você escolhe o local do clima. Mude aqui se precisar.", LARGURA)
        self.cfg["usuario"]["fuso"] = f.opcoes("fuso", x, y + 6, self.cfg["usuario"]["fuso"], FUSOS, 200, 4)
```

Fuso horário.

### Linha 254

```python
        return y + 6 + 42 * 3
```

Devolve o y final.

### Linha 256

```python
    def _tela(self, x, y):
```

Seção Tela.

### Linha 257

```python
        """Orientação, resolução e tela cheia (o layout se ajusta como uma media query)."""
```

Docstring.

### Linha 258

```python
        from .tela import ORIENTACOES, RESOLUCOES
```

Importa as opções de orientação e resolução.

### Linhas 259 a 262

```python
        f, t = self.form, self.cfg["tela"]
        y = f.secao(x, y + 10, "Tela", LARGURA)
        y = f.paragrafo(x, y, "Automática: o layout fica vertical quando a janela é mais alta que larga, e horizontal "
                              "no contrário. Dá para redimensionar a janela arrastando a borda.", LARGURA)
```

Atalhos, título e explicação.

### Linhas 263 a 264

```python
        t["orientacao"] = f.opcoes("orient", x, y + 6, t["orientacao"], ORIENTACOES, 200, 4)
        y += 56
```

Botões de orientação.

### Linhas 265 a 268

```python
        f.texto(x, y, "Tamanho da janela ao abrir")
        lista = RESOLUCOES["vertical" if t["orientacao"] == "vertical" else "horizontal"]
        if t["orientacao"] == "automatica":
            lista = RESOLUCOES["horizontal"] + RESOLUCOES["vertical"]
```

Resoluções conforme a orientação (na automática, todas).

### Linha 269

```python
        escolhas = [(r, r.replace("x", " x ")) for r in lista]
```

Texto mostrado com espaços em volta do "x".

### Linhas 270 a 271

```python
        if t["resolucao"] not in lista:
            t["resolucao"] = lista[1]
```

Se a resolução salva não está na lista, usa a segunda (a padrão de cada grupo).

### Linhas 272 a 273

```python
        t["resolucao"] = f.opcoes("resol", x, y + 26, t["resolucao"], escolhas, 200, 4)
        y += 26 + 42 * ((len(escolhas) + 3) // 4) + 8
```

Botões de resolução e cálculo da altura usada (linhas de 4).

### Linha 274

```python
        t["tela_cheia"] = f.alternar("cheia", x, y, t["tela_cheia"], "Tela cheia (ocupa o monitor inteiro)")
```

Tela cheia.

### Linha 275

```python
        return y + 40
```

Devolve.

### Linha 277

```python
    def aba_clima(self, x, y):
```

Aba Clima.

### Linhas 278 a 281

```python
        f = self.form
        y = f.secao(x, y, "Local do clima e tempo", LARGURA)
        y = f.paragrafo(x, y, "Digite um endereço, bairro ou cidade e clique em Buscar. Depois escolha o resultado certo.", LARGURA)
        self.busca = f.campo("busca", x, y + 8, 520, self.busca, dica="ex.: Av. Paulista 1000, São Paulo")
```

Título, explicação e campo de busca.

### Linhas 282 a 284

```python
        if f.botao("buscar", x + 532, y + 8, 120, "Buscar"):
            self.rodar("buscar", assistente.buscar_endereco, self.busca,
                       depois=lambda r: self.dados.__setitem__("enderecos", r) or f"{len(r)} resultado(s). Clique no certo:")
```

Botão Buscar: roda a busca de endereço e guarda os resultados. O truque `__setitem__(...) or texto` guarda e depois devolve o texto, numa `lambda` de uma linha (o `__setitem__` devolve `None`).

### Linhas 285 a 287

```python
        if f.botao("aqui", x + 664, y + 8, 236, "Minha localização"):
            self.rodar("buscar", assistente.minha_localizacao,
                       depois=lambda r: self.dados.__setitem__("enderecos", [r]) or "Achei pela internet. Confirme clicando:")
```

Botão Minha localização, pelo IP.

### Linha 288

```python
        y = f.status(x, y + 52, self.mensagens.get("buscar")) + 6
```

Mensagem do resultado.

### Linhas 289 a 293

```python
        for i, r in enumerate(self.dados.get("enderecos", [])):
            rotulo = font.cortar(r["local"], LARGURA - 30)
            if f.botao(f"end{i}", x, y, LARGURA, rotulo, (120, 200, 255)):
                self.escolher_local(r)
            y += 42
```

Cada resultado vira um botão; clicar escolhe o local.

### Linhas 294 a 298

```python
        y = f.secao(x, y + 14, "Escolhido", LARGURA)
        c = self.cfg["clima"]
        y = f.paragrafo(x, y, c.get("local") or "nenhum", LARGURA, BRANCO)
        if c.get("lat") is not None:
            y = f.paragrafo(x, y, f"coordenadas {c['lat']}, {c['lon']}  |  fuso {self.cfg['usuario']['fuso']}", LARGURA)
```

Mostra o local escolhido e as coordenadas.

### Linhas 299 a 303

```python
        if f.botao("climaagora", x, y + 10, 220, "Ver o clima agora"):
            def ver():
                k = weather.buscar(self.cfg["clima"], self.cfg["usuario"]["fuso"])
                return f"Agora em {k.cidade}: {k.temperatura:.0f}°, {k.descricao}, chuva {k.prob_chuva}%"
            self.rodar("climaagora", ver)
```

Botão "Ver o clima agora": busca e mostra temperatura, descrição e chance de chuva.

### Linha 304

```python
        return f.status(x, y + 56, self.mensagens.get("climaagora"))
```

Mensagem do resultado.

### Linha 306

```python
    def escolher_local(self, r):
```

Escolhe um local.

### Linhas 307 a 308

```python
        self.cfg["clima"] = {"local": r["local"], "cidade": r.get("cidade") or r["local"].split(",")[0],
                             "lat": r["lat"], "lon": r["lon"]}
```

Grava local, cidade e coordenadas.

### Linha 309

```python
        self.dados["enderecos"] = []
```

Limpa a lista de resultados.

### Linhas 310 a 312

```python
        if r.get("fuso"):
            self.cfg["usuario"]["fuso"] = r["fuso"]
            self.mensagens["buscar"] = ("Local escolhido!", VERDE)
```

Se o resultado trouxe o fuso, usa.

### Linhas 313 a 318

```python
        else:
            def ajustar(fuso):
                if fuso:
                    self.cfg["usuario"]["fuso"] = fuso
                return f"Local escolhido! Fuso: {fuso}"
            self.rodar("buscar", assistente.fuso_do_local, r["lat"], r["lon"], depois=ajustar)
```

Senão, pergunta o fuso ao Open-Meteo em segundo plano e aplica.

### Linha 320

```python
    def aba_horarios(self, x, y):
```

Aba Horários.

### Linhas 321 a 327

```python
        f = self.form
        h = self.cfg["horarios"]
        y = f.secao(x, y, "Animações e resumos do dia", LARGURA)
        f.texto(x, y + 10, "Bom dia (resumo da manhã)")
        h["inicio_dia"] = f.hora("ini", x + 420, y, h["inicio_dia"])
        f.texto(x, y + 60, "Fim do expediente")
        h["fim_dia"] = f.hora("fim", x + 420, y + 50, h["fim_dia"])
```

Seletores de horário do bom dia e do fim do expediente.

### Linhas 328 a 333

```python
        y = f.secao(x, y + 110, "Horário de trabalho", LARGURA)
        y = f.paragrafo(x, y, "O agendador só sugere reuniões dentro deste horário, de segunda a sexta.", LARGURA)
        f.texto(x, y + 18, "Das")
        h["expediente"][0] = f.hora("exp0", x + 60, y + 8, h["expediente"][0])
        f.texto(x + 240, y + 18, "até")
        h["expediente"][1] = f.hora("exp1", x + 300, y + 8, h["expediente"][1])
```

Horário de trabalho (início e fim do expediente).

### Linha 334

```python
        return y + 60
```

Devolve.

### Linha 336

```python
    def aba_notificacoes(self, x, y):
```

Aba Notificações.

### Linha 337

```python
        f, n, ch = self.form, self.cfg["notificacoes"], self.chaves
```

Atalhos.

### Linhas 338 a 342

```python
        y = f.secao(x, y, "Discord", LARGURA)
        n["discord"] = f.alternar("ndisc", x, y, n["discord"], "Mandar os avisos para um canal do Discord")
        y += 40
        if n["discord"]:
            y = self._discord(x, y)
```

Discord: interruptor e, se ligado, a seção do webhook.

### Linhas 343 a 345

```python
        y = f.secao(x, y + 10, "Celular (app ntfy, grátis)", LARGURA)
        n["celular"] = f.alternar("ncel", x, y, n["celular"], "Mandar os avisos para o celular")
        y += 40
```

Celular: interruptor.

### Linhas 346 a 349

```python
        if n["celular"]:
            topo = y
            y = f.paragrafo(x, y, "1. Instale o app ntfy (Play Store).  2. Toque em + e digite o tópico abaixo, "
                                  "ou leia o QR code com a câmera.  3. Clique em Testar.", 560)
```

Se ligado: passo a passo.

### Linhas 350 a 353

```python
            f.texto(x, y + 8, "Tópico (funciona como senha, não divulgue)")
            ch["NTFY_TOPIC"] = f.campo("topico", x, y + 30, 420, ch["NTFY_TOPIC"], dica="clique em Gerar")
            if f.botao("gertop", x + 430, y + 30, 120, "Gerar"):
                ch["NTFY_TOPIC"] = assistente.novo_topico()
```

Campo do tópico e botão Gerar.

### Linhas 354 a 356

```python
            if f.botao("testcel", x, y + 76, 220, "Testar celular"):
                self.rodar("testcel", assistente.testar_ntfy, ch["NTFY_SERVER"], ch["NTFY_TOPIC"], ch["NTFY_TOKEN"])
            y = f.status(x, y + 120, self.mensagens.get("testcel"))
```

Botão Testar celular.

### Linhas 357 a 359

```python
            if ch["NTFY_TOPIC"]:
                lado = f.qrcode(x + 640, topo, f"{ch['NTFY_SERVER'].rstrip('/')}/{ch['NTFY_TOPIC']}", 5) or 0
                y = max(y, topo + lado + 10)
```

QR code do endereço do tópico, para assinar com a câmera do celular.

### Linhas 360 a 362

```python
        y = f.secao(x, y + 10, "Alarme do celular", LARGURA)
        n["ouvir_alarme"] = f.alternar("nalarm", x, y, n["ouvir_alarme"], "Mostrar na tela quando o alarme do celular tocar")
        y += 40
```

Alarme do celular: interruptor.

### Linhas 363 a 365

```python
        if n["ouvir_alarme"]:
            if not ch["NTFY_TOPIC_ALARME"]:
                ch["NTFY_TOPIC_ALARME"] = assistente.novo_topico("pixeldigest-alarme")
```

Se ligado e ainda sem tópico do alarme, gera um.

### Linha 366

```python
            url = assistente.endereco_alarme(ch["NTFY_SERVER"], ch["NTFY_TOPIC_ALARME"])
```

Endereço que vai no MacroDroid.

### Linhas 367 a 372

```python
            topo = y
            y = f.paragrafo(x, y, "No celular, abra o MacroDroid e crie uma macro:", 600, BRANCO)
            y = f.paragrafo(x, y, "1. Gatilho: Notificação recebida, app Relógio, texto contém \"Alarme\".", 600)
            y = f.paragrafo(x, y, "2. Ação: Requisição HTTP (GET ou POST, tanto faz) no endereço abaixo. "
                                  "Para não digitar errado, aponte a câmera para o QR code, copie e cole.", 600)
            y = f.paragrafo(x, y + 4, url, 600, AMARELO, 1)
```

Passo a passo do MacroDroid e o endereço em amarelo.

### Linhas 373 a 375

```python
            if f.botao("copiaalarm", x, y + 8, 170, "Copiar endereço"):
                copiar(url)
                self.mensagens["testalarm"] = ("endereço copiado", VERDE)
```

Copiar endereço.

### Linhas 376 a 379

```python
            if f.botao("testalarm", x + 180, y + 8, 200, "Testar alarme agora"):
                self.rodar("testalarm", assistente.testar_ntfy, ch["NTFY_SERVER"], ch["NTFY_TOPIC_ALARME"],
                           ch["NTFY_TOKEN"], "Alarme", "Teste do alarme",
                           depois=lambda r: "enviado pelo PC! Se já salvou, o despertador aparece na tela")
```

Testar alarme: publica no tópico do alarme a partir do PC.

### Linhas 380 a 382

```python
            if f.botao("chegou", x, y + 50, 380, "Ver o que chegou do celular"):
                self.rodar("testalarm", assistente.ultimas_mensagens, ch["NTFY_SERVER"], ch["NTFY_TOPIC_ALARME"],
                           ch["NTFY_TOKEN"], aguarde="consultando o ntfy...")
```

Ver o que chegou do celular nas últimas 24 horas.

### Linhas 383 a 388

```python
            ouvinte = getattr(self.app.motor, "alarme", None)
            if ouvinte is not None and getattr(ouvinte, "conectado", False):
                estado = "O PC está escutando o celular agora." + (f" Último alarme: {ouvinte.ultima[0]}" if ouvinte.ultima else "")
                f.texto(x, y + 96, estado, VERDE, 1)
            else:
                f.texto(x, y + 96, "O PC ainda não está escutando (salve as configurações).", AMARELO, 1)
```

Mostra se o PC está escutando o tópico agora (e a hora do último alarme).

### Linha 389

```python
            y = f.status(x, y + 122, self.mensagens.get("testalarm"))
```

Mensagem.

### Linhas 390 a 391

```python
            lado = f.qrcode(x + 640, topo, url, 3) or 0
            y = max(y, topo + lado + 10)
```

QR code do endereço.

### Linhas 392 a 396

```python
        y = f.secao(x, y + 10, "Avançado (opcional)", LARGURA)
        f.texto(x, y, "Servidor ntfy")
        ch["NTFY_SERVER"] = f.campo("ntfysrv", x, y + 22, 420, ch["NTFY_SERVER"])
        f.texto(x + 470, y, "Token do ntfy")
        ch["NTFY_TOKEN"] = f.campo("ntfytok", x + 470, y + 22, 420, ch["NTFY_TOKEN"], secreto=True, dica="vazio no ntfy.sh")
```

Avançado: servidor e token do ntfy.

### Linha 397

```python
        return y + 70
```

Devolve.

### Linha 399

```python
    def _discord(self, x, y):
```

Seção do Discord (usada em duas abas).

### Linhas 400 a 403

```python
        f = self.form
        y = f.paragrafo(x, y, "No Discord: editar canal > Integrações > Webhooks > Novo webhook > Copiar URL. Cole aqui:", LARGURA)
        self.chaves["DISCORD_WEBHOOK_URL"] = f.campo("webhook", x, y + 8, 760, self.chaves["DISCORD_WEBHOOK_URL"],
                                                    secreto=True, dica="https://discord.com/api/webhooks/...")
```

Passo a passo e campo secreto do webhook.

### Linhas 404 a 405

```python
        if f.botao("testdisc", x, y + 52, 220, "Testar Discord"):
            self.rodar("testdisc", assistente.testar_discord, self.chaves["DISCORD_WEBHOOK_URL"].strip())
```

Botão Testar Discord.

### Linha 406

```python
        return f.status(x, y + 96, self.mensagens.get("testdisc")) + 6
```

Mensagem.

### Linha 408

```python
    def aba_empresas(self, x, y):
```

Aba Empresas.

### Linhas 409 a 411

```python
        f = self.form
        y = f.paragrafo(x, y, "Adicione as empresas em que você trabalha e ligue os serviços que cada uma usa. "
                              "As chaves de cada serviço ficam na aba Chaves de API.", LARGURA) + 10
```

Explicação.

### Linha 412

```python
        for i, emp in enumerate(list(self.cfg["empresas"])):
```

Para cada empresa (em cópia da lista, porque ela pode ser removida no meio).

### Linhas 413 a 414

```python
            topo = y
            pygame.draw.rect(f.tela, config.cor_rgb(emp.get("cor", "#5ab0ff")), f.r(x - 10, topo, 4, 10))
```

Faixa colorida à esquerda.

### Linhas 415 a 417

```python
            f.texto(x, y, "Nome da empresa")
            novo_nome = f.campo(f"emp{i}nome", x, y + 22, 420, emp["nome"], dica="ex.: Minha Empresa")
            emp["nome"] = novo_nome
```

Nome da empresa.

### Linhas 418 a 419

```python
            f.texto(x + 470, y, "Cor")
            emp["cor"] = f.cores(f"emp{i}cor", x + 470, y + 24, emp.get("cor", PALETA[0]))
```

Cor.

### Linhas 420 a 423

```python
            y += 72
            emp["ativa"] = f.alternar(f"emp{i}ativa", x, y, emp.get("ativa", True),
                                      "Empresa ativa" if emp.get("ativa", True) else "Desligada: nada desta empresa é buscado")
            y += 40
```

Interruptor de empresa ativa.

### Linhas 424 a 425

```python
            f.texto(x, y, "Serviços que essa empresa usa:")
            y += 24
```

Título dos serviços.

### Linha 426

```python
            ligados = {c["tipo"] for c in emp["conectores"]}
```

Tipos já ligados.

### Linhas 427 a 432

```python
            for j, (tipo, rotulo) in enumerate(SERVICOS):
                marcado, _ = f.chip(f"emp{i}{tipo}", x + (j % 3) * 300, y + (j // 3) * 38, rotulo, tipo in ligados)
                if marcado and tipo not in ligados:
                    emp["conectores"].append(servico_novo(tipo, emp["nome"] or f"empresa{i}"))
                elif not marcado and tipo in ligados:
                    emp["conectores"] = [c for c in emp["conectores"] if c["tipo"] != tipo]
```

Um chip por serviço. Marcar acrescenta um serviço novo com as opções iniciais; desmarcar remove.

### Linha 433

```python
            y += 38 * ((len(SERVICOS) + 2) // 3) + 8
```

Altura usada pelos chips.

### Linhas 434 a 441

```python
            ms = next((c for c in emp["conectores"] if c["tipo"] == "microsoft"), None)
            if ms:
                f.texto(x, y, "No Outlook + Teams, usar:")
                y += 26
                for k, (chave, rotulo) in enumerate([("email", "E-mails"), ("agenda", "Agenda"), ("teams", "Chats do Teams"),
                                                     ("agendador", "Agendador de reuniões")]):
                    ms[chave], _ = f.chip(f"emp{i}ms{chave}", x + (k % 2) * 300, y + (k // 2) * 38, rotulo, ms.get(chave, True))
                y += 84
```

Se tem Microsoft, chips das partes a usar (e-mails, agenda, Teams, agendador).

### Linhas 442 a 448

```python
            rotulo = "Clique de novo para confirmar" if self.confirmar_remover == i else "Remover empresa"
            if f.botao(f"emp{i}rem", x, y, 300, rotulo, VERMELHO):
                if self.confirmar_remover == i:
                    self.cfg["empresas"].pop(i)
                    self.confirmar_remover = None
                    return y
                self.confirmar_remover = i
```

Remover empresa com confirmação: o primeiro clique troca o texto, o segundo remove.

### Linha 449

```python
            pygame.draw.rect(f.tela, config.cor_rgb(emp.get("cor", "#5ab0ff")), f.r(x - 10, topo, 4, y + 34 - topo))
```

Faixa colorida com a altura total do bloco.

### Linha 450

```python
            y += 60
```

Espaço entre empresas.

### Linhas 451 a 454

```python
        if f.botao("addemp", x, y, 300, "+ Adicionar empresa", VERDE, h=40):
            n = len(self.cfg["empresas"])
            self.cfg["empresas"].append({"nome": "", "cor": PALETA[n % len(PALETA)], "conectores": []})
            self.mensagens.pop("addemp", None)
```

Adicionar empresa com a próxima cor da paleta.

### Linha 455

```python
        return y + 50
```

Devolve.

### Linha 457

```python
    def aba_chaves(self, x, y):
```

Aba Chaves de API.

### Linhas 458 a 460

```python
        f = self.form
        y = f.paragrafo(x, y, "Todas as chaves de API ficam aqui. Elas são gravadas só no arquivo .env do seu "
                              "computador (nunca no GitHub). Use os botões Conectar e Testar para conferir.", LARGURA) + 8
```

Explicação: as chaves ficam só no `.env` do computador.

### Linhas 461 a 462

```python
        y = f.secao(x, y, "Discord", LARGURA)
        y = self._discord(x, y)
```

Discord.

### Linhas 463 a 468

```python
        y = f.secao(x, y + 6, "Celular (ntfy)", LARGURA)
        f.texto(x, y, "Tópico das notificações")
        self.chaves["NTFY_TOPIC"] = f.campo("topico2", x, y + 22, 420, self.chaves["NTFY_TOPIC"], dica="gere na aba Notificações")
        f.texto(x + 470, y, "Token do ntfy (opcional)")
        self.chaves["NTFY_TOKEN"] = f.campo("ntfytok2", x + 470, y + 22, 420, self.chaves["NTFY_TOKEN"], secreto=True)
        y += 76
```

ntfy: tópico e token.

### Linha 469

```python
        y = self._chaves_claude(x, y)
```

Claude.

### Linhas 470 a 471

```python
        if not self.cfg["empresas"]:
            return f.paragrafo(x, y + 10, "Nenhuma empresa ainda. Adicione na aba Empresas.", LARGURA, AMARELO)
```

Sem empresas, avisa.

### Linhas 472 a 476

```python
        for i, emp in enumerate(self.cfg["empresas"]):
            if not emp.get("ativa", True):
                y = f.secao(x, y + 10, f"{emp['nome']}: desligada", LARGURA)
                y = f.paragrafo(x, y, "Ligue a empresa na aba Empresas para configurar as chaves dela.", LARGURA) + 6
                continue
```

Empresa desligada: mostra só o aviso.

### Linhas 477 a 480

```python
            for con in emp["conectores"]:
                titulo = f"{emp['nome'] or 'Empresa sem nome'}: {dict(SERVICOS)[con['tipo']]}"
                y = f.secao(x, y + 10, titulo, LARGURA)
                y = getattr(self, f"_chaves_{con['tipo']}")(f"{i}{con['tipo']}", emp, con, x, y)
```

Para cada serviço, um título e a seção específica. `getattr(self, f"_chaves_{tipo}")` chama o método pelo nome montado (ex.: `_chaves_slack`).

### Linhas 481 a 483

```python
                if f.botao(f"t{i}{con['tipo']}", x, y, 260, "Testar este serviço"):
                    self.rodar(f"t{i}{con['tipo']}", lambda e=emp, c=con: assistente.testar_servico(
                        c["tipo"], e["nome"], copy.deepcopy(c), self._cfg_pronto()))
```

Botão Testar este serviço: roda `testar_servico` com uma cópia das opções. Os argumentos padrão `e=emp, c=con` da `lambda` congelam os valores do laço (sem isso, todas as `lambda` usariam a última empresa).

### Linha 484

```python
                y = f.status(x, y + 44, self.mensagens.get(f"t{i}{con['tipo']}")) + 4
```

Mensagem.

### Linha 485

```python
        return y
```

Devolve.

### Linha 487

```python
    def _segredo(self, id_, con, campo, x, y, w, rotulo, dica):
```

Campo de chave secreta.

### Linha 488

```python
        """Campo de chave secreta: o valor vai para self.chaves[nome da variável]."""
```

Docstring.

### Linha 489

```python
        nome = con.setdefault(f"{campo}_env", nome_segredo(id_, campo))
```

Nome da variável: o que já está nas opções ou um novo (`setdefault` grava se faltar).

### Linhas 490 a 492

```python
        self.form.texto(x, y, rotulo)
        self.chaves[nome] = self.form.campo(id_ + campo, x, y + 22, w, self.chaves.get(nome, os.getenv(nome, "")),
                                            secreto=True, dica=dica)
```

Campo secreto; o valor vai para o dicionário de chaves.

### Linha 493

```python
        return self.chaves[nome]
```

Devolve.

### Linha 495

```python
    def _chaves_slack(self, id_, emp, con, x, y):
```

Seção do Slack.

### Linhas 496 a 500

```python
        f = self.form
        y = f.paragrafo(x, y, "Use o token de USUÁRIO (xoxp-): ele lê como você, então aparecem seus canais privados "
                              "e suas DMs. No app em api.slack.com/apps, em OAuth & Permissions > User Token Scopes, "
                              "adicione channels:history, channels:read, groups:history, groups:read, im:history, "
                              "im:read, mpim:history, mpim:read e users:read. Reinstale e copie o User OAuth Token.", LARGURA)
```

Instruções com os escopos necessários.

### Linhas 501 a 502

```python
        if f.botao(id_ + "guia", x, y + 6, 240, "Abrir api.slack.com"):
            webbrowser.open("https://api.slack.com/apps")
```

Abrir api.slack.com.

### Linhas 503 a 504

```python
        y += 50
        token = self._segredo(id_, con, "token", x, y, 700, "Token do Slack (de usuário, começa com xoxp-)", "xoxp-...")
```

Campo do token.

### Linha 505

```python
        if f.botao(id_ + "con", x + 710, y + 22, 180, "Conectar"):
```

Botão Conectar.

### Linhas 506 a 517

```python
            def pronto(r, c=con, k=id_):
                texto, canais, usuario = r
                self.dados[k + "canais"] = canais
                if usuario:                      # token de usuário: o ID de membro é o do próprio token
                    c["meu_id"] = usuario
                # tira da seleção canais que não existem mais (ou que este token não enxerga)
                existentes = {cid for cid, _ in canais}
                sumidos = [cid for cid in c.get("canais", []) if cid not in existentes]
                c["canais"] = [cid for cid in c.get("canais", []) if cid in existentes]
                if sumidos:
                    texto += f". Removi {len(sumidos)} canal(is) que não existem mais"
                return f"{texto}. Marque os canais que quer acompanhar:"
```

Função que trata o resultado: guarda os canais, usa o id de membro do próprio token, remove da seleção canais que não existem mais e devolve o texto.

### Linha 518

```python
            self.rodar(id_ + "con", assistente.slack_conectar, token.strip(), depois=pronto)
```

Roda a conexão em segundo plano.

### Linha 519

```python
        y = f.status(x, y + 66, self.mensagens.get(id_ + "con"))
```

Mensagem.

### Linhas 520 a 521

```python
        canais = self.dados.get(id_ + "canais")
        escolhidos = set(con.get("canais", []))
```

Canais disponíveis e escolhidos.

### Linhas 522 a 535

```python
        if canais:
            cx, cy = x, y + 4
            for cid, nome in canais:
                w = Form.largura_chip("#" + nome)
                if cx + w > x + LARGURA:
                    cx, cy = x, cy + 38
                marcado, w = f.chip(id_ + cid, cx, cy, "#" + nome, cid in escolhidos)
                if marcado:
                    escolhidos.add(cid)
                else:
                    escolhidos.discard(cid)
                cx += w + 8
            con["canais"] = sorted(escolhidos)
            y = cy + 44
```

Desenha um chip por canal, quebrando a linha quando não cabe, e atualiza a seleção.

### Linhas 536 a 537

```python
        elif escolhidos:
            y = f.paragrafo(x, y + 4, f"{len(escolhidos)} canal(is) escolhido(s). Clique em Conectar para mudar.", LARGURA) + 6
```

Sem a lista carregada, mostra quantos estão escolhidos.

### Linhas 538 a 539

```python
        f.texto(x, y + 4, "Seu ID de membro no Slack (para saber quando te marcam)")
        con["meu_id"] = f.campo(id_ + "meuid", x, y + 26, 420, con.get("meu_id", ""), dica="U0123... (perfil > Copiar ID)")
```

Campo do id de membro.

### Linhas 540 a 541

```python
        con["incluir_dms"] = f.alternar(id_ + "dms", x + 450, y + 30, con.get("incluir_dms", False),
                                        "Ler DMs e grupos")
```

Interruptor de ler DMs e grupos.

### Linha 542

```python
        return y + 76
```

Devolve.

### Linha 544

```python
    def _chaves_clickup(self, id_, emp, con, x, y):
```

Seção do ClickUp.

### Linhas 545 a 547

```python
        f = self.form
        y = f.paragrafo(x, y, "No ClickUp: avatar > Configurações > Apps > API Token > Gerar. Cole abaixo e clique em Conectar.", LARGURA)
        y += 8
```

Instruções.

### Linha 548

```python
        token = self._segredo(id_, con, "token", x, y, 700, "Token pessoal do ClickUp", "pk_...")
```

Campo do token.

### Linhas 549 a 556

```python
        if f.botao(id_ + "con", x + 710, y + 22, 180, "Conectar"):
            def pronto(lista, k=id_, c=con):
                self.dados[k + "ws"] = lista
                if len(lista) == 1:
                    c["equipe_id"] = lista[0][0]
                    return f"conectado ao workspace {lista[0][1]}"
                return "escolha o workspace:"
            self.rodar(id_ + "con", assistente.clickup_workspaces, token.strip(), depois=pronto)
```

Conectar: se houver um workspace só, escolhe sozinho; se houver vários, pede para escolher.

### Linha 557

```python
        y = f.status(x, y + 66, self.mensagens.get(id_ + "con"))
```

Mensagem.

### Linhas 558 a 561

```python
        lista = self.dados.get(id_ + "ws", [])
        if len(lista) > 1:
            con["equipe_id"] = f.opcoes(id_ + "ws", x, y + 4, con.get("equipe_id"), lista, 290, 3)
            y += 4 + 42 * ((len(lista) + 2) // 3)
```

Botões dos workspaces, se houver mais de um.

### Linhas 562 a 563

```python
        f.texto(x, y + 4, f"Workspace escolhido: {con.get('equipe_id') or 'nenhum'}", CINZA)
        return y + 34
```

Workspace escolhido.

### Linha 565

```python
    def _chaves_claude(self, x, y):
```

Seção do Claude.

### Linha 566

```python
        """Chave do Claude para o resumo dos e-mails com IA."""
```

Docstring.

### Linhas 567 a 571

```python
        f = self.form
        y = f.secao(x, y + 6, "Resumo dos e-mails com IA (Claude)", LARGURA)
        y = f.paragrafo(x, y, "Com a chave, os 10 e-mails mais recentes de cada conta viram um resumo dos pontos "
                              "importantes. O texto dos e-mails é enviado para a API da Anthropic. Crie a chave em "
                              "console.anthropic.com > API Keys.", LARGURA)
```

Título e explicação (incluindo o aviso de privacidade).

### Linhas 572 a 573

```python
        if f.botao("claudeguia", x, y + 6, 260, "Abrir console.anthropic.com"):
            webbrowser.open("https://console.anthropic.com/settings/keys")
```

Abrir o console da Anthropic.

### Linhas 574 a 577

```python
        y += 52
        f.texto(x, y, "Chave do Claude")
        self.chaves["ANTHROPIC_API_KEY"] = f.campo("claudekey", x, y + 22, 640, self.chaves.get("ANTHROPIC_API_KEY", ""),
                                                   secreto=True, dica="sk-ant-...")
```

Campo da chave.

### Linhas 578 a 580

```python
        if f.botao("claudetest", x + 720, y + 22, 170, "Testar"):
            self.rodar("claudetest", assistente.testar_claude, self.chaves["ANTHROPIC_API_KEY"].strip(),
                       self.cfg["ia"]["modelo"])
```

Testar a chave com o modelo escolhido.

### Linha 581

```python
        y = f.status(x, y + 64, self.mensagens.get("claudetest"))
```

Mensagem.

### Linhas 582 a 584

```python
        f.texto(x, y + 6, "Modelo")
        from ..resumo_email import MODELOS
        self.cfg["ia"]["modelo"] = f.opcoes("modelo", x + 90, y, self.cfg["ia"]["modelo"], MODELOS, 260, 3)
```

Escolha do modelo.

### Linha 585

```python
        return y + 50
```

Devolve.

### Linha 587

```python
    def _chaves_zoom(self, id_, emp, con, x, y):
```

Seção do Zoom.

### Linhas 588 a 593

```python
        f = self.form
        y = f.paragrafo(x, y, "No Zoom: marketplace.zoom.us > Develop > Build App > Server-to-Server OAuth. Dê um nome, "
                              "em Scopes adicione meeting:read:list_meetings:admin, ative o app e copie Account ID, "
                              "Client ID e Client Secret. Pode precisar do admin da conta Zoom.", LARGURA)
        if f.botao(id_ + "guia", x, y + 6, 260, "Abrir Zoom Marketplace"):
            webbrowser.open("https://marketplace.zoom.us/develop/create")
```

Instruções e botão para o Marketplace.

### Linhas 594 a 598

```python
        y += 54
        f.texto(x, y, "Account ID")
        con["account_id"] = f.campo(id_ + "acc", x, y + 22, 430, con.get("account_id", ""))
        f.texto(x + 460, y, "Client ID")
        con["client_id"] = f.campo(id_ + "cid", x + 460, y + 22, 430, con.get("client_id", ""))
```

Account ID e Client ID (não são secretos, ficam no YAML).

### Linhas 599 a 600

```python
        y += 70
        self._segredo(id_, con, "client_secret", x, y, 500, "Client Secret", "")
```

Client Secret (secreto, vai para o `.env`).

### Linhas 601 a 602

```python
        f.texto(x + 580, y, "Seu e-mail no Zoom")
        con["email"] = f.campo(id_ + "mail", x + 580, y + 22, 310, con.get("email", ""), dica="felipe@...")
```

E-mail no Zoom.

### Linha 603

```python
        return y + 72
```

Devolve.

### Linha 605

```python
    def _chaves_gmail(self, id_, emp, con, x, y):
```

Seção do Gmail.

### Linhas 606 a 611

```python
        f = self.form
        if not con.get("credenciais"):          # outra conta já tem o arquivo? usa o mesmo
            for e in self.cfg["empresas"]:
                for c in e["conectores"]:
                    if c is not con and c.get("tipo") == "gmail" and c.get("credenciais"):
                        con["credenciais"] = c["credenciais"]
```

Se esta conta não tem arquivo de credenciais e outra conta já tem, reaproveita o mesmo (um app do Google serve para várias contas).

### Linhas 612 a 616

```python
        y = f.paragrafo(x, y, "No Google Cloud: crie um projeto, ative Gmail API e Calendar API, configure a tela de "
                              "consentimento e crie um ID do cliente OAuth do tipo App para computador. "
                              "Baixe o arquivo .json e escolha ele aqui.", LARGURA)
        if f.botao(id_ + "guia", x, y + 6, 260, "Abrir Google Cloud"):
            webbrowser.open("https://console.cloud.google.com/apis/credentials")
```

Instruções e botão para o Google Cloud.

### Linhas 617 a 619

```python
        y += 54
        f.texto(x, y, "Arquivo de credenciais OAuth (.json)")
        con["credenciais"] = f.campo(id_ + "cred", x, y + 22, 560, con.get("credenciais", ""), dica="clique em Procurar")
```

Campo do arquivo de credenciais.

### Linhas 620 a 625

```python
        if f.botao(id_ + "proc", x + 570, y + 22, 150, "Procurar..."):
            caminho = escolher_arquivo()
            if caminho:
                destino = config.TOKENS / f"google-cliente-{con.get('conta', 'padrao')}.json"
                shutil.copyfile(caminho, destino)
                con["credenciais"] = str(destino.relative_to(config.ROOT)).replace("\\", "/")
```

Procurar: abre a janela do sistema, copia o arquivo para `tokens/` (fora do GitHub) e grava o caminho relativo com barras normais.

### Linha 626

```python
        conta = config.TOKENS / f"google-{con.get('conta', 'padrao')}.json"
```

Arquivo do login desta conta.

### Linhas 627 a 633

```python
        if f.botao(id_ + "login", x + 730, y + 22, 160, "Fazer login"):
            def entrar(e=emp, c=con):
                from ..connectors.google import GmailConector
                email = GmailConector(e["nome"], c, self._cfg_pronto()).login()
                c["email"] = email
                return f"login feito como {email}!"
            self.rodar(id_ + "login", entrar, aguarde="abrindo o navegador... escolha a conta certa e autorize")
```

Fazer login: em segundo plano, cria o conector e chama `login()` (abre o navegador); grava o e-mail da conta.

### Linha 634

```python
        y = f.status(x, y + 66, self.mensagens.get(id_ + "login"))
```

Mensagem.

### Linhas 635 a 638

```python
        if conta.exists():
            f.texto(x, y + 4, f"Conectado{' como ' + con['email'] if con.get('email') else ''}", VERDE)
        else:
            f.texto(x, y + 4, "Ainda não conectado", AMARELO)
```

Mostra se está conectado e como quem.

### Linhas 639 a 641

```python
        y += 34
        con["agenda"] = f.alternar(id_ + "agenda", x, y, con.get("agenda", True), "Incluir a Google Agenda")
        con["resumo_ia"] = f.alternar(id_ + "ia", x + 400, y, con.get("resumo_ia", True), "Resumir os e-mails com IA")
```

Interruptores de agenda e resumo com IA.

### Linha 642

```python
        return y + 40
```

Devolve.

### Linha 644

```python
    def _chaves_microsoft(self, id_, emp, con, x, y):
```

Seção da Microsoft.

### Linhas 645 a 651

```python
        f = self.form
        y = f.paragrafo(x, y, "No portal do Azure: Entra ID > Registros de aplicativo > Novo registro. Em Autenticação, "
                              "ligue Permitir fluxos de clientes públicos. Em Permissões, adicione (delegadas) User.Read, "
                              "Mail.Read, Calendars.ReadWrite, Chat.Read, ChatMessage.Send, People.Read e "
                              "User.ReadBasic.All. Pode precisar do TI da empresa.", LARGURA)
        if f.botao(id_ + "guia", x, y + 6, 240, "Abrir portal Azure"):
            webbrowser.open("https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade")
```

Instruções e botão para o portal do Azure.

### Linhas 652 a 656

```python
        y += 54
        f.texto(x, y, "ID do aplicativo (cliente)")
        con["client_id"] = f.campo(id_ + "cid", x, y + 22, 430, con.get("client_id", ""), dica="0000-...")
        f.texto(x + 460, y, "ID do diretório (locatário)")
        con["tenant"] = f.campo(id_ + "ten", x + 460, y + 22, 430, con.get("tenant", "organizations"), dica="organizations")
```

Client ID e tenant.

### Linhas 657 a 665

```python
        y += 70
        if f.botao(id_ + "login", x, y, 200, "Fazer login"):
            def entrar(e=emp, c=con, k=id_):
                from ..connectors.microsoft import MicrosoftConector
                MicrosoftConector(e["nome"], c, self._cfg_pronto()).login(
                    mostrar_codigo=lambda site, codigo: self.codigos.__setitem__(k, (site, codigo)))
                self.codigos.pop(k, None)
                return "login feito!"
            self.rodar(id_ + "login", entrar, aguarde="gerando o código...")
```

Fazer login: a função de mostrar o código guarda site e código para a tela exibir; quando termina, apaga o código.

### Linha 666

```python
        y = f.status(x + 214, y + 10, self.mensagens.get(id_ + "login"))
```

Mensagem.

### Linhas 667 a 675

```python
        if id_ in self.codigos:
            site, codigo = self.codigos[id_]
            y = f.paragrafo(x, y + 6, f"Abra {site} e digite o código:", LARGURA, BRANCO)
            f.texto(x, y + 4, codigo, AMARELO, 5)
            if f.botao(id_ + "abrir", x + 420, y, 160, "Abrir site"):
                webbrowser.open(site)
            if f.botao(id_ + "copiar", x + 590, y, 180, "Copiar código"):
                copiar(codigo)
            y += 54
```

Se há um código, mostra grande com os botões Abrir site e Copiar código.

### Linhas 676 a 678

```python
        from ..connectors.microsoft import slug
        conectado = (config.TOKENS / f"ms-{slug(emp['nome'])}.json").exists()   # login salvo
        f.texto(x, y + 6, "Conectado" if conectado else "Ainda não conectado", VERDE if conectado else AMARELO)
```

Mostra se já existe o arquivo de login.

### Linha 679

```python
        return y + 40
```

Devolve.

### Linha 681

```python
    def aba_reunioes(self, x, y):
```

Aba Reuniões.

### Linhas 682 a 685

```python
        f, r = self.form, self.cfg["reunioes"]
        y = f.secao(x, y, "Agendador de reuniões (Outlook + Teams)", LARGURA)
        y = f.paragrafo(x, y, "Usa a empresa com 'Agendador de reuniões' marcado na aba Empresas. Quando alguém pede "
                              "reunião no Teams, ele mostra os horários livres para vocês dois.", LARGURA) + 10
```

Título e explicação.

### Linhas 686 a 689

```python
        f.texto(x, y + 10, "Duração padrão")
        r["duracao_padrao"] = f.numero("dur", x + 360, y, int(r["duracao_padrao"]), 15, 240, 15, "{} min")
        f.texto(x, y + 60, "Quantos dias úteis olhar")
        r["dias_para_frente"] = f.numero("dias", x + 360, y + 50, int(r["dias_para_frente"]), 1, 10, 1, "{} dias")
```

Duração padrão (15 a 240 minutos, de 15 em 15) e quantos dias olhar (1 a 10).

### Linhas 690 a 693

```python
        y += 110
        r["responder_no_teams"] = f.alternar("resp", x, y, r["responder_no_teams"],
                                             "Responder sozinho no chat do Teams com os horários livres")
        y += 46
```

Resposta automática no Teams.

### Linha 694

```python
        f.texto(x, y, "Palavras que indicam pedido de reunião (separadas por vírgula)")
```

Título das palavras.

### Linhas 695 a 697

```python
        # o texto digitado fica guardado como está (com vírgulas e espaços); a lista é derivada dele
        texto = self.dados.setdefault("palavras", ", ".join(r["palavras"]))
        self.dados["palavras"] = f.campo("palavras", x, y + 22, LARGURA, texto)
```

O comentário explica: o texto digitado fica guardado como está, para o campo não "pular" enquanto você digita vírgulas e espaços.

### Linha 698

```python
        r["palavras"] = [p.strip() for p in self.dados["palavras"].split(",") if p.strip()] or r["palavras"]
```

A lista é derivada do texto: separa nas vírgulas e tira espaços. Se ficar vazia, mantém a anterior.

### Linha 699

```python
        return y + 70
```

Devolve.

### Linha 702

```python
def escolher_arquivo():
```

Abre a janela do sistema para escolher um arquivo.

### Linha 703

```python
    """Janela do sistema para escolher o .json do Google."""
```

Docstring.

### Linhas 704 a 706

```python
    try:
        import tkinter
        from tkinter import filedialog
```

Usa o `tkinter` e o diálogo de arquivos.

### Linhas 707 a 709

```python
        raiz = tkinter.Tk()
        raiz.withdraw()
        raiz.attributes("-topmost", True)
```

Cria uma janela escondida e deixa o diálogo por cima de tudo.

### Linhas 710 a 711

```python
        caminho = filedialog.askopenfilename(title="Arquivo de credenciais do Google",
                                             filetypes=[("JSON", "*.json"), ("Todos", "*.*")])
```

Abre o diálogo filtrando arquivos JSON.

### Linhas 712 a 713

```python
        raiz.destroy()
        return caminho
```

Fecha a janela escondida e devolve o caminho.

### Linhas 714 a 715

```python
    except Exception:
        return ""
```

Se algo falhar, devolve vazio.
