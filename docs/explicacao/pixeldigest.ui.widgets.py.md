# `pixeldigest/ui/widgets.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/ui/widgets.py)

Componentes da interface (botões, campos de texto, interruptores, QR code) no estilo "immediate mode": em vez de criar um objeto para cada botão, a tela chama uma função a cada quadro, e a função desenha e já responde se foi clicada.

### Linhas 1 a 12

```python
"""Componentes da tela de Configurações (no estilo "immediate mode").

Em vez de criar objetos para cada botão, a tela chama funções a cada quadro:

    nome = form.campo("nome", x, y, 400, nome)
    if form.botao("salvar", x, y, 200, "Salvar"):
        salvar()

Cada função desenha o componente e já devolve o novo valor (ou True se clicado).
O Form guarda só o que precisa durar entre quadros: qual campo está com o foco,
o texto digitado, o clique do mouse e a rolagem.
"""
```

Docstring com um exemplo do estilo. O `Form` guarda só o que precisa durar entre quadros: qual campo tem o foco, o texto digitado, o clique e a rolagem.

### Linha 13

```python
import pygame
```

Importa o pygame.

### Linha 15

```python
from . import font
```

Importa o módulo de fontes.

### Linha 16

```python
from .tela import mouse_pos
```

Importa a posição do mouse já convertida para a tela lógica.

### Linhas 18 a 24

```python
AZUL = (90, 170, 255)
VERDE = (90, 200, 110)
VERMELHO = (255, 95, 95)
AMARELO = (255, 205, 80)
CINZA = (150, 156, 178)
BRANCO = (240, 242, 248)
FUNDO_CAMPO = (18, 22, 38)
```

Cores usadas nos componentes.

### Linha 25

```python
PALETA = ["#3fa7ff", "#7ad67a", "#ff9f43", "#ff6b81", "#a78bfa", "#2dd4bf", "#facc15", "#f472b6"]
```

Paleta de cores para escolher a cor de cada empresa.

### Linha 28

```python
def area_de_transferencia():
```

Lê o texto copiado (área de transferência).

### Linha 29

```python
    """Texto copiado (Ctrl+C) no Windows/macOS/Linux."""
```

Docstring.

### Linhas 30 a 31

```python
    try:
        return pygame.scrap.get_text() or ""
```

Tenta pelo módulo `scrap` do pygame.

### Linhas 32 a 39

```python
    except Exception:
        try:
            import tkinter
            r = tkinter.Tk()
            r.withdraw()
            texto = r.clipboard_get()
            r.destroy()
            return texto
```

Se falhar, usa o `tkinter` (vem com o Python): cria uma janela escondida, lê a área de transferência e fecha a janela.

### Linhas 40 a 41

```python
        except Exception:
            return ""
```

Se nada funcionar, devolve vazio.

### Linhas 44 a 48

```python
def copiar(texto):
    try:
        pygame.scrap.put_text(texto)
    except Exception:
        pass
```

Copia um texto para a área de transferência; se não der, ignora.

### Linha 51

```python
class Form:
```

Classe do formulário.

### Linhas 52 a 53

```python
    def __init__(self, tela):
        self.tela = tela
```

Guarda a superfície onde desenhar.

### Linha 54

```python
        self.foco = None            # id do campo que está recebendo o teclado
```

Campo que está recebendo o teclado.

### Linha 55

```python
        self.clique = None          # posição do clique deste quadro
```

Posição do clique deste quadro.

### Linhas 56 a 59

```python
        self.digitado = ""
        self.apagar = 0
        self.colar = None
        self.tab = False
```

Entradas de teclado acumuladas no quadro: texto digitado, quantas vezes apertou Backspace, texto colado e se apertou Tab.

### Linha 60

```python
        self.campos = []            # ordem dos campos (para o Tab pular para o próximo)
```

Ordem dos campos desenhados (para o Tab ir ao próximo).

### Linha 61

```python
        self.mostrar = set()        # campos secretos que o usuário pediu para ver
```

Campos secretos que o usuário pediu para ver.

### Linha 62

```python
        self.rolagem = 0
```

Rolagem atual.

### Linha 63

```python
        self.area = pygame.Rect(0, 0, *tela.get_size())
```

Área atual de desenho. O `*` desempacota a tupla do tamanho.

### Linhas 64 a 66

```python
        self.altura = 0             # altura total do conteúdo (para limitar a rolagem)
        self.desloc = 0             # quanto a parte atual está rolada
        self.altura_visivel = 0     # altura da área que rola
```

Altura total do conteúdo, deslocamento da parte atual e altura visível (para limitar a rolagem).

### Linha 67

```python
        self._clicou_campo = False
```

Indica se o clique deste quadro caiu num campo.

### Linha 69

```python
    # ---------- eventos ----------
```

Comentário: eventos.

### Linha 70

```python
    def evento(self, ev):
```

Recebe um evento do pygame.

### Linhas 71 a 72

```python
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.clique = ev.pos
```

Clique com o botão esquerdo (1): guarda a posição.

### Linhas 73 a 74

```python
        elif ev.type == pygame.MOUSEWHEEL:
            self.rolagem = max(0, min(self.rolagem - ev.y * 40, max(0, self.altura - self.altura_visivel)))
```

Rodinha do mouse: muda a rolagem em 40 pixels por passo, limitada entre 0 e o máximo (altura do conteúdo menos a visível).

### Linhas 75 a 76

```python
        elif ev.type == pygame.TEXTINPUT and self.foco:
            self.digitado += ev.text
```

Texto digitado com algum campo em foco: acumula. O evento `TEXTINPUT` já entrega letras com acento.

### Linhas 77 a 85

```python
        elif ev.type == pygame.KEYDOWN and self.foco:
            if ev.key == pygame.K_BACKSPACE:
                self.apagar += 1
            elif ev.key == pygame.K_v and ev.mod & pygame.KMOD_CTRL:
                self.colar = area_de_transferencia()
            elif ev.key == pygame.K_TAB:
                self.tab = True
            elif ev.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                self.foco = None
```

Teclas especiais com foco: Backspace conta uma letra a apagar; Ctrl+V cola (`ev.mod & KMOD_CTRL` confere se o Ctrl está apertado); Tab marca para ir ao próximo campo; Enter ou Esc tiram o foco.

### Linha 87

```python
    def comecar(self, area, rolar=False):
```

Começa uma parte da tela.

### Linhas 88 a 91

```python
        """Começa uma parte da tela; tudo fora de 'area' fica cortado.

        rolar=True: a parte acompanha a rodinha do mouse (o conteúdo das abas).
        """
```

Docstring: o que estiver fora da área fica cortado; com `rolar=True`, a parte acompanha a rolagem.

### Linhas 92 a 94

```python
        self.area = area
        self.desloc = self.rolagem if rolar else 0
        self.tela.set_clip(area)
```

Guarda a área, o deslocamento e limita o desenho à área com `set_clip`.

### Linha 96

```python
    def terminar(self, altura_conteudo=None):
```

Termina uma parte.

### Linha 97

```python
        """Fim de uma parte da tela (abas, conteúdo com rolagem, rodapé)."""
```

Docstring.

### Linha 98

```python
        self.tela.set_clip(None)
```

Libera o corte.

### Linhas 99 a 102

```python
        if altura_conteudo is not None:
            self.altura = altura_conteudo
            self.altura_visivel = self.area.h
            self.rolagem = max(0, min(self.rolagem, max(0, self.altura - self.altura_visivel)))
```

Se foi informada a altura do conteúdo, guarda e corrige a rolagem para não passar do limite.

### Linha 104

```python
    def fim_do_quadro(self):
```

Fim do quadro inteiro.

### Linha 105

```python
        """Fim do quadro inteiro: aplica Tab, tira o foco se clicou fora e limpa o teclado/mouse."""
```

Docstring.

### Linhas 106 a 108

```python
        if self.tab and self.foco in self.campos:
            i = self.campos.index(self.foco)
            self.foco = self.campos[(i + 1) % len(self.campos)]
```

Se apertou Tab, passa o foco para o próximo campo (o `%` volta ao primeiro depois do último).

### Linhas 109 a 110

```python
        elif self.clique and self.foco and not getattr(self, "_clicou_campo", False):
            self.foco = None                  # clicou fora: tira o foco
```

Se clicou fora de qualquer campo, tira o foco.

### Linhas 111 a 114

```python
        self.clique, self.digitado, self.apagar, self.colar, self.tab = None, "", 0, None, False
        self._clicou_campo = False
        self.campos = []
        self.desloc = 0
```

Limpa tudo o que vale só para um quadro.

### Linha 116

```python
    # ---------- utilidades ----------
```

Comentário: utilidades.

### Linhas 117 a 119

```python
    def r(self, x, y, w, h):
        """Retângulo na tela, já descontando a rolagem."""
        return pygame.Rect(x, y - self.desloc, w, h)
```

Cria um retângulo já descontando a rolagem.

### Linha 121

```python
    def clicou(self, rect):
```

Diz se um retângulo foi clicado.

### Linhas 122 a 124

```python
        if self.clique and rect.collidepoint(self.clique) and self.area.collidepoint(self.clique):
            self.clique = None                # um clique vale para um componente só
            return True
```

Precisa ter clique, o clique estar dentro do retângulo e dentro da área visível. Depois apaga o clique, para que ele valha para um componente só.

### Linha 125

```python
        return False
```

Não foi clicado.

### Linhas 127 a 129

```python
    def sobre(self, rect):
        m = mouse_pos()
        return rect.collidepoint(m) and self.area.collidepoint(m)
```

Diz se o mouse está sobre o retângulo (para o efeito de destaque).

### Linhas 131 a 132

```python
    def texto(self, x, y, texto, cor=BRANCO, escala=2, familia="texto"):
        self.tela.blit(font.render(texto, escala, cor, familia=familia), (x, y - self.desloc))
```

Escreve um texto descontando a rolagem.

### Linhas 134 a 137

```python
    def texto_no_meio(self, rect, texto, cor=BRANCO, escala=2):
        """Texto centralizado dentro de um retângulo (já na tela)."""
        t = font.render(texto, escala, cor)
        self.tela.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))
```

Escreve um texto centralizado num retângulo.

### Linhas 139 a 144

```python
    def paragrafo(self, x, y, texto, largura, cor=CINZA, escala=2):
        """Texto quebrado em linhas que cabem na largura. Devolve o y logo abaixo."""
        for linha in font.wrap(texto, largura, escala):
            self.texto(x, y, linha, cor, escala)
            y += font.altura(escala)
        return y
```

Escreve um parágrafo quebrado em linhas e devolve o y logo abaixo, para o próximo componente começar ali.

### Linhas 146 a 150

```python
    def secao(self, x, y, titulo, largura):
        """Título de seção (fonte de fliperama) com uma linha embaixo."""
        self.texto(x, y, titulo.upper(), AZUL, 3, "titulo")
        pygame.draw.line(self.tela, (50, 60, 90), (x, y + 30 - self.desloc), (x + largura, y + 30 - self.desloc), 2)
        return y + 42
```

Título de seção em maiúsculas, com a fonte de fliperama, e uma linha embaixo.

### Linha 152

```python
    # ---------- componentes ----------
```

Comentário: componentes.

### Linha 153

```python
    def botao(self, id_, x, y, w, rotulo, cor=AZUL, h=34, ativo=True):
```

Botão.

### Linha 154

```python
        w = max(w, font.largura(rotulo) + 28)      # nunca corta o texto
```

A largura nunca é menor que o texto mais uma margem.

### Linha 155

```python
        rect = self.r(x, y, w, h)
```

Retângulo.

### Linha 156

```python
        cheio = self.sobre(rect) and ativo
```

Fica "aceso" com o mouse em cima.

### Linha 157

```python
        pygame.draw.rect(self.tela, cor if cheio else tuple(c // 3 for c in cor), rect)
```

Fundo: a cor cheia quando aceso, ou a cor escurecida (cada componente dividido por 3).

### Linha 158

```python
        pygame.draw.rect(self.tela, cor if ativo else CINZA, rect, 2)
```

Borda.

### Linha 159

```python
        self.texto_no_meio(rect, rotulo, (10, 12, 20) if cheio else BRANCO)
```

Texto escuro quando aceso, branco quando não.

### Linha 160

```python
        return ativo and self.clicou(rect)
```

Devolve `True` se estiver ativo e foi clicado.

### Linha 162

```python
    def campo(self, id_, x, y, w, valor, secreto=False, dica=""):
```

Caixa de texto.

### Linha 163

```python
        """Caixa de texto. Ctrl+V cola, Tab vai para o próximo, Enter confirma."""
```

Docstring.

### Linha 164

```python
        valor = valor or ""
```

Valor nunca `None`.

### Linha 165

```python
        self.campos.append(id_)
```

Registra o campo na ordem do Tab.

### Linhas 166 a 167

```python
        larg_campo = w - (70 if secreto else 0)
        rect = self.r(x, y, larg_campo, 34)
```

Campo secreto deixa espaço para o botão "ver".

### Linhas 168 a 170

```python
        if self.clicou(rect):
            self.foco = id_
            self._clicou_campo = True
```

Clicou no campo: ganha o foco.

### Linha 171

```python
        focado = self.foco == id_
```

Está em foco?

### Linhas 172 a 175

```python
        if focado:
            if self.apagar:
                valor = valor[:-self.apagar] if self.apagar <= len(valor) else ""
            valor += self.digitado + (self.colar or "").strip()
```

Em foco: aplica os Backspaces (apaga as últimas letras) e acrescenta o que foi digitado e colado.

### Linhas 176 a 177

```python
        pygame.draw.rect(self.tela, FUNDO_CAMPO, rect)
        pygame.draw.rect(self.tela, AZUL if focado else (70, 76, 100), rect, 2)
```

Fundo e borda (azul quando em foco).

### Linhas 178 a 179

```python
        if not valor and not focado:
            mostrado, cor = dica, (90, 96, 120)
```

Vazio e sem foco: mostra a dica em cinza.

### Linhas 180 a 181

```python
        elif secreto and id_ not in self.mostrar:
            mostrado, cor = ("•" * min(12, max(0, len(valor) - 4)) + valor[-4:]) if valor else "", BRANCO
```

Secreto e não revelado: mostra pontos e só os 4 últimos caracteres.

### Linhas 182 a 183

```python
        else:
            mostrado, cor = valor, BRANCO
```

Senão, o valor.

### Linha 184

```python
        cabe = larg_campo - 24
```

Largura disponível para o texto.

### Linhas 185 a 186

```python
        # digitando: mostra o fim do texto; parado: mostra o começo
        mostrado = font.cauda(mostrado, cabe) if focado else font.cortar(mostrado, cabe)
```

Digitando: mostra o fim do texto; parado: o começo.

### Linhas 187 a 189

```python
        t = font.render(mostrado, 2, cor)
        ty = rect.centery - t.get_height() // 2
        self.tela.blit(t, (rect.x + 10, ty))
```

Desenha o texto centralizado na altura.

### Linhas 190 a 191

```python
        if focado and pygame.time.get_ticks() // 450 % 2:      # cursor piscando
            pygame.draw.rect(self.tela, AZUL, (rect.x + 12 + t.get_width(), rect.y + 7, 3, rect.h - 14))
```

Cursor piscando: a cada 450 ms alterna entre aparecer e sumir (`get_ticks` são os milissegundos desde o início).

### Linhas 192 a 195

```python
        if secreto:
            olho = "ocultar" if id_ in self.mostrar else "ver"
            if self.botao(id_ + ":olho", x + larg_campo + 6, y, 64, olho, CINZA):
                self.mostrar ^= {id_}
```

Campo secreto: botão "ver"/"ocultar". `^=` (ou exclusivo) põe o campo no conjunto se não estiver, ou tira se estiver.

### Linha 196

```python
        return valor
```

Devolve o valor atualizado.

### Linha 198

```python
    def alternar(self, id_, x, y, valor, rotulo):
```

Interruptor liga/desliga.

### Linha 199

```python
        """Interruptor liga/desliga com texto ao lado. Clicar no texto também alterna."""
```

Docstring.

### Linhas 200 a 203

```python
        rect = self.r(x, y, 52, 28)
        largura_txt = font.largura(rotulo)
        if self.clicou(rect) or self.clicou(self.r(x + 60, y, largura_txt + 10, 28)):
            valor = not valor
```

Clicar no interruptor ou no texto inverte o valor.

### Linha 204

```python
        pygame.draw.rect(self.tela, VERDE if valor else (60, 64, 84), rect)
```

Fundo verde quando ligado.

### Linhas 205 a 206

```python
        bolinha = self.r(x + (28 if valor else 4), y + 4, 20, 20)
        pygame.draw.rect(self.tela, BRANCO, bolinha)
```

Bolinha branca à direita (ligado) ou à esquerda (desligado).

### Linha 207

```python
        self.texto(x + 64, y + 14 - font.altura() // 2, rotulo, BRANCO if valor else CINZA)
```

Texto ao lado.

### Linha 208

```python
        return valor
```

Devolve.

### Linha 210

```python
    def numero(self, id_, x, y, valor, minimo, maximo, passo=1, formato="{}"):
```

Seletor de número com "-" e "+".

### Linhas 211 a 212

```python
        if self.botao(id_ + ":-", x, y, 34, "-"):
            valor = max(minimo, valor - passo)
```

"-" diminui sem passar do mínimo.

### Linha 213

```python
        self.texto(x + 46, y + 17 - font.altura() // 2, formato.format(valor))
```

Mostra o número formatado.

### Linha 214

```python
        larg = font.largura(formato.format(maximo)) + 24
```

Espaço reservado para o maior número, para o "+" não pular de lugar.

### Linhas 215 a 216

```python
        if self.botao(id_ + ":+", x + 46 + larg, y, 34, "+"):
            valor = min(maximo, valor + passo)
```

"+" aumenta sem passar do máximo.

### Linha 217

```python
        return valor
```

Devolve.

### Linha 219

```python
    def hora(self, id_, x, y, valor, passo=15):
```

Seletor de horário.

### Linha 220

```python
        """Seletor de horário HH:MM com - e + (de 15 em 15 minutos)."""
```

Docstring.

### Linhas 221 a 222

```python
        h, m = map(int, valor.split(":"))
        total = h * 60 + m
```

Converte "07:30" em minutos desde a meia-noite.

### Linhas 223 a 226

```python
        if self.botao(id_ + ":-", x, y, 34, "-"):
            total = (total - passo) % (24 * 60)
        if self.botao(id_ + ":+", x + 118, y, 34, "+"):
            total = (total + passo) % (24 * 60)
```

"-" e "+" mudam 15 minutos. O `% (24 * 60)` faz o horário dar a volta (23:45 mais 15 vira 00:00).

### Linha 227

```python
        texto = f"{total // 60:02d}:{total % 60:02d}"
```

Volta para "HH:MM" com dois dígitos (`:02d`).

### Linhas 228 a 229

```python
        self.texto_no_meio(self.r(x + 34, y, 84, 34), texto)
        return texto
```

Mostra e devolve.

### Linha 231

```python
    def opcoes(self, id_, x, y, valor, escolhas, largura=150, por_linha=4):
```

Grupo de botões em que só um fica escolhido.

### Linha 232

```python
        """Botões lado a lado; o escolhido fica aceso. escolhas: [(valor, rótulo)]."""
```

Docstring.

### Linhas 233 a 237

```python
        for i, (v, rotulo) in enumerate(escolhas):
            bx = x + (i % por_linha) * (largura + 8)
            by = y + (i // por_linha) * 42
            if self.botao(f"{id_}:{v}", bx, by, largura, rotulo, VERDE if v == valor else (110, 116, 140)):
                valor = v
```

Desenha os botões em linhas de `por_linha`; o escolhido fica verde. Clicar troca o valor.

### Linha 238

```python
        return valor
```

Devolve.

### Linha 240

```python
    def cores(self, id_, x, y, valor):
```

Seletor de cor.

### Linhas 241 a 249

```python
        for i, hexa in enumerate(PALETA):
            rect = self.r(x + i * 40, y, 32, 32)
            cor = tuple(int(hexa[k:k + 2], 16) for k in (1, 3, 5))
            pygame.draw.rect(self.tela, cor, rect)
            if hexa == valor:
                pygame.draw.rect(self.tela, BRANCO, rect.inflate(6, 6), 3)
            if self.clicou(rect):
                valor = hexa
        return valor
```

Um quadrado para cada cor da paleta; o escolhido ganha borda branca (`inflate` aumenta o retângulo). Clicar escolhe.

### Linhas 251 a 253

```python
    @staticmethod
    def largura_chip(rotulo):
        return font.largura(rotulo) + 46
```

Largura de um "chip" para um texto (usado para posicionar vários lado a lado).

### Linha 255

```python
    def chip(self, id_, x, y, rotulo, marcado):
```

Caixinha de marcar com texto.

### Linha 256

```python
        """Caixinha de marcar com texto (serviços, canais do Slack...)."""
```

Docstring.

### Linhas 257 a 260

```python
        w = self.largura_chip(rotulo)
        rect = self.r(x, y, w, 32)
        if self.clicou(rect):
            marcado = not marcado
```

Retângulo; clicar inverte.

### Linhas 261 a 264

```python
        pygame.draw.rect(self.tela, (36, 78, 50) if marcado else FUNDO_CAMPO, rect)
        pygame.draw.rect(self.tela, VERDE if marcado else (70, 76, 100), rect, 2)
        caixa = pygame.Rect(rect.x + 10, rect.centery - 7, 14, 14)
        pygame.draw.rect(self.tela, VERDE if marcado else CINZA, caixa, 2)
```

Fundo e borda verdes quando marcado; desenha a caixinha.

### Linhas 265 a 266

```python
        if marcado:   # "v" de marcado desenhado em pixels
            pygame.draw.lines(self.tela, BRANCO, False, [(caixa.x + 3, caixa.y + 7), (caixa.x + 6, caixa.y + 10), (caixa.x + 11, caixa.y + 3)], 2)
```

Quando marcado, desenha o sinal de visto com três pontos ligados por linhas.

### Linhas 267 a 268

```python
        t = font.render(rotulo, 2, BRANCO if marcado else CINZA)
        self.tela.blit(t, (rect.x + 32, rect.centery - t.get_height() // 2))
```

Texto ao lado.

### Linha 269

```python
        return marcado, w
```

Devolve o estado e a largura.

### Linhas 271 a 276

```python
    def status(self, x, y, mensagem):
        """Mensagem de resultado de um botão: (texto, cor)."""
        if mensagem:
            texto, cor = mensagem
            return self.paragrafo(x, y, texto, 860, cor)
        return y
```

Mostra a mensagem de resultado de um botão (texto e cor) como parágrafo e devolve o y abaixo.

### Linha 278

```python
    def qrcode(self, x, y, texto, tamanho=4):
```

Desenha um QR code.

### Linha 279

```python
        """Desenha um QR code (o celular lê com a câmera)."""
```

Docstring.

### Linhas 280 a 283

```python
        try:
            import qrcode
        except ImportError:
            return
```

Importa a biblioteca `qrcode`; se não estiver instalada, não desenha nada.

### Linhas 284 a 287

```python
        qr = qrcode.QRCode(border=2, box_size=1)
        qr.add_data(texto)
        qr.make(fit=True)
        matriz = qr.get_matrix()
```

Gera o QR code do texto e pega a matriz de quadradinhos (verdadeiro é preto).

### Linha 288

```python
        lado = len(matriz) * tamanho
```

Lado total em pixels.

### Linha 289

```python
        pygame.draw.rect(self.tela, (255, 255, 255), self.r(x, y, lado, lado))
```

Fundo branco.

### Linhas 290 a 293

```python
        for j, linha in enumerate(matriz):
            for i, preto in enumerate(linha):
                if preto:
                    self.tela.fill((0, 0, 0), self.r(x + i * tamanho, y + j * tamanho, tamanho, tamanho))
```

Pinta de preto cada quadradinho verdadeiro, no tamanho pedido.

### Linha 294

```python
        return lado
```

Devolve o lado (para posicionar o que vem depois).
