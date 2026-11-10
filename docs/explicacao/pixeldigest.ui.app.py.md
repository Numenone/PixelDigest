# `pixeldigest/ui/app.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/ui/app.py)

A janela principal: cenário animado ao fundo, as abas (Início, Resumo do dia, E-mails, Agenda) e a barra de navegação embaixo. Recebe os eventos do Motor e desenha 30 quadros por segundo.

### Linhas 1 a 16

```python
"""Janela principal (pygame-ce): cenário animado + abas + barra de navegação.

Abas (barra fixa embaixo, na horizontal e na vertical):
- Início:       relógio, clima com previsão, próximo compromisso e contadores do dia;
- Resumo do dia: tudo que chegou das empresas (Slack, ClickUp, e-mails...), com Limpar;
- E-mails:      resumo dos e-mails com IA, uma aba por conta;
- Agenda:       compromissos de hoje e amanhã (Google, Zoom, Outlook) e o agendador;
- Configurar:   abre a tela de Configurações.

Tamanho: o app desenha numa tela lógica (1280x720 na horizontal, 720x1280 na
vertical) e ela é ajustada à janela de qualquer resolução (ui/tela.py). Cada aba
calcula as posições a partir do retângulo de conteúdo, então funciona nas duas.

A tela nunca chama APIs diretamente: ela manda comandos para o Motor e
desenha os eventos que ele devolve (fila). Assim a animação não trava.
"""
```

Docstring: descreve cada aba, a tela lógica que se ajusta a qualquer janela e a regra principal: a tela nunca chama APIs, só manda comandos para o Motor e desenha o que ele devolve. Assim a animação não trava esperando a internet.

### Linha 17

```python
import os
```

Importa `os` (conferir se as chaves de notificação existem).

### Linha 18

```python
import queue
```

Importa `queue` (reconhecer a fila vazia).

### Linha 19

```python
import webbrowser
```

Importa `webbrowser` (abrir o link de um item).

### Linha 20

```python
from datetime import datetime, timedelta
```

Importa `datetime` e `timedelta`.

### Linha 22

```python
import pygame
```

Importa o pygame.

### Linhas 24 a 25

```python
from .. import config
from ..config import cor_rgb
```

Importa a configuração e o conversor de cor.

### Linha 26

```python
from ..meetings import interpretar, rotulo
```

Importa a interpretação do comando de reunião (para a prévia ao digitar) e a formatação de horário.

### Linha 27

```python
from ..models import ALTA, URGENTE
```

Importa as prioridades.

### Linha 28

```python
from . import effects, font, icons, tela
```

Importa os módulos de animação, fontes, ícones e tela.

### Linha 29

```python
from .effects import Agendado, Alarme, BomDia, FimDia, Toast
```

Importa as classes de animação usadas aqui.

### Linha 30

```python
from .scene import PRESETS, Cena
```

Importa os climas da demonstração e o cenário.

### Linha 31

```python
from .settings import TelaConfig
```

Importa a tela de Configurações.

### Linhas 33 a 35

```python
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]
```

Nomes dos dias da semana e dos meses em português, para a data por extenso.

### Linhas 36 a 37

```python
NOMES_SERVICO = {"slack": "Slack", "clickup": "ClickUp", "gmail": "Gmail", "microsoft": "Outlook/Teams",
                 "zoom": "Zoom", "google_agenda": "Google", "outlook": "Outlook"}
```

Nome amigável de cada fonte.

### Linha 38

```python
COR_PRIO = {URGENTE: (255, 84, 84), ALTA: (255, 176, 60)}
```

Cor da faixa de prioridade (vermelho para urgente, laranja para alta).

### Linha 39

```python
BRANCO, CINZA, AMARELO, VERDE, VERMELHO, AZUL = (240, 242, 248), (150, 156, 178), (255, 205, 80), (90, 200, 110), (255, 95, 95), (90, 170, 255)
```

Cores usadas na tela, numa linha só com atribuição múltipla.

### Linha 40

```python
SOMBRA = (8, 10, 18)
```

Cor da sombra dos textos.

### Linha 41

```python
EXEMPLO = "reunião com Ana amanhã 30min"
```

Exemplo mostrado no campo de reunião vazio.

### Linhas 42 a 43

```python
ABAS = [("inicio", "Início", "casa"), ("resumo", "Resumo", "lista"), ("emails", "E-mails", "email"),
        ("agenda", "Agenda", "evento"), ("config", "Configurar", "engrenagem")]
```

Abas da barra de navegação: chave, texto e ícone.

### Linha 46

```python
_paineis = {}
```

Cache dos painéis escuros.

### Linha 49

```python
def painel(superficie, rect, alpha=170, borda=None):
```

Desenha um painel escuro semitransparente.

### Linha 50

```python
    """Fundo escuro semitransparente. A Surface é reaproveitada (não cria uma nova a cada quadro)."""
```

Docstring: a superfície é reaproveitada para não criar uma nova a cada quadro.

### Linhas 51 a 57

```python
    chave = (rect.w, rect.h, alpha)
    caixa = _paineis.get(chave)
    if caixa is None:
        if len(_paineis) > 60:
            _paineis.clear()
        caixa = _paineis[chave] = pygame.Surface(rect.size, pygame.SRCALPHA)
        caixa.fill((10, 12, 22, alpha))
```

Procura no cache pelo tamanho e transparência; se não existir, cria (esvaziando o cache se passar de 60).

### Linha 58

```python
    superficie.blit(caixa, rect.topleft)
```

Desenha o painel.

### Linhas 59 a 60

```python
    if borda:
        pygame.draw.rect(superficie, borda, rect, 2)
```

Borda opcional.

### Linha 63

```python
def erro_amigavel(texto):
```

Transforma uma mensagem de erro técnica numa mensagem amigável.

### Linha 64

```python
    """'Minha Empresa / slack: falta a chave PD_...' -> ('Minha Empresa · Slack', 'falta configurar a chave')."""
```

Docstring com exemplo.

### Linha 65

```python
    origem, _, motivo = texto.partition(": ")
```

Separa a origem do motivo no primeiro ": ". `partition` devolve três partes: antes, o separador e depois.

### Linhas 66 a 68

```python
    if " / " in origem:
        empresa, _, tipo = origem.partition(" / ")
        origem = f"{empresa} · {NOMES_SERVICO.get(tipo.split()[0], tipo)}"
```

Se a origem é "Empresa / tipo", troca por "Empresa · Nome do serviço".

### Linhas 69 a 77

```python
    m = motivo.lower()
    if "falta fazer o login" in m:
        motivo = "falta fazer o login"
    elif "falta" in m:
        motivo = "falta configurar a chave"
    elif "acesso negado" in m or "recusad" in m or "invalid_auth" in m:
        motivo = "a chave foi recusada"
    elif "sem resposta" in m or "http 5" in m:
        motivo = "serviço fora do ar ou sem internet"
```

Traduz o motivo para uma frase curta conforme palavras-chave: falta login, falta chave, chave recusada ou serviço fora do ar.

### Linha 78

```python
    return origem, motivo or texto
```

Devolve origem e motivo.

### Linha 81

```python
class App:
```

Classe da janela principal.

### Linha 82

```python
    def __init__(self, cfg, motor, janela=None, demo_forcado=False):
```

Construtor.

### Linhas 83 a 87

```python
        self.cfg = cfg
        self.motor = motor
        self.demo = cfg["demo"]
        self.demo_forcado = demo_forcado      # veio do --demo na linha de comando
        self.nome = cfg["usuario"]["nome"]
```

Guarda configuração, motor, modo demonstração, se o `--demo` veio da linha de comando e o nome.

### Linhas 88 a 89

```python
        self.janela_fixa = janela is not None  # imagens do README usam uma janela fixa
        self.janela = janela or self._criar_janela()
```

Se recebeu uma janela pronta (imagens do README), usa ela; senão cria a janela.

### Linha 90

```python
        pygame.display.set_caption("PixelDigest" + (" (demonstração)" if self.demo else ""))
```

Título da janela.

### Linha 91

```python
        self.relogio = pygame.time.Clock()
```

Relógio que controla os quadros por segundo.

### Linhas 92 a 94

```python
        self.orientacao = None
        self.cena = None
        self.aplicar_layout()
```

Calcula o layout pela primeira vez.

### Linha 95

```python
        self.pagina = "inicio"
```

Aba inicial.

### Linha 96

```python
        self.efeitos, self.toasts = [], []
```

Animações e avisos ativos.

### Linha 97

```python
        self.resumo, self.cores, self.clima = None, {}, None
```

Resumo atual, cores das empresas e clima.

### Linha 98

```python
        self.proposta = None
```

Proposta de reunião aberta.

### Linha 99

```python
        self.texto, self.status = "", ""
```

Texto digitado no campo de reunião e mensagem de status.

### Linhas 100 a 101

```python
        self.preset = None            # demo: clima forçado (F6)
        self.desloc_horas = 0         # demo: adianta o relógio (F7)
```

Clima forçado e horas adiantadas (atalhos da demonstração).

### Linha 102

```python
        self.rolagem = {"resumo": 0, "emails": 0, "agenda": 0}
```

Rolagem de cada aba.

### Linha 103

```python
        self.alvos = []               # (retângulo, ação) clicáveis deste quadro
```

Lista dos retângulos clicáveis deste quadro e a ação de cada um.

### Linha 104

```python
        self.dica = None              # texto completo do item embaixo do mouse
```

Texto da dica que aparece ao passar o mouse.

### Linha 105

```python
        self.config_tela = None       # tela de Configurações, quando aberta
```

Tela de Configurações, quando aberta.

### Linha 106

```python
        self.atualizado = None
```

Hora da última atualização.

### Linha 107

```python
        self.confirmar_limpar = -99999  # momento do 1º clique em "Limpar" (precisa clicar 2 vezes)
```

Momento do primeiro clique em "Limpar tudo". Começa num valor muito negativo para o botão não abrir já pedindo confirmação.

### Linhas 108 a 109

```python
        self.resumos_email = {}       # conta -> {"resumo", "pontos", "gerado", "fonte"}
        self.conta_email = None       # aba escolhida no resumo dos e-mails
```

Resumos dos e-mails por conta e a conta escolhida.

### Linha 110

```python
        self.rodando = True
```

Laço principal ligado.

### Linha 112

```python
    # ---------- janela, orientação e layout (as "media queries") ----------
```

Comentário: janela, orientação e layout.

### Linha 113

```python
    def _criar_janela(self):
```

Cria a janela.

### Linhas 114 a 115

```python
        t = self.cfg.get("tela", {})
        tamanho = tela.tamanho(t.get("resolucao", "1280x720"))
```

Lê a resolução configurada.

### Linhas 116 a 117

```python
        if t.get("tela_cheia"):
            return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
```

Tela cheia: `(0, 0)` usa a resolução do monitor.

### Linha 118

```python
        return pygame.display.set_mode(tamanho, pygame.RESIZABLE)
```

Senão, janela redimensionável (`RESIZABLE`).

### Linha 120

```python
    def aplicar_layout(self):
```

Monta o layout.

### Linha 121

```python
        """Escolhe horizontal/vertical pela configuração (ou pelo formato da janela) e monta as áreas."""
```

Docstring.

### Linha 122

```python
        nova = tela.orientacao(self.cfg.get("tela", {}), self.janela.get_size())
```

Decide a orientação.

### Linhas 123 a 124

```python
        if nova == self.orientacao:
            return
```

Se não mudou, não faz nada.

### Linhas 125 a 127

```python
        self.orientacao = nova
        lw, lh = tela.LOGICO[nova]
        self.tela = pygame.Surface((lw, lh))
```

Guarda e cria a tela lógica no tamanho dessa orientação.

### Linhas 128 a 131

```python
        vertical = nova == "vertical"
        self.nav_h = 116 if vertical else 84
        self.topo_h = 64 if vertical else 60
        m = 16 if vertical else 20
```

Medidas que mudam com a orientação: altura da barra de navegação, altura do topo e margem.

### Linha 132

```python
        self.r_nav = pygame.Rect(0, lh - self.nav_h, lw, self.nav_h)
```

Retângulo da barra de navegação, embaixo.

### Linha 133

```python
        self.r_conteudo = pygame.Rect(m, self.topo_h + 12, lw - 2 * m, lh - self.topo_h - 12 - self.nav_h - 12)
```

Retângulo do conteúdo: entre o topo e a barra, com margens.

### Linhas 134 a 135

```python
        antigo = self.cena
        self.cena = Cena(lw // 4, lh // 4)
```

Cria o cenário com um quarto do tamanho (será ampliado 4 vezes).

### Linhas 136 a 138

```python
        if antigo is not None:                           # mantém o clima que já estava na tela
            self.cena.vis, self.cena.alvo = antigo.vis, antigo.alvo
            self.cena.nascer, self.cena.por = antigo.nascer, antigo.por
```

Se já existia um cenário, mantém o clima que estava na tela.

### Linhas 139 a 141

```python
        effects.CX, effects.LARGURA_TELA = lw // 2, lw
        effects.BANNER_Y = 520 if vertical else 250
        Toast.topo_base = self.r_conteudo.y + 6
```

Ajusta as animações ao novo tamanho (centro, largura, altura do banner e dos avisos).

### Linhas 143 a 145

```python
    def redimensionou(self):
        self.janela = pygame.display.get_surface()
        self.aplicar_layout()
```

Quando a janela é redimensionada: pega a superfície nova e recalcula o layout (a "media query").

### Linha 147

```python
    # ---------- configurações ----------
```

Comentário: configurações.

### Linhas 148 a 150

```python
    def abrir_config(self, primeira_vez=False, aba=0):
        self.config_tela = TelaConfig(self, primeira_vez, self.orientacao)
        self.config_tela.aba = aba
```

Abre a tela de Configurações numa aba.

### Linha 152

```python
    def recarregar(self):
```

Recarrega tudo depois de salvar.

### Linha 153

```python
        """Depois de salvar: lê a configuração nova, ajusta a janela e reinicia o Motor."""
```

Docstring.

### Linha 154

```python
        from ..core import Motor
```

Importa o Motor.

### Linha 155

```python
        tela_antes = dict(self.cfg.get("tela", {}))
```

Guarda as opções de tela de antes.

### Linha 156

```python
        self.motor.encerrar()
```

Para o motor antigo.

### Linhas 157 a 158

```python
        self.cfg = config.carregar(demo=self.demo_forcado)
        self.demo, self.nome = self.cfg["demo"], self.cfg["usuario"]["nome"]
```

Carrega a configuração nova.

### Linhas 159 a 160

```python
        if not self.janela_fixa and self.cfg.get("tela") != tela_antes:
            self.janela = self._criar_janela()
```

Se as opções de tela mudaram, recria a janela.

### Linhas 161 a 162

```python
        self.orientacao = None
        self.aplicar_layout()
```

Força recalcular o layout.

### Linha 163

```python
        pygame.display.set_caption("PixelDigest" + (" (demonstração)" if self.demo else ""))
```

Atualiza o título.

### Linha 164

```python
        self.resumo, self.clima, self.proposta, self.preset = None, None, None, None
```

Limpa o estado antigo.

### Linhas 165 a 166

```python
        self.motor = Motor(self.cfg)
        self.motor.start()
```

Cria e liga um motor novo com a configuração nova.

### Linha 167

```python
        self.toasts.append(Toast("Configurações salvas", "carregando as informações…", VERDE))
```

Aviso de que as configurações foram salvas.

### Linha 169

```python
    # ---------- eventos que vêm do Motor ----------
```

Comentário: eventos do Motor.

### Linha 170

```python
    def receber(self):
```

Lê todos os eventos que chegaram.

### Linhas 171 a 175

```python
        while True:
            try:
                tipo, d = self.motor.eventos.get_nowait()
            except queue.Empty:
                return
```

Tira da fila sem esperar; quando vazia, termina.

### Linhas 176 a 179

```python
            if tipo == "clima":
                self.clima = d["clima"]
                if not self.preset:
                    self.cena.definir_clima(clima=self.clima)
```

Clima: guarda e passa para o cenário (a menos que um clima de demonstração esteja forçado).

### Linhas 180 a 183

```python
            elif tipo == "resumo":
                self.resumo, self.cores = d["resumo"], d["cores"]
                self.atualizado = datetime.now()
                self.status = ""
```

Resumo: guarda, anota a hora e limpa o status.

### Linhas 184 a 185

```python
            elif tipo == "bom_dia":
                self.efeitos.append(BomDia(self.nome, len(d["resumo"].itens)))
```

Bom dia: começa a animação.

### Linhas 186 a 188

```python
            elif tipo == "fim_do_dia":
                self.cena.acender_janelas()
                self.efeitos.append(FimDia())
```

Fim do dia: acende as janelas e começa a animação.

### Linhas 189 a 190

```python
            elif tipo == "toast":
                self.toasts.append(Toast(d["titulo"], d["texto"], cor_rgb(d.get("cor") or "#ff5050")))
```

Aviso: cria um toast com a cor da empresa.

### Linhas 191 a 196

```python
            elif tipo == "proposta":
                self.proposta = d["proposta"]
                self.pagina = "agenda"
                self.status = ""
                if d["proposta"].get("origem") == "teams":
                    self.toasts.append(Toast("Pedido de reunião no Teams", d["proposta"]["pessoa"], (122, 214, 122)))
```

Proposta de reunião: guarda, vai para a aba Agenda e, se veio do Teams, mostra um aviso.

### Linhas 197 a 200

```python
            elif tipo == "agendado":
                self.proposta = None
                self.status = ""
                self.efeitos.append(Agendado(d["pessoa"].split()[0], rotulo(d["horario"]), d["assunto"]))
```

Reunião agendada: fecha a proposta e mostra a animação com o primeiro nome da pessoa.

### Linhas 201 a 204

```python
            elif tipo == "emails":
                self.resumos_email = d["resumos"]
                if self.conta_email not in self.resumos_email:
                    self.conta_email = next(iter(self.resumos_email), None)
```

Resumos de e-mail: guarda e, se a conta escolhida não existe, escolhe a primeira.

### Linhas 205 a 206

```python
            elif tipo == "alarme":
                self.efeitos.append(Alarme(d["titulo"], d["texto"]))
```

Alarme: mostra a animação.

### Linhas 207 a 209

```python
            elif tipo == "erro":
                self.status = ""
                self.toasts.append(Toast("Não deu certo", d["texto"], VERMELHO))
```

Erro: mostra um aviso vermelho.

### Linha 211

```python
    # ---------- teclado e mouse ----------
```

Comentário: teclado e mouse.

### Linha 212

```python
    def tratar(self, ev):
```

Trata um evento.

### Linha 213

```python
        alarme = next((e for e in self.efeitos if isinstance(e, Alarme)), None)
```

Procura um alarme ativo.

### Linhas 214 a 215

```python
        if ev.type == pygame.QUIT:
            self.rodando = False
```

Fechar a janela encerra o laço.

### Linhas 216 a 219

```python
        elif self.config_tela:
            self.config_tela.evento(ev)           # com as Configurações abertas, o teclado é delas
            if not self.config_tela.aberta:
                self.config_tela = None
```

Com as Configurações abertas, o evento vai para elas.

### Linhas 220 a 221

```python
        elif alarme and ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            alarme.fechar()                       # qualquer tecla desliga o alarme
```

Com alarme tocando, qualquer tecla ou clique desliga.

### Linhas 222 a 227

```python
        elif ev.type == pygame.TEXTINPUT:
            if self.pagina != "agenda" or not self.motor.agendador:
                return                            # só a Agenda tem campo de texto
            if self.proposta and not self.texto and ev.text in "123":
                return                            # 1-3 escolhe horário (tratado no KEYDOWN)
            self.texto = (self.texto + ev.text)[:90]
```

Texto digitado: só vale na aba Agenda com agendador. As teclas 1 a 3 com proposta aberta escolhem horário (tratadas em outro lugar). O texto é limitado a 90 caracteres.

### Linhas 228 a 230

```python
        elif ev.type == pygame.MOUSEWHEEL and self.r_conteudo.collidepoint(tela.mouse_pos()):
            if self.pagina in self.rolagem:
                self.rolagem[self.pagina] = max(0, self.rolagem[self.pagina] - ev.y * 40)
```

Rodinha do mouse sobre o conteúdo: rola a aba atual.

### Linhas 231 a 235

```python
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for rect, acao in reversed(self.alvos):   # o que foi desenhado por último está por cima
                if rect.collidepoint(ev.pos):
                    acao()
                    break
```

Clique: procura de trás para frente o retângulo clicado (o último desenhado está por cima) e executa a ação.

### Linhas 236 a 237

```python
        elif ev.type == pygame.KEYDOWN:
            self.tecla(ev)
```

Outras teclas.

### Linhas 239 a 243

```python
    def ir(self, pagina):
        if pagina == "config":
            self.abrir_config()
        else:
            self.pagina = pagina
```

Vai para uma aba (ou abre as Configurações).

### Linha 245

```python
    def tecla(self, ev):
```

Trata as teclas.

### Linhas 246 a 247

```python
        k = ev.key
        digitando = self.pagina == "agenda" and self.texto
```

Tecla e se está digitando na Agenda.

### Linhas 248 a 249

```python
        if k == pygame.K_ESCAPE:
            self.proposta, self.texto = None, ""
```

Esc fecha a proposta e limpa o texto.

### Linhas 250 a 251

```python
        elif k == pygame.K_BACKSPACE and digitando:
            self.texto = self.texto[:-1]
```

Backspace apaga.

### Linhas 252 a 254

```python
        elif k == pygame.K_v and ev.mod & pygame.KMOD_CTRL and self.pagina == "agenda":
            from .widgets import area_de_transferencia
            self.texto = (self.texto + area_de_transferencia().strip())[:90]
```

Ctrl+V cola no campo de reunião.

### Linhas 255 a 258

```python
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER) and digitando:
            self.motor.comandos.put(("reuniao", {"texto": self.texto.strip()}))
            self.status = "procurando horários livres…"
            self.texto = ""
```

Enter manda o comando de reunião para o Motor e mostra o status.

### Linhas 259 a 262

```python
        elif self.proposta and not self.texto and pygame.K_1 <= k <= pygame.K_3:
            i = k - pygame.K_1
            if i < len(self.proposta["horarios"]):
                self.confirmar(self.proposta["horarios"][i])
```

Teclas 1, 2 e 3 confirmam o horário correspondente.

### Linhas 263 a 266

```python
        elif k in (pygame.K_LEFT, pygame.K_RIGHT) and not digitando:
            abas = [a for a, _, _ in ABAS if a != "config"]
            i = abas.index(self.pagina) + (1 if k == pygame.K_RIGHT else -1)
            self.pagina = abas[i % len(abas)]
```

Setas trocam de aba em círculo.

### Linhas 267 a 270

```python
        elif k == pygame.K_F10:
            self.abrir_config()
        elif k == pygame.K_F5:
            self.atualizar()
```

F10 abre as Configurações e F5 atualiza.

### Linhas 271 a 274

```python
        elif self.demo:
            acoes = {pygame.K_F1: "bom_dia", pygame.K_F2: "fim_do_dia", pygame.K_F3: "pedido", pygame.K_F4: "alarme"}
            if k in acoes:
                self.motor.comandos.put(("demo", {"acao": acoes[k]}))
```

Na demonstração, F1 a F4 disparam as ações pelo Motor (os mesmos caminhos do uso real).

### Linhas 275 a 279

```python
            elif k == pygame.K_F6:
                nomes = list(PRESETS) + [None]
                self.preset = nomes[(nomes.index(self.preset) + 1) % len(nomes)]
                self.cena.definir_clima(clima=self.clima, preset=self.preset)
                self.toasts.append(Toast("Clima da demonstração", self.preset or "clima real", AZUL))
```

F6 troca o clima da demonstração em círculo (incluindo voltar ao clima real) e avisa.

### Linhas 280 a 281

```python
            elif k == pygame.K_F7:
                self.desloc_horas = (self.desloc_horas + 3) % 24
```

F7 adianta o relógio em 3 horas.

### Linha 283

```python
    def limpar_tudo(self):
```

Limpar tudo.

### Linhas 284 a 288

```python
        if pygame.time.get_ticks() - self.confirmar_limpar < 4000:
            self.motor.comandos.put(("limpar", {}))
            self.confirmar_limpar = -99999
            self.rolagem["resumo"] = 0
            self.toasts.append(Toast("Resumo limpo", "os itens novos continuam aparecendo aqui", VERDE))
```

Se o segundo clique veio em menos de 4 segundos, manda o comando, zera a rolagem e avisa.

### Linhas 289 a 290

```python
        else:
            self.confirmar_limpar = pygame.time.get_ticks()
```

Senão, guarda o momento do primeiro clique (o botão passa a mostrar "Confirmar?").

### Linhas 292 a 295

```python
    def dispensar(self, item):
        self.motor.comandos.put(("limpar", {"chaves": [item.chave()]}))
        if self.resumo:
            self.resumo.itens = [i for i in self.resumo.itens if i is not item]   # some na hora
```

Tira um item: manda o comando ao Motor e já remove da tela, para sumir na hora.

### Linhas 297 a 299

```python
    def atualizar(self):
        self.motor.comandos.put(("atualizar", {}))
        self.status = "atualizando…"
```

Manda o comando de atualizar.

### Linhas 301 a 303

```python
    def confirmar(self, horario):
        self.motor.comandos.put(("confirmar", {"proposta": self.proposta, "horario": horario}))
        self.status = "agendando…"
```

Manda a confirmação de um horário.

### Linha 305

```python
    # ---------- utilidades de desenho ----------
```

Comentário: utilidades de desenho.

### Linhas 306 a 307

```python
    def agora(self):
        return datetime.now().astimezone() + timedelta(hours=self.desloc_horas)
```

Hora atual mais o deslocamento da demonstração.

### Linhas 309 a 312

```python
    def escrever(self, texto, x, y, escala=2, cor=BRANCO, familia="texto", sombra=SOMBRA):
        surf = font.render(texto, escala, cor, shadow=sombra, familia=familia)
        self.tela.blit(surf, (x, y))
        return surf.get_width()
```

Escreve um texto e devolve a largura.

### Linhas 314 a 316

```python
    def centralizado(self, texto, cx, y, escala=2, cor=BRANCO, familia="texto", sombra=SOMBRA):
        surf = font.render(texto, escala, cor, shadow=sombra, familia=familia)
        self.tela.blit(surf, (cx - surf.get_width() // 2, y))
```

Escreve um texto centralizado.

### Linha 318

```python
    def botao(self, rect, texto, cor, acao, cheio=False):
```

Botão grande.

### Linhas 319 a 324

```python
        sobre = rect.collidepoint(tela.mouse_pos())
        painel(self.tela, rect, 235 if sobre else 190, cor)
        if sobre or cheio:
            pygame.draw.rect(self.tela, cor, rect.inflate(-6, -6))
        t = font.render(texto, 2, (12, 14, 24) if (sobre or cheio) else cor)
        self.tela.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))
```

Painel com borda; com o mouse em cima fica preenchido e o texto escuro.

### Linha 325

```python
        self.alvos.append((rect, acao))
```

Registra o retângulo e a ação para o clique.

### Linhas 327 a 333

```python
    def botao_pequeno(self, rect, texto, cor, acao):
        sobre = rect.collidepoint(tela.mouse_pos())
        pygame.draw.rect(self.tela, cor if sobre else (24, 28, 44), rect)
        pygame.draw.rect(self.tela, cor, rect, 1)
        t = font.render(texto, 1, (12, 14, 24) if sobre else cor)
        self.tela.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))
        self.alvos.append((rect, acao))
```

Botão pequeno, mesma ideia.

### Linhas 335 a 342

```python
    def paragrafo(self, texto, x, y, largura, escala=2, cor=(220, 224, 236), max_linhas=99):
        linhas = font.wrap(texto, largura, escala)
        if len(linhas) > max_linhas:
            linhas = linhas[:max_linhas - 1] + [font.cortar(" ".join(linhas[max_linhas - 1:]), largura, escala)]
        for linha in linhas:
            self.escrever(linha, x, y, escala, cor, sombra=None)
            y += font.altura(escala)
        return y
```

Parágrafo com limite de linhas: se passar, a última linha é cortada com reticências.

### Linha 344

```python
    def cabecalho_painel(self, area, titulo, direita=""):
```

Cabeçalho das abas.

### Linha 345

```python
        """Título da aba dentro do painel + texto à direita. Devolve o y onde começa o conteúdo."""
```

Docstring.

### Linha 346

```python
        painel(self.tela, area, 175 + int(55 * self.cena.escuro))
```

Painel do fundo, mais escuro quando o tempo está escuro (para o texto continuar legível).

### Linhas 347 a 350

```python
        self.escrever(titulo, area.x + 16, area.y + 14, 2, BRANCO, "titulo", sombra=None)
        if direita:
            t = font.render(direita, 1, CINZA)
            self.tela.blit(t, (area.right - t.get_width() - 16, area.y + 16))
```

Título e texto à direita.

### Linha 351

```python
        return area.y + 48
```

Devolve onde o conteúdo começa.

### Linhas 353 a 358

```python
    def noite(self, agora):
        c = self.clima
        if c and c.nascer and c.por_do_sol:
            hora = agora.replace(tzinfo=None)
            return not (c.nascer <= hora <= c.por_do_sol)
        return agora.hour < 6 or agora.hour >= 18
```

Diz se é noite: pelo nascer e pôr do sol reais ou, sem clima, entre 18h e 6h.

### Linhas 360 a 363

```python
    def codigo_clima(self):
        if self.preset:
            return {"sol": 0, "nublado": 3, "chuva": 63, "tempestade": 95}[self.preset]
        return self.clima.codigo if self.clima else 0
```

Código do clima atual (do preset da demonstração ou do clima real).

### Linhas 365 a 366

```python
    def data_extenso(self, agora):
        return f"{DIAS[agora.weekday()].capitalize()}, {agora.day} de {MESES[agora.month - 1]}"
```

Data por extenso, como "Segunda-feira, 10 de novembro".

### Linha 368

```python
    # ---------- topo (abas internas) ----------
```

Comentário: topo.

### Linha 369

```python
    def desenhar_topo(self, agora):
```

Desenha a barra do topo.

### Linhas 370 a 372

```python
        lw = self.tela.get_width()
        painel(self.tela, pygame.Rect(0, 0, lw, self.topo_h), 185)
        pygame.draw.line(self.tela, (60, 70, 100), (0, self.topo_h), (lw, self.topo_h), 2)
```

Painel e linha.

### Linhas 373 a 374

```python
        w = self.escrever(f"{agora:%H:%M}", 18, 10, 4, BRANCO, "titulo")
        self.escrever(self.data_extenso(agora), 26 + w, 20 if self.orientacao == "horizontal" else 14, 1, (200, 206, 222))
```

Hora grande e data.

### Linhas 375 a 382

```python
        x = lw - 18
        if self.clima or self.preset:
            temp = f"{self.clima.temperatura:.0f}°" if self.clima and not self.preset else ""
            t = font.render(temp, 3, BRANCO, familia="titulo")
            x -= t.get_width()
            self.tela.blit(t, (x, 16))
            x -= 46
            self.tela.blit(icons.clima(self.codigo_clima(), self.noite(agora), 40), (x, 10))
```

À direita, temperatura e ícone do clima.

### Linhas 383 a 385

```python
        if self.status:
            s = font.render(self.status, 1, AMARELO)
            self.tela.blit(s, (x - s.get_width() - 16, 22))
```

Mensagem de status em amarelo.

### Linha 387

```python
    # ---------- aba Início ----------
```

Comentário: aba Início.

### Linhas 388 a 393

```python
    def proximo_evento(self, agora):
        if not self.resumo:
            return None
        futuros = [i for i in self.resumo.itens if i.tipo == "evento" and i.quando and i.quando > agora
                   and i.quando.date() == agora.date()]
        return min(futuros, key=lambda i: i.quando, default=None)
```

Próximo compromisso de hoje: o evento futuro mais próximo (`min` com `default=None` se não houver).

### Linha 395

```python
    def contadores(self, agora):
```

Contadores da aba Início.

### Linhas 396 a 400

```python
        itens = self.resumo.itens if self.resumo else []
        urgentes = sum(1 for i in itens if i.prioridade >= URGENTE)
        eventos = sum(1 for i in itens if i.tipo == "evento" and i.quando and i.quando.date() == agora.date())
        tarefas = sum(1 for i in itens if i.tipo == "tarefa")
        importantes = sum(1 for r in self.resumos_email.values() for p in r.get("pontos", []) if p.get("prioridade") == "alta")
```

Conta urgentes, compromissos de hoje, tarefas e pontos de e-mail com prioridade alta.

### Linhas 401 a 402

```python
        return [("Urgentes", urgentes, VERMELHO, "resumo"), ("E-mails importantes", importantes, AMARELO, "emails"),
                ("Compromissos hoje", eventos, AZUL, "agenda"), ("Tarefas abertas", tarefas, VERDE, "resumo")]
```

Devolve cada contador com texto, valor, cor e a aba para onde leva ao clicar.

### Linha 404

```python
    def pagina_inicio(self, agora):
```

Desenha a aba Início.

### Linhas 405 a 406

```python
        c = self.r_conteudo
        vertical = self.orientacao == "vertical"
```

Atalhos.

### Linhas 407 a 417

```python
        if vertical:
            cx = c.centerx
            heroi = pygame.Rect(c.x, c.y, c.w, 420)
            painel(self.tela, heroi, 120)
            self.centralizado(f"{agora:%H:%M}", cx, heroi.y + 24, 10, BRANCO, "titulo")
            self.centralizado(self.data_extenso(agora), cx, heroi.y + 134, 3, (220, 224, 236))
            self.bloco_clima(pygame.Rect(c.x + 20, heroi.y + 190, c.w - 40, 220), agora, previsao=4)
            y = heroi.bottom + 14
            y = self.cartao_proximo(pygame.Rect(c.x, y, c.w, 92), agora) + 14
            self.blocos_contadores(pygame.Rect(c.x, y, c.w, 250), agora, 2)
            self.linha_status(pygame.Rect(c.x, y + 264, c.w, 56))
```

Vertical: relógio enorme centralizado, data, clima com 4 horas de previsão, cartão do próximo compromisso, contadores em 2 colunas e a linha de status, um embaixo do outro.

### Linhas 418 a 427

```python
        else:
            esquerda = pygame.Rect(c.x, c.y, 640, c.h)
            painel(self.tela, esquerda, 120)
            self.escrever(f"{agora:%H:%M}", esquerda.x + 30, esquerda.y + 24, 10, BRANCO, "titulo")
            self.escrever(self.data_extenso(agora), esquerda.x + 36, esquerda.y + 134, 3, (220, 224, 236))
            self.bloco_clima(pygame.Rect(esquerda.x + 30, esquerda.y + 196, esquerda.w - 60, 300), agora, previsao=6)
            direita = pygame.Rect(c.x + 660, c.y, c.w - 660, c.h)
            y = self.cartao_proximo(pygame.Rect(direita.x, direita.y, direita.w, 92), agora) + 14
            self.blocos_contadores(pygame.Rect(direita.x, y, direita.w, 260), agora, 2)
            self.linha_status(pygame.Rect(direita.x, y + 276, direita.w, 56))
```

Horizontal: à esquerda relógio, data e clima com 6 horas; à direita próximo compromisso, contadores e status.

### Linhas 428 a 430

```python
        if self.demo:
            dica = "DEMO · F1 bom dia · F2 18h · F3 pedido · F4 alarme · F6 clima · F7 +3h · setas trocam de aba"
            self.centralizado(font.cortar(dica, c.w - 20, 1), c.centerx, c.bottom - 22, 1, BRANCO)
```

Na demonstração, mostra a lista de atalhos embaixo.

### Linha 432

```python
    def bloco_clima(self, r, agora, previsao):
```

Bloco do clima.

### Linhas 433 a 437

```python
        if self.preset:
            self.tela.blit(icons.clima(self.codigo_clima(), self.noite(agora), 80), (r.x, r.y))
            self.escrever(self.preset.capitalize(), r.x + 96, r.y + 14, 5, BRANCO, "titulo")
            self.escrever("clima da demonstração (F6 troca)", r.x + 98, r.y + 66, 1, CINZA)
            return
```

Clima de demonstração: ícone e nome.

### Linhas 438 a 440

```python
        if not self.clima:
            self.escrever("buscando o clima…", r.x, r.y + 20, 2, CINZA)
            return
```

Sem clima ainda: "buscando...".

### Linhas 441 a 446

```python
        cl = self.clima
        self.tela.blit(icons.clima(cl.codigo, self.noite(agora), 80), (r.x, r.y))
        w = self.escrever(f"{cl.temperatura:.0f}°", r.x + 96, r.y + 6, 7, BRANCO, "titulo")
        self.escrever(font.cortar(cl.descricao.capitalize(), r.w - 120 - w, 3), r.x + 112 + w, r.y + 14, 3)
        self.escrever(f"mín {cl.minima:.0f}° · máx {cl.maxima:.0f}° · chuva {cl.prob_chuva}%", r.x + 112 + w, r.y + 50, 1, (205, 210, 226))
        self.escrever(font.cortar(cl.cidade, r.w - 100, 1), r.x + 98, r.y + 76, 1, CINZA)
```

Ícone, temperatura grande, descrição, mínima, máxima, chance de chuva e cidade.

### Linhas 447 a 450

```python
        y = r.y + 112
        n = min(previsao, len(cl.proximas))
        if not n:
            return
```

Previsão das próximas horas.

### Linha 451

```python
        passo = r.w // n
```

Largura de cada coluna.

### Linhas 452 a 459

```python
        for i, (hora, temp, cod, prob) in enumerate(cl.proximas[:n]):
            cx = r.x + i * passo + passo // 2
            self.centralizado(hora, cx, y, 1, CINZA, sombra=None)
            hora_n = int(hora[:2])
            self.tela.blit(icons.clima(cod, hora_n < 6 or hora_n >= 19, 40), (cx - 20, y + 22))
            if temp is not None:
                self.centralizado(f"{temp:.0f}°", cx, y + 66, 2, BRANCO, sombra=None)
            self.centralizado(f"{prob}%", cx, y + 92, 1, AZUL if prob >= 30 else CINZA, sombra=None)
```

Para cada hora: a hora, o ícone (de noite antes das 6h e depois das 19h), a temperatura e a chance de chuva (azul se 30% ou mais).

### Linha 461

```python
    def cartao_proximo(self, r, agora):
```

Cartão do próximo compromisso.

### Linhas 462 a 465

```python
        painel(self.tela, r, 190)
        prox = self.proximo_evento(agora)
        self.tela.blit(icons.item("evento", 36), (r.x + 16, r.y + 16))
        self.escrever("Próximo compromisso", r.x + 64, r.y + 12, 1, CINZA, sombra=None)
```

Painel, ícone e título.

### Linhas 466 a 467

```python
        if not prox:
            self.escrever("Nada mais na agenda hoje", r.x + 64, r.y + 44, 2, BRANCO, sombra=None)
```

Sem compromisso: avisa.

### Linhas 468 a 476

```python
        else:
            falta = int((prox.quando - agora).total_seconds() // 60)
            cor = VERMELHO if falta <= 15 else (AMARELO if falta <= 60 else VERDE)
            pygame.draw.rect(self.tela, cor, r, 2)
            quando = f"em {falta} min" if falta < 60 else f"às {prox.quando:%H:%M}"
            t = font.render(quando, 3, cor)
            self.tela.blit(t, (r.right - t.get_width() - 16, r.y + 38))
            self.escrever(font.cortar(prox.titulo, r.w - t.get_width() - 100, 2), r.x + 64, r.y + 44, 2, BRANCO, sombra=None)
            self.alvos.append((r, lambda: self.ir("agenda")))
```

Com compromisso: calcula quantos minutos faltam, escolhe a cor (vermelho até 15 min, amarelo até 1 hora, verde depois), desenha borda, "em X min" ou o horário, o título, e torna o cartão clicável para ir à Agenda.

### Linha 477

```python
        return r.bottom
```

Devolve onde o cartão termina.

### Linha 479

```python
    def blocos_contadores(self, r, agora, colunas):
```

Contadores.

### Linhas 480 a 483

```python
        dados = self.contadores(agora)
        linhas = (len(dados) + colunas - 1) // colunas
        w = (r.w - (colunas - 1) * 14) // colunas
        h = (r.h - (linhas - 1) * 14) // linhas
```

Calcula linhas, largura e altura de cada bloco.

### Linha 484

```python
        mouse = tela.mouse_pos()
```

Posição do mouse.

### Linhas 485 a 491

```python
        for i, (rot, n, cor, destino) in enumerate(dados):
            b = pygame.Rect(r.x + (i % colunas) * (w + 14), r.y + (i // colunas) * (h + 14), w, h)
            painel(self.tela, b, 215 if b.collidepoint(mouse) else 185)
            pygame.draw.rect(self.tela, cor, (b.x, b.y, 6, b.h))
            self.escrever(str(n), b.x + 24, b.y + 14, 6, cor if n else CINZA, "titulo", sombra=None)
            self.escrever(font.cortar(rot, b.w - 40, 2), b.x + 24, b.bottom - 36, 2, BRANCO, sombra=None)
            self.alvos.append((b, lambda d=destino: self.ir(d)))
```

Cada bloco: painel (mais claro com o mouse em cima), faixa colorida, número grande e texto. Clicar vai para a aba correspondente.

### Linha 493

```python
    def linha_status(self, r):
```

Linha de status.

### Linhas 494 a 497

```python
        n = self.cfg["notificacoes"]
        canais = [("Discord", n["discord"] and bool(os.getenv("DISCORD_WEBHOOK_URL"))),
                  ("Celular", n["celular"] and bool(os.getenv("NTFY_TOPIC"))),
                  ("Alarme", n["ouvir_alarme"] and getattr(self.motor.alarme, "conectado", False))]
```

Estado de cada canal: Discord, celular e alarme (este último pelo ouvinte conectado).

### Linhas 498 a 501

```python
        x = r.x + 4
        for nome, ligado in canais:
            pygame.draw.rect(self.tela, VERDE if ligado else (90, 94, 110), (x, r.y + 8, 10, 10))
            x += 16 + self.escrever(nome, x + 16, r.y + 2, 1, BRANCO if ligado else CINZA) + 18
```

Desenha uma bolinha verde ou cinza e o nome de cada canal.

### Linhas 502 a 503

```python
        info = "demonstração" if self.demo else (f"atualizado às {self.atualizado:%H:%M}" if self.atualizado else "carregando…")
        self.escrever(self.status or info, r.x + 4, r.y + 30, 1, AMARELO if self.status else CINZA)
```

Hora da última atualização (ou o status).

### Linha 504

```python
        self.botao(pygame.Rect(r.right - 150, r.y, 150, 46), "Atualizar", AZUL, self.atualizar)
```

Botão Atualizar.

### Linha 506

```python
    # ---------- aba Resumo do dia ----------
```

Comentário: aba Resumo do dia.

### Linha 507

```python
    def pagina_resumo(self, agora):
```

Desenha a aba Resumo.

### Linhas 508 a 511

```python
        area = self.r_conteudo
        itens = self.resumo.itens if self.resumo else []
        urg = sum(1 for i in itens if i.prioridade >= URGENTE)
        y = self.cabecalho_painel(area, "RESUMO DO DIA")
```

Itens, urgentes e cabeçalho.

### Linhas 512 a 519

```python
        if self.resumo and itens:
            confirmando = pygame.time.get_ticks() - self.confirmar_limpar < 4000
            rot = "Confirmar?" if confirmando else "Limpar tudo"
            w = font.largura(rot, 1) + 24
            self.botao_pequeno(pygame.Rect(area.right - w - 14, area.y + 10, w, 28), rot,
                               VERMELHO if confirmando else CINZA, self.limpar_tudo)
            t = font.render(f"{len(itens)} itens" + (f" · {urg} urgentes" if urg else ""), 1, VERMELHO if urg else CINZA)
            self.tela.blit(t, (area.right - w - 28 - t.get_width(), area.y + 16))
```

Com itens: botão "Limpar tudo" (vira "Confirmar?" em vermelho depois do primeiro clique) e o total de itens.

### Linhas 520 a 522

```python
        if not self.resumo:
            self.escrever("carregando…", area.x + 16, y, 2, CINZA)
            return
```

Sem resumo ainda: "carregando...".

### Linhas 523 a 527

```python
        if not self.cfg["empresas"] and not self.demo:
            y = self.paragrafo("Nenhuma empresa configurada ainda. Adicione as suas e cole as chaves de API "
                               "nas Configurações.", area.x + 16, y + 6, area.w - 32)
            self.botao(pygame.Rect(area.x + 16, y + 14, 280, 44), "Abrir configurações", AMARELO, lambda: self.abrir_config(aba=4))
            return
```

Sem empresas: explica e oferece o botão para abrir as Configurações na aba Empresas.

### Linhas 528 a 532

```python
        erros = self.resumo.erros
        rodape = (44 + 22 * min(3, len(erros))) if erros else 0
        self.desenhar_lista(pygame.Rect(area.x, y, area.w, area.bottom - y - rodape - 6), agora)
        if erros:
            self.desenhar_erros(pygame.Rect(area.x, area.bottom - rodape, area.w, rodape), erros)
```

Desenha a lista e, se houver fontes com erro, um rodapé com os erros.

### Linha 534

```python
    def desenhar_lista(self, lista, agora):
```

Desenha a lista do resumo.

### Linha 535

```python
        """Itens agrupados por empresa, com ícone, horário e rolagem."""
```

Docstring.

### Linhas 536 a 540

```python
        x = lista.x + 16
        linhas = []
        for empresa, itens in self.resumo.por_empresa().items():
            linhas.append(("empresa", empresa, itens))
            linhas += [("item", empresa, it) for it in itens]
```

Monta uma lista plana com um título por empresa seguido dos itens dela.

### Linhas 541 a 544

```python
        if not linhas:
            self.paragrafo("Nada por aqui agora. Quando chegar algo das suas empresas, aparece nesta lista.",
                           x, lista.y + 8, lista.w - 32, 2, CINZA)
            return
```

Lista vazia: mensagem.

### Linhas 545 a 546

```python
        altura_total = sum(36 if t == "empresa" else 32 for t, _, _ in linhas)
        self.rolagem["resumo"] = max(0, min(self.rolagem["resumo"], altura_total - lista.h))
```

Altura total e limite da rolagem.

### Linhas 547 a 548

```python
        self.tela.set_clip(lista)
        y = lista.y - self.rolagem["resumo"]
```

Corta o desenho à área da lista e começa no topo menos a rolagem.

### Linha 549

```python
        mouse = tela.mouse_pos()
```

Mouse.

### Linhas 550 a 552

```python
        for tipo, empresa, dado in linhas:
            if y > lista.bottom:
                break
```

Para cada linha; para quando passar do fim da área (não desenha o que não aparece).

### Linha 553

```python
            cor = cor_rgb(self.cores.get(empresa, "#5ab0ff"))
```

Cor da empresa.

### Linhas 554 a 559

```python
            if tipo == "empresa":
                if y + 36 >= lista.y:
                    pygame.draw.rect(self.tela, cor, (x - 6, y + 2, lista.w - 26, 28))
                    self.escrever(f"{empresa} · {len(dado)}", x + 2, y + 5, 2, (12, 14, 24), sombra=None)
                y += 36
                continue
```

Título da empresa: faixa colorida com o nome e a quantidade.

### Linhas 560 a 563

```python
            it = dado
            if y + 32 < lista.y:
                y += 32
                continue
```

Item fora da área visível (acima): só soma a altura.

### Linhas 564 a 566

```python
            linha = pygame.Rect(x - 6, y, lista.w - 26, 30)
            q = self.quando_curto(it, agora)
            largura_txt = linha.w - 48 - (font.largura(q, 1) + 14 if q else 0)
```

Retângulo da linha, horário curto e largura disponível para o título.

### Linhas 567 a 577

```python
            if linha.collidepoint(mouse) and lista.collidepoint(mouse):
                pygame.draw.rect(self.tela, (40, 48, 72), linha)
                if it.url:
                    self.alvos.append((linha.clip(lista), lambda u=it.url: webbrowser.open(u)))
                if font.cortar(it.titulo, largura_txt, 2) != it.titulo or it.detalhe:
                    self.dica = (it.titulo + (f"  ·  {it.detalhe}" if it.detalhe else ""), mouse)
                fechar = pygame.Rect(linha.right - 26, y + 4, 22, 22).clip(lista)
                q = ""
                pygame.draw.rect(self.tela, (70, 40, 50), fechar)
                self.escrever("×", fechar.x + 6, fechar.y + 1, 2, VERMELHO, sombra=None)
                self.alvos.append((fechar, lambda i=it: self.dispensar(i)))
```

Com o mouse em cima: destaca, torna clicável para abrir o link, mostra a dica com o título inteiro se ele foi cortado, e desenha o "×" que tira o item do resumo.

### Linhas 578 a 580

```python
            pygame.draw.rect(self.tela, COR_PRIO.get(it.prioridade, (70, 74, 92)), (x - 6, y + 3, 4, 24))
            self.tela.blit(icons.item(it.tipo, 22), (x + 2, y + 4))
            self.escrever(font.cortar(it.titulo, largura_txt, 2), x + 30, y + 4, 2, BRANCO, sombra=None)
```

Faixa de prioridade, ícone do tipo e título.

### Linhas 581 a 583

```python
            if q:
                t = font.render(q, 1, VERMELHO if q == "atrasado" else CINZA)
                self.tela.blit(t, (linha.right - t.get_width() - 6, y + 8))
```

Horário à direita (vermelho se atrasado).

### Linha 584

```python
            y += 32
```

Próxima linha.

### Linhas 585 a 586

```python
        self.tela.set_clip(None)
        self.barra_rolagem(lista, altura_total, self.rolagem["resumo"])
```

Libera o corte e desenha a barra de rolagem.

### Linhas 588 a 592

```python
    def barra_rolagem(self, area, altura_total, rolagem):
        if altura_total > area.h:
            prop = area.h / altura_total
            pygame.draw.rect(self.tela, (90, 100, 130),
                             (area.right - 8, area.y + int(rolagem * prop), 4, max(20, int(area.h * prop))))
```

Barra de rolagem proporcional (mínimo de 20 pixels).

### Linhas 594 a 604

```python
    @staticmethod
    def quando_curto(it, agora):
        """Horário curto do item: 14:30, amanhã, 12/11 ou atrasado."""
        if not it.quando:
            return ""
        dias = (it.quando.date() - agora.date()).days
        if dias == 0:
            return it.quando.strftime("%H:%M")
        if dias < 0:
            return "atrasado" if it.tipo == "tarefa" else it.quando.strftime("%d/%m")
        return "amanhã" if dias == 1 else it.quando.strftime("%d/%m")
```

Horário curto de um item: a hora (hoje), "atrasado" (tarefa de dia anterior), "amanhã" ou a data.

### Linha 606

```python
    def desenhar_erros(self, rect, erros):
```

Rodapé dos erros.

### Linhas 607 a 609

```python
        pygame.draw.line(self.tela, (80, 60, 50), (rect.x + 12, rect.y), (rect.right - 12, rect.y), 1)
        x = rect.x + 16
        self.escrever(f"{len(erros)} fonte(s) com problema", x, rect.y + 10, 1, AMARELO, sombra=None)
```

Linha e título.

### Linhas 610 a 612

```python
        for i, e in enumerate(erros[:3]):
            origem, motivo = erro_amigavel(e)
            self.escrever(font.cortar(f"{origem}: {motivo}", rect.w - 32, 1), x, rect.y + 38 + i * 22, 1, (255, 200, 150), sombra=None)
```

Até 3 erros em texto amigável.

### Linha 613

```python
        self.botao(pygame.Rect(rect.right - 130, rect.y + 6, 114, 34), "Resolver", AMARELO, lambda: self.abrir_config(aba=5))
```

Botão Resolver, que abre as Configurações na aba Chaves de API.

### Linha 615

```python
    # ---------- aba E-mails ----------
```

Comentário: aba E-mails.

### Linha 616

```python
    def pagina_emails(self, agora):
```

Desenha a aba E-mails.

### Linhas 617 a 619

```python
        area = self.r_conteudo
        y = self.cabecalho_painel(area, "RESUMO DOS E-MAILS")
        x = area.x + 16
```

Cabeçalho.

### Linhas 620 a 624

```python
        if not self.resumos_email:
            y = self.paragrafo("Os e-mails aparecem aqui depois que você conecta uma conta Gmail "
                               "(Configurações > Chaves de API > Fazer login).", x, y + 6, area.w - 32, 2, CINZA)
            self.botao(pygame.Rect(x, y + 14, 280, 44), "Abrir configurações", AMARELO, lambda: self.abrir_config(aba=5))
            return
```

Sem resumos: explica como conectar o Gmail e oferece o botão.

### Linhas 625 a 634

```python
        # uma "aba" por conta de e-mail (quebra linha se não couber)
        bx, by = x, y
        for conta in self.resumos_email:
            rot = font.cortar(conta, area.w - 60, 1)
            w = font.largura(rot, 1) + 26
            if bx + w > area.right - 16:
                bx, by = x, by + 36
            self.botao_pequeno(pygame.Rect(bx, by, w, 30), rot, AZUL if conta == self.conta_email else CINZA,
                               lambda c=conta: (setattr(self, "conta_email", c), self.rolagem.__setitem__("emails", 0)))
            bx += w + 8
```

Uma "aba" por conta de e-mail, quebrando a linha se não couber. Clicar escolhe a conta e zera a rolagem (a `lambda` faz as duas coisas numa tupla).

### Linha 635

```python
        y = by + 44
```

Posição abaixo das contas.

### Linha 636

```python
        r = self.resumos_email.get(self.conta_email) or next(iter(self.resumos_email.values()))
```

Resumo da conta escolhida.

### Linhas 637 a 638

```python
        fonte = "resumo com IA" if r.get("fonte") == "ia" else "resumo simples (sem IA)"
        y = self.paragrafo(f"{r.get('resumo', '')}  ·  {fonte} às {r.get('gerado', '--:--')}", x, y, area.w - 32, 1, (200, 206, 222), 3) + 10
```

Frase geral, se veio da IA ou é simples, e a hora.

### Linhas 639 a 640

```python
        lista = pygame.Rect(area.x, y, area.w, area.bottom - y - 8)
        cores = {"alta": VERMELHO, "media": AMARELO, "baixa": CINZA}
```

Área da lista e cores das prioridades.

### Linhas 641 a 643

```python
        self.tela.set_clip(lista)
        yy = lista.y - self.rolagem["emails"]
        inicio = yy
```

Corta à área e aplica a rolagem.

### Linhas 644 a 652

```python
        for p in r.get("pontos", []):
            pygame.draw.rect(self.tela, cores.get(p.get("prioridade"), CINZA), (x, yy + 6, 10, 10))
            self.escrever(font.cortar(p.get("titulo", ""), area.w - 64, 2), x + 22, yy, 2, BRANCO, sombra=None)
            yy = self.paragrafo(p.get("detalhe", ""), x + 22, yy + 28, area.w - 64, 1, (205, 210, 226), 2)
            if p.get("acao"):
                self.escrever(font.cortar("→ " + p["acao"], area.w - 64, 1), x + 22, yy + 2, 1, AMARELO, sombra=None)
                yy += 22
            yy += 14
            pygame.draw.line(self.tela, (50, 56, 78), (x, yy - 7), (area.right - 16, yy - 7), 1)
```

Cada ponto: quadrado da cor da prioridade, título, detalhe em até 2 linhas, a ação em amarelo com seta (se houver) e uma linha separadora.

### Linhas 653 a 656

```python
        self.tela.set_clip(None)
        total = yy - inicio
        self.rolagem["emails"] = max(0, min(self.rolagem["emails"], max(0, total - lista.h)))
        self.barra_rolagem(lista, total, self.rolagem["emails"])
```

Libera o corte, limita a rolagem e desenha a barra.

### Linha 658

```python
    # ---------- aba Agenda ----------
```

Comentário: aba Agenda.

### Linha 659

```python
    def pagina_agenda(self, agora):
```

Desenha a aba Agenda.

### Linhas 660 a 664

```python
        area = self.r_conteudo
        y = self.cabecalho_painel(area, "AGENDA", "hoje e amanhã")
        x = area.x + 16
        tem_agendador = bool(self.motor.agendador)
        barra_h = 96 if tem_agendador else 0
```

Cabeçalho e espaço para a barra do agendador.

### Linhas 665 a 666

```python
        eventos = sorted([i for i in (self.resumo.itens if self.resumo else []) if i.tipo == "evento" and i.quando],
                         key=lambda i: i.quando)
```

Eventos ordenados por horário.

### Linhas 667 a 671

```python
        lista = pygame.Rect(area.x, y, area.w, area.bottom - y - barra_h - 8)
        self.tela.set_clip(lista)
        yy = lista.y - self.rolagem["agenda"]
        inicio = yy
        mouse = tela.mouse_pos()
```

Área da lista, corte, rolagem e mouse.

### Linhas 672 a 674

```python
        if not eventos:
            yy = self.paragrafo("Nenhum compromisso hoje nem amanhã. Conecte o Google Agenda ou o Zoom nas Configurações.",
                                x, yy + 6, area.w - 32, 2, CINZA)
```

Sem eventos: mensagem.

### Linhas 675 a 682

```python
        dia_atual = None
        for ev in eventos:
            dias = (ev.quando.date() - agora.date()).days
            if dias != dia_atual:
                dia_atual = dias
                rot = "HOJE" if dias == 0 else ("AMANHÃ" if dias == 1 else ev.quando.strftime("%d/%m"))
                self.escrever(rot, x, yy + 6, 2, AZUL, "titulo", sombra=None)
                yy += 36
```

Ao mudar de dia, escreve "HOJE", "AMANHÃ" ou a data.

### Linhas 683 a 688

```python
            linha = pygame.Rect(x - 6, yy, area.w - 26, 52)
            passou = ev.quando < agora
            if linha.collidepoint(mouse) and lista.collidepoint(mouse):
                pygame.draw.rect(self.tela, (40, 48, 72), linha)
                if ev.url:
                    self.alvos.append((linha.clip(lista), lambda u=ev.url: webbrowser.open(u)))
```

Linha do evento; com o mouse em cima, destaca e torna clicável.

### Linhas 689 a 690

```python
            self.escrever(ev.quando.strftime("%H:%M"), x + 4, yy + 12, 3, CINZA if passou else BRANCO, "titulo", sombra=None)
            self.tela.blit(icons.item("evento", 26), (x + 104, yy + 12))
```

Hora (cinza se já passou) e ícone.

### Linha 691

```python
            fonte = NOMES_SERVICO.get(ev.fonte, ev.fonte) + (f" · {ev.detalhe}" if ev.detalhe and ev.detalhe not in ("Zoom",) else "")
```

Fonte e detalhe (sem repetir "Zoom").

### Linhas 692 a 694

```python
            falta = int((ev.quando - agora).total_seconds() // 60)
            marca = f"em {falta} min" if 0 <= falta < 120 else ""
            larg = linha.w - 160 - (font.largura(marca, 2) + 16 if marca else 0)
```

Minutos que faltam e a marca "em X min" para as próximas 2 horas.

### Linhas 695 a 696

```python
            self.escrever(font.cortar(ev.titulo, larg, 2), x + 142, yy + 6, 2, CINZA if passou else BRANCO, sombra=None)
            self.escrever(font.cortar(f"{ev.empresa} · {fonte}", larg, 1), x + 142, yy + 30, 1, CINZA, sombra=None)
```

Título e empresa com a fonte.

### Linhas 697 a 699

```python
            if marca:
                t = font.render(marca, 2, VERMELHO if falta <= 15 else AMARELO)
                self.tela.blit(t, (linha.right - t.get_width() - 8, yy + 14))
```

Marca em vermelho (até 15 min) ou amarelo.

### Linha 700

```python
            yy += 58
```

Próxima linha.

### Linhas 701 a 704

```python
        self.tela.set_clip(None)
        total = yy - inicio
        self.rolagem["agenda"] = max(0, min(self.rolagem["agenda"], max(0, total - lista.h)))
        self.barra_rolagem(lista, total, self.rolagem["agenda"])
```

Libera o corte, limita a rolagem e desenha a barra.

### Linhas 705 a 706

```python
        if tem_agendador:
            self.desenhar_barra(pygame.Rect(area.x + 12, area.bottom - 60, area.w - 24, 50))
```

Barra do agendador, se houver.

### Linhas 707 a 708

```python
        if self.proposta:
            self.desenhar_proposta()
```

Proposta de reunião por cima, se houver.

### Linha 710

```python
    def desenhar_proposta(self):
```

Desenha a proposta de reunião.

### Linhas 711 a 716

```python
        p = self.proposta
        c = self.r_conteudo
        largura = min(c.w - 40, 760)
        area = pygame.Rect(c.centerx - largura // 2, c.y + 70, largura, 330 if self.orientacao == "vertical" else 250)
        painel(self.tela, area, 235, (122, 214, 122))
        x, y = area.x + 20, area.y + 16
```

Painel centralizado, mais alto na vertical.

### Linhas 717 a 720

```python
        if p.get("origem") == "teams":
            self.tela.blit(icons.item("mensagem", 30), (x, y))
            self.escrever(font.cortar(f"{p['pessoa']} pediu uma reunião", area.w - 80, 3), x + 40, y, 3, (122, 214, 122), sombra=None)
            y = self.paragrafo(f"“{p.get('texto', '')}”", x, y + 40, area.w - 40, 1, max_linhas=2)
```

Pedido do Teams: ícone de mensagem, quem pediu e o texto da mensagem.

### Linhas 721 a 726

```python
        else:
            self.tela.blit(icons.item("evento", 30), (x, y))
            self.escrever(font.cortar(p["assunto"], area.w - 80, 3), x + 40, y, 3, (122, 214, 122), sombra=None)
            self.escrever(font.cortar(f"com {p['pessoa']} ({p['email']}) · {p.get('duracao', 30)} min", area.w - 40, 1),
                          x, y + 40, 1, (220, 224, 236), sombra=None)
            y += 62
```

Comando digitado: assunto, pessoa, e-mail e duração.

### Linhas 727 a 728

```python
        self.escrever("Horários livres para vocês dois:", x, y + 8, 2, (200, 206, 222), sombra=None)
        y += 40
```

Título dos horários.

### Linhas 729 a 730

```python
        colunas = 1 if self.orientacao == "vertical" else 3
        w = (area.w - 40 - (colunas - 1) * 12) // colunas
```

Uma coluna na vertical e três na horizontal.

### Linhas 731 a 739

```python
        for i, h in enumerate(p["horarios"][:3]):
            r = pygame.Rect(x + (i % colunas) * (w + 12), y + (i // colunas) * 58, w, 52)
            sobre = r.collidepoint(tela.mouse_pos())
            pygame.draw.rect(self.tela, (70, 150, 80) if sobre else (30, 64, 40), r)
            pygame.draw.rect(self.tela, (122, 214, 122), r, 2)
            self.escrever(f"{i + 1}", r.x + 12, r.y + 12, 3, AMARELO, "titulo", sombra=None)
            self.escrever(rotulo(h), r.x + 44, r.y + 6, 2, BRANCO, sombra=None)
            self.escrever(f"até {h.fim:%H:%M}", r.x + 44, r.y + 30, 1, CINZA, sombra=None)
            self.alvos.append((r, lambda h=h: self.confirmar(h)))
```

Cada horário vira um botão com o número (1 a 3), o dia e a hora e o fim. Clicar confirma.

### Linha 740

```python
        self.escrever("1, 2 ou 3 (ou clique) para agendar · Esc ignora", x, area.bottom - 26, 1, CINZA, sombra=None)
```

Instrução.

### Linha 742

```python
    def desenhar_barra(self, r):
```

Barra de comando do agendador.

### Linha 743

```python
        """Campo 'reunião com …' + prévia do que o programa entendeu."""
```

Docstring.

### Linhas 744 a 745

```python
        painel(self.tela, r, 215, AZUL)
        self.escrever(">", r.x + 12, r.y + 10, 3, AZUL, "titulo", sombra=None)
```

Painel e o sinal ">".

### Linhas 746 a 750

```python
        if self.texto:
            t = font.cauda(self.texto, r.w - 70, 2)
            w = self.escrever(t, r.x + 42, r.y + 14, 2, BRANCO, sombra=None)
            if pygame.time.get_ticks() // 450 % 2:
                pygame.draw.rect(self.tela, AZUL, (r.x + 46 + w, r.y + 12, 3, r.h - 24))
```

Com texto: mostra o fim do que foi digitado e o cursor piscando.

### Linhas 751 a 752

```python
        else:
            self.escrever(EXEMPLO, r.x + 42, r.y + 14, 2, (100, 110, 140), sombra=None)
```

Sem texto: mostra o exemplo em cinza.

### Linha 753

```python
        acima = r.y - 26
```

Posição da prévia, acima da barra.

### Linhas 754 a 761

```python
        if self.texto:
            p = interpretar(self.texto, self.agora().date(), self.cfg["reunioes"]["duracao_padrao"])
            if p:
                partes = [p["pessoa"], f"{p['dia']:%d/%m}" if p["dia"] else "próximos dias", f"{p['duracao']} min"]
                if p["hora"]:
                    partes.insert(2, f"{p['hora']:%H:%M}")
                texto = "  ·  ".join(partes) + "  (Enter busca horários)"
                self.escrever(font.cortar(texto, r.w, 1), r.x + 4, acima, 1, VERDE, sombra=None)
```

Prévia ao vivo do que o programa entendeu (pessoa, dia, hora, duração), usando a mesma função `interpretar` do Motor. Ajuda a pessoa a ver se escreveu certo antes de apertar Enter.

### Linhas 762 a 764

```python
            else:
                self.escrever(font.cortar("Comece com: reunião com <pessoa> [amanhã | sexta] [às 14h] [45min]", r.w, 1),
                              r.x + 4, acima, 1, CINZA, sombra=None)
```

Se ainda não entendeu, mostra o formato esperado.

### Linha 766

```python
    # ---------- barra de navegação ----------
```

Comentário: barra de navegação.

### Linha 767

```python
    def desenhar_nav(self):
```

Desenha a barra.

### Linhas 768 a 770

```python
        r = self.r_nav
        painel(self.tela, r, 235)
        pygame.draw.line(self.tela, (60, 70, 100), (0, r.y), (r.right, r.y), 2)
```

Painel e linha.

### Linhas 771 a 772

```python
        w = r.w / len(ABAS)
        vertical = self.orientacao == "vertical"
```

Largura de cada aba e orientação.

### Linhas 773 a 775

```python
        itens = self.resumo.itens if self.resumo else []
        selos = {"resumo": sum(1 for i in itens if i.prioridade >= URGENTE),
                 "emails": sum(1 for x in self.resumos_email.values() for p in x.get("pontos", []) if p.get("prioridade") == "alta")}
```

Selos: quantos urgentes no Resumo e quantos pontos importantes nos E-mails.

### Linha 776

```python
        mouse = tela.mouse_pos()
```

Mouse.

### Linhas 777 a 779

```python
        for i, (chave, rot, icone) in enumerate(ABAS):
            b = pygame.Rect(int(r.x + i * w), r.y + 2, int(w), r.h - 2)
            ativa = chave == self.pagina
```

Para cada aba, retângulo e se está ativa.

### Linhas 780 a 783

```python
            if ativa or b.collidepoint(mouse):
                pygame.draw.rect(self.tela, (34, 42, 66) if ativa else (26, 30, 48), b)
            if ativa:
                pygame.draw.rect(self.tela, AZUL, (b.x + 10, b.y, b.w - 20, 4))
```

Fundo destacado e uma faixa azul em cima da aba ativa.

### Linhas 784 a 785

```python
            tam = 64 if vertical else 48
            self.tela.blit(icons.item(icone, tam), (b.centerx - tam // 2, b.y + (4 if vertical else 0)))
```

Ícone (maior na vertical).

### Linhas 786 a 787

```python
            cor = BRANCO if ativa else CINZA
            self.centralizado(rot, b.centerx, b.bottom - (36 if vertical else 26), 2 if vertical else 1, cor, sombra=None)
```

Texto embaixo.

### Linhas 788 a 792

```python
            n = selos.get(chave, 0)
            if n:
                sx, sy = b.centerx + tam // 3, b.y + 4
                pygame.draw.circle(self.tela, VERMELHO, (sx, sy + 8), 11)
                self.centralizado(str(min(n, 99)), sx, sy, 1, BRANCO, sombra=None)
```

Selo vermelho com o número (até 99).

### Linha 793

```python
            self.alvos.append((b, lambda c=chave: self.ir(c)))
```

Clicar vai para a aba.

### Linha 795

```python
    def desenhar_dica(self):
```

Dica com o título inteiro.

### Linha 796

```python
        """Caixinha com o título inteiro do item embaixo do mouse."""
```

Docstring.

### Linhas 797 a 798

```python
        if not self.dica:
            return
```

Sem dica, não faz nada.

### Linhas 799 a 803

```python
        texto, (mx, my) = self.dica
        lw = self.tela.get_width()
        linhas = font.wrap(texto, min(420, lw - 60), 1)[:4]
        w = max(font.largura(linha, 1) for linha in linhas) + 20
        h = len(linhas) * font.altura(1) + 14
```

Quebra em até 4 linhas e calcula o tamanho da caixa.

### Linhas 804 a 805

```python
        x = max(10, min(mx - w - 12, lw - w - 10))
        y = my + 14
```

Posição perto do mouse, sem sair da tela.

### Linhas 806 a 808

```python
        painel(self.tela, pygame.Rect(x, y, w, h), 240, (120, 130, 160))
        for i, linha in enumerate(linhas):
            self.escrever(linha, x + 10, y + 7 + i * font.altura(1), 1, BRANCO, sombra=None)
```

Desenha a caixa e as linhas.

### Linha 810

```python
    # ---------- quadro ----------
```

Comentário: quadro.

### Linha 811

```python
    def quadro(self, dt):
```

Desenha um quadro completo.

### Linhas 812 a 813

```python
        agora = self.agora()
        self.alvos, self.dica = [], None
```

Hora e limpa os alvos e a dica.

### Linhas 814 a 815

```python
        self.cena.update(dt, agora)
        baixa = self.cena.draw(agora)
```

Atualiza e desenha o cenário pequeno.

### Linhas 816 a 817

```python
        for e in self.efeitos:
            e.draw_baixa(baixa)
```

Animações que desenham no cenário pequeno.

### Linha 818

```python
        pygame.transform.scale(baixa, self.tela.get_size(), self.tela)
```

Amplia o cenário para a tela lógica.

### Linhas 819 a 822

```python
        if self.config_tela:
            self.config_tela.desenhar(baixa)       # Configurações têm a própria tela
            if not self.config_tela.aberta:        # clicou em Salvar ou Cancelar
                self.config_tela = None
```

Com as Configurações abertas, elas desenham na própria superfície; se foram fechadas, some.

### Linhas 823 a 829

```python
        else:
            if self.pagina != "inicio":
                self.desenhar_topo(agora)
            {"inicio": self.pagina_inicio, "resumo": self.pagina_resumo,
             "emails": self.pagina_emails, "agenda": self.pagina_agenda}[self.pagina](agora)
            self.desenhar_nav()
            self.desenhar_dica()
```

Senão: topo (menos na aba Início, que tem o relógio grande), a aba atual (escolhida num dicionário de funções), a barra de navegação e a dica.

### Linhas 830 a 831

```python
        for e in self.efeitos + self.toasts:
            e.update(dt)
```

Atualiza animações e avisos.

### Linha 832

```python
        alvo = self.config_tela.superficie if self.config_tela else self.tela
```

Onde desenhar as animações: na tela das Configurações, se aberta, ou na tela principal.

### Linhas 833 a 836

```python
        for e in self.efeitos:
            e.draw(alvo)
        for i, t in enumerate(self.toasts[-3:]):
            t.draw(alvo, i)
```

Desenha as animações e os 3 avisos mais recentes.

### Linhas 837 a 838

```python
        self.efeitos = [e for e in self.efeitos if e.vivo]
        self.toasts = [t for t in self.toasts if t.vivo]
```

Remove as animações e os avisos que terminaram.

### Linha 839

```python
        tela.VIEW.apresentar(alvo, self.janela)
```

Ajusta a tela lógica à janela real.

### Linha 841

```python
    def rodar(self):
```

Laço principal.

### Linha 842

```python
        pygame.key.start_text_input()
```

Liga a entrada de texto (letras com acento chegam como `TEXTINPUT`).

### Linha 843

```python
        while self.rodando:
```

Enquanto estiver rodando.

### Linha 844

```python
            dt = self.relogio.tick(30) / 1000
```

Espera o tempo necessário para dar 30 quadros por segundo e devolve o tempo do quadro em segundos.

### Linhas 845 a 849

```python
            for ev in pygame.event.get():
                if ev.type in (pygame.VIDEORESIZE, pygame.WINDOWSIZECHANGED):
                    self.redimensionou()
                    continue
                self.tratar(tela.converter(ev))
```

Trata os eventos: redimensionar recalcula o layout; os outros são convertidos para a tela lógica e tratados.

### Linhas 850 a 852

```python
            self.receber()
            self.quadro(dt)
            pygame.display.flip()
```

Lê os eventos do Motor, desenha o quadro e mostra na janela (`flip`).

### Linha 853

```python
        self.motor.encerrar()
```

Ao sair, para o Motor.
