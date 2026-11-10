# `pixeldigest/ui/effects.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/ui/effects.py)

Animações que aparecem por cima da tela: bom dia, fim do expediente, reunião agendada, alarme, avisos rápidos (toasts) e confete.

### Linhas 1 a 9

```python
"""Animações que aparecem por cima da tela.

Cada efeito tem um tempo de vida (dur) e dois desenhos opcionais:
- draw_baixa(surf): desenha no cenário pequeno (320x180), vira pixel grande;
- draw(tela): desenha na tela grande (1280x720), para textos e cartões.

Efeitos: BomDia (07:00), FimDia (18:00), Agendado (reunião marcada),
Alarme (alarme do celular), Toast (aviso rápido) e Confete.
"""
```

Docstring: cada efeito tem uma duração e dois desenhos opcionais, um no cenário pequeno (que vira pixel grande ao ampliar) e outro na tela grande (textos e cartões).

### Linha 10

```python
import math
```

Importa `math` (seno e cosseno para os movimentos).

### Linha 11

```python
import random
```

Importa `random` (confete e estrelas).

### Linha 13

```python
import pygame
```

Importa o pygame.

### Linha 15

```python
from . import font
```

Importa as fontes.

### Linhas 17 a 20

```python
# Centro horizontal e altura do texto grande; a tela principal ajusta conforme a orientação
CX = 640
BANNER_Y = 250
LARGURA_TELA = 1280
```

Centro horizontal, altura do texto grande e largura da tela. A tela principal muda esses valores quando troca de orientação (na vertical o centro é 360, não 640).

### Linha 22

```python
# ---------- sprites em texto: cada letra é uma cor ----------
```

Comentário: sprites em texto, como nos ícones.

### Linhas 23 a 39

```python
CALENDARIO = [
    "..K..........K..",
    ".RKRRRRRRRRRRKR.",
    ".RKRRRRRRRRRRKR.",
    ".RRRRRRRRRRRRRR.",
    ".RRRRRRRRRRRRRR.",
    ".WWWWWWWWWWWWWW.",
    ".WWWWWWWWWWWWWW.",
    ".WWWWWWWWWWWWWW.",
    ".WWWWWWWWWWWWWW.",
    ".WWWWWWWWWWWWWW.",
    ".WWWWWWWWWWWWWW.",
    ".WWWWWWWWWWWWWW.",
    ".WWWWWWWWWWWWWW.",
    ".WWWWWWWWWWWWWW.",
    ".GGGGGGGGGGGGGG.",
]
```

Calendário: topo vermelho com argolas, corpo branco e base cinza.

### Linhas 40 a 57

```python
DESPERTADOR = [
    ".YY..........YY.",
    "YYYY........YYYY",
    "YYY..KKKKKK..YYY",
    ".Y.KKWWWWWWKK.Y.",
    "..KWWWWKWWWWWK..",
    ".KWWWWWKWWWWWWK.",
    ".KWWWWWKWWWWWWK.",
    "KWWWWWWKWWWWWWWK",
    "KWWWWWWKKKKWWWWK",
    "KWWWWWWWWWWWWWWK",
    ".KWWWWWWWWWWWWK.",
    ".KWWWWWWWWWWWWK.",
    "..KWWWWWWWWWWK..",
    "...KKWWWWWWKK...",
    "..K..KKKKKK..K..",
    ".K............K.",
]
```

Despertador: sinos amarelos em cima, mostrador branco e ponteiros.

### Linha 58

```python
CORES = {"K": (30, 30, 40), "R": (220, 60, 70), "W": (250, 250, 250), "G": (190, 190, 200), "Y": (255, 200, 60)}
```

Paleta desses sprites.

### Linha 61

```python
def sprite(linhas, escala, cores=CORES):
```

Transforma um sprite de texto numa imagem ampliada.

### Linha 62

```python
    s = pygame.Surface((len(linhas[0]) * escala, len(linhas) * escala), pygame.SRCALPHA)
```

Superfície transparente do tamanho do sprite vezes a escala.

### Linhas 63 a 66

```python
    for y, linha in enumerate(linhas):
        for x, ch in enumerate(linha):
            if ch in cores:
                s.fill(cores[ch], (x * escala, y * escala, escala, escala))
```

Para cada letra com cor, pinta um quadrado de `escala` pixels.

### Linha 67

```python
    return s
```

Devolve.

### Linha 70

```python
def ease_out_back(t):
```

Função de suavização (easing) "ease out back".

### Linha 71

```python
    """Passa um pouco do ponto e volta (efeito 'mola')."""
```

Docstring: passa um pouco do ponto e volta, como uma mola.

### Linhas 72 a 74

```python
    c = 1.7
    t -= 1
    return 1 + (c + 1) * t ** 3 + c * t ** 2
```

Fórmula clássica: recebe o progresso de 0 a 1 e devolve um valor que passa de 1 perto do fim e volta para 1. O `c` controla o quanto passa.

### Linha 77

```python
def centro(tela, surf, y, cx=None):
```

Desenha uma imagem centralizada na horizontal.

### Linha 78

```python
    cx = CX if cx is None else cx          # CX muda com a orientação: lê o valor na hora
```

Lê o `CX` na hora da chamada (o comentário explica por quê: ele muda com a orientação; se fosse valor padrão do parâmetro, ficaria congelado no valor inicial).

### Linha 79

```python
    tela.blit(surf, (cx - surf.get_width() // 2, y))
```

Desenha com o centro em `cx`.

### Linha 82

```python
class Efeito:
```

Classe base dos efeitos.

### Linha 83

```python
    dur = 3.0
```

Duração padrão de 3 segundos.

### Linha 84

```python
    bloqueia = False      # True: fica até o usuário fechar (alarme)
```

Efeitos que bloqueiam (o alarme) ficam até o usuário fechar.

### Linhas 86 a 88

```python
    def __init__(self):
        self.t = 0.0
        self.vivo = True
```

Tempo decorrido e se está vivo.

### Linhas 90 a 93

```python
    def update(self, dt):
        self.t += dt
        if self.t >= self.dur and not self.bloqueia:
            self.vivo = False
```

A cada quadro soma o tempo; quando passa da duração e não bloqueia, morre.

### Linhas 95 a 96

```python
    def fechar(self):
        self.vivo = False
```

Fecha na hora (clique ou tecla).

### Linhas 98 a 102

```python
    def draw_baixa(self, surf):
        pass

    def draw(self, tela):
        pass
```

Desenhos vazios; cada efeito sobrescreve o que precisar.

### Linha 105

```python
class Confete(Efeito):
```

Confete.

### Linha 106

```python
    CORES = [(255, 90, 90), (255, 200, 60), (90, 200, 255), (120, 230, 120), (220, 120, 255)]
```

Cores possíveis.

### Linhas 108 a 111

```python
    def __init__(self, x, y, n=90, dur=3.0):
        super().__init__()
        self.dur = dur
        self.p = [[x, y, random.uniform(-380, 380), random.uniform(-620, -150), random.choice(self.CORES)] for _ in range(n)]
```

Cria `n` partículas, cada uma com posição, velocidade horizontal e vertical aleatórias (para cima, por isso negativa) e uma cor.

### Linhas 113 a 118

```python
    def update(self, dt):
        super().update(dt)
        for p in self.p:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 900 * dt          # gravidade
```

Move cada partícula pela velocidade vezes o tempo do quadro e soma a gravidade na velocidade vertical (física simples).

### Linhas 120 a 122

```python
    def draw(self, tela):
        for x, y, *_, cor in self.p:
            tela.fill(cor, (int(x) // 4 * 4, int(y) // 4 * 4, 8, 8))   # "trava" na grade de 4 px
```

Desenha cada partícula como um quadrado de 8 pixels. A posição é arredondada para a grade de 4 pixels (`// 4 * 4`) para combinar com o pixel art. O `*_` ignora os valores do meio da lista.

### Linhas 125 a 126

```python
class Banner(Efeito):
    """Texto grande com as letras caindo uma a uma."""
```

Texto grande com as letras caindo uma por uma.

### Linhas 128 a 131

```python
    def __init__(self, texto, sub="", cor=(255, 255, 255), dur=4.5, y=None):
        super().__init__()
        self.texto, self.sub, self.cor, self.dur = texto.upper(), sub, cor, dur
        self.y = BANNER_Y if y is None else y
```

Guarda texto (em maiúsculas), subtítulo, cor, duração e altura.

### Linhas 133 a 134

```python
    def alpha(self):
        return max(0, min(255, int(255 * (self.dur - self.t) / 0.6)))
```

Transparência: some nos últimos 0,6 segundo (de 255 a 0), limitada entre 0 e 255.

### Linha 136

```python
    def draw(self, tela):
```

Desenha.

### Linhas 137 a 138

```python
        # o maior tamanho que cabe na largura da tela (vertical é mais estreita)
        escala = next((e for e in (6, 5, 4, 3) if font.largura(self.texto, e, "titulo") <= LARGURA_TELA - 60), 3)
```

Escolhe o maior tamanho de letra que cabe na largura da tela (o layout vertical é mais estreito).

### Linhas 139 a 140

```python
        largura = font.largura(self.texto, escala, "titulo")
        x0 = CX - largura // 2
```

Largura total e posição inicial para centralizar.

### Linha 141

```python
        a = self.alpha()
```

Transparência atual.

### Linha 142

```python
        for i, ch in enumerate(self.texto):
```

Para cada letra.

### Linha 143

```python
            t = max(0.0, min(1.0, (self.t - i * 0.05) / 0.5))
```

Progresso desta letra: cada uma começa 0,05 segundo depois da anterior e leva 0,5 segundo para cair.

### Linhas 144 a 145

```python
            if t <= 0 or ch == " ":
                continue
```

Pula letras que ainda não começaram e os espaços.

### Linha 146

```python
            y = self.y - 220 * (1 - ease_out_back(t))
```

Altura: começa 220 pixels acima e cai até o lugar com o efeito de mola.

### Linhas 147 a 148

```python
            letra = font.render(ch, escala, self.cor, shadow=(20, 20, 30), familia="titulo").copy()
            letra.set_alpha(a)
```

Desenha a letra com sombra. O `.copy()` é necessário porque a imagem vem do cache e a transparência não pode alterar a original.

### Linhas 149 a 150

```python
            # cada letra cai no lugar dela: a posição é a largura do texto antes dela
            tela.blit(letra, (x0 + font.largura(self.texto[:i], escala, "titulo"), int(y)))
```

Coloca cada letra na posição certa, medindo a largura do texto antes dela.

### Linhas 151 a 154

```python
        if self.sub and self.t > 0.8:
            s = font.render(self.sub, 3, (240, 240, 240), shadow=(20, 20, 30)).copy()
            s.set_alpha(a)
            centro(tela, s, self.y + 80)
```

Depois de 0,8 segundo, mostra o subtítulo centralizado embaixo.

### Linhas 157 a 158

```python
class BomDia(Efeito):
    """07:00: o sol nasce rápido, a tela ganha um brilho quente e aparece o 'BOM DIA'."""
```

Bom dia (07:00): o sol nasce rápido, a tela ganha um brilho quente e aparece o "BOM DIA".

### Linha 159

```python
    dur = 6.5
```

Duração de 6,5 segundos.

### Linhas 161 a 163

```python
    def __init__(self, nome, n_itens):
        super().__init__()
        self.banner = Banner(f"BOM DIA, {nome}!", f"{n_itens} itens no seu resumo de hoje", (255, 214, 90), self.dur)
```

Cria o banner com o nome e quantos itens há no resumo.

### Linhas 165 a 167

```python
    def update(self, dt):
        super().update(dt)
        self.banner.update(dt)
```

Atualiza o efeito e o banner.

### Linha 169

```python
    def draw_baixa(self, surf):
```

Desenho no cenário pequeno.

### Linha 170

```python
        p = min(1.0, self.t / 2.5)
```

Progresso do nascer do sol nos primeiros 2,5 segundos.

### Linha 171

```python
        y = int(175 - 110 * math.sin(p * math.pi / 2))
```

Altura do sol: sobe seguindo um seno (rápido no começo e devagar no fim).

### Linhas 172 a 174

```python
        brilho = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        brilho.fill((255, 170, 80, int(110 * (1 - self.t / self.dur))))
        surf.blit(brilho, (0, 0))
```

Camada laranja transparente que vai sumindo ao longo do efeito.

### Linhas 175 a 178

```python
        for i in range(12):                  # raios girando
            ang = self.t * 0.8 + i * math.pi / 6
            x2, y2 = CX // 4 + math.cos(ang) * 34, y + math.sin(ang) * 34
            pygame.draw.line(surf, (255, 226, 120), (CX // 4, y), (int(x2), int(y2)))
```

Doze raios girando em volta do sol, calculados com cosseno e seno. `CX // 4` converte o centro para o cenário pequeno (que tem um quarto do tamanho).

### Linhas 179 a 180

```python
        pygame.draw.circle(surf, (255, 200, 80), (CX // 4, y), 18)
        pygame.draw.circle(surf, (255, 236, 130), (CX // 4, y), 13)
```

Dois círculos para o sol (borda e centro mais claro).

### Linhas 182 a 183

```python
    def draw(self, tela):
        self.banner.draw(tela)
```

Desenho na tela grande: o banner.

### Linhas 186 a 187

```python
class FimDia(Efeito):
    """18:00: a lua sobe, as janelas da cidade acendem e aparece 'FIM DO EXPEDIENTE'."""
```

Fim do expediente (18:00): a lua sobe, as janelas acendem e aparece o texto.

### Linha 188

```python
    dur = 6.5
```

Duração.

### Linhas 190 a 193

```python
    def __init__(self):
        super().__init__()
        self.banner = Banner("FIM DO EXPEDIENTE", "bom descanso!", (190, 170, 255), self.dur)
        self.estrelas = [(random.randint(0, 319), random.randint(0, 90), random.random() * 3) for _ in range(40)]
```

Cria o banner e 40 estrelas em posições aleatórias, cada uma com um atraso para aparecer.

### Linhas 195 a 197

```python
    def update(self, dt):
        super().update(dt)
        self.banner.update(dt)
```

Atualiza.

### Linha 199

```python
    def draw_baixa(self, surf):
```

Desenho no cenário pequeno.

### Linha 200

```python
        p = min(1.0, self.t / 2.5)
```

Progresso.

### Linhas 201 a 203

```python
        noite = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        noite.fill((20, 10, 60, int(120 * p * (1 - max(0, self.t - 5) / 1.5))))
        surf.blit(noite, (0, 0))
```

Camada roxa de noite que aparece e some no final.

### Linha 204

```python
        y = int(170 - 120 * math.sin(p * math.pi / 2))
```

Altura da lua.

### Linha 205

```python
        cor_ceu = surf.get_at((150, max(0, y - 20)))[:3]
```

Lê a cor do céu acima da lua.

### Linhas 206 a 207

```python
        pygame.draw.circle(surf, (236, 236, 214), (150, y), 14)
        pygame.draw.circle(surf, cor_ceu, (156, y - 4), 12)      # recorte com a cor do céu = lua crescente
```

Desenha a lua e, por cima, um círculo com a cor do céu deslocado: o que sobra é uma lua crescente.

### Linhas 208 a 210

```python
        for x, ys, atraso in self.estrelas:
            if self.t > atraso and int((self.t + atraso) * 4) % 3:
                surf.set_at((x, ys), (255, 255, 220))
```

Cada estrela aparece depois do seu atraso e pisca (aparece em 2 de cada 3 momentos).

### Linhas 212 a 213

```python
    def draw(self, tela):
        self.banner.draw(tela)
```

Banner.

### Linhas 216 a 217

```python
class Agendado(Efeito):
    """Reunião marcada: o calendário entra voando, ganha o carimbo e solta confete."""
```

Reunião agendada: o calendário entra voando, ganha um carimbo e solta confete.

### Linha 218

```python
    dur = 5.0
```

Duração.

### Linhas 220 a 224

```python
    def __init__(self, pessoa, quando, assunto):
        super().__init__()
        self.pessoa, self.quando, self.assunto = pessoa, quando, assunto
        self.cal = sprite(CALENDARIO, 14)
        self.confete = None
```

Guarda os dados, cria a imagem do calendário e deixa o confete para depois.

### Linhas 226 a 231

```python
    def update(self, dt):
        super().update(dt)
        if self.t > 1.1 and self.confete is None:
            self.confete = Confete(CX, 330, 120)
        if self.confete:
            self.confete.update(dt)
```

Depois de 1,1 segundo cria o confete uma vez e passa a atualizá-lo.

### Linha 233

```python
    def draw(self, tela):
```

Desenha.

### Linhas 234 a 236

```python
        p = min(1.0, self.t / 0.9)
        y = int(760 - (760 - 150) * ease_out_back(p))
        x = CX - self.cal.get_width() // 2
```

O calendário sobe de baixo da tela até a posição final em 0,9 segundo, com efeito de mola.

### Linha 237

```python
        fade = max(0, min(255, int(255 * (self.dur - self.t) / 0.6)))
```

Transparência para sumir no fim.

### Linhas 238 a 240

```python
        cal = self.cal.copy()
        cal.set_alpha(fade)
        tela.blit(cal, (x, y))
```

Desenha o calendário.

### Linhas 241 a 244

```python
        dia = font.render(self.quando.split()[1][:5] if " " in self.quando else self.quando, 5, (40, 40, 50), familia="titulo")
        dia = dia.copy()
        dia.set_alpha(fade)
        tela.blit(dia, (x + (self.cal.get_width() - dia.get_width()) // 2, y + 105))
```

Escreve no calendário a data da reunião (a segunda palavra de "qui 07/11 14:30", ou o texto todo).

### Linhas 245 a 249

```python
        if self.t > 1.1:
            # carimbo: começa grande e "bate" no tamanho certo, com tremida
            q = min(1.0, (self.t - 1.1) / 0.25)
            escala = int(9 - 4 * q)
            tremida = int(math.sin(self.t * 60) * 6 * (1 - q))
```

Depois de 1,1 segundo, o carimbo: começa grande (escala 9) e "bate" no tamanho 5 em 0,25 segundo, tremendo enquanto bate.

### Linhas 250 a 252

```python
            carimbo = font.render("AGENDADO!", escala, (60, 200, 90), shadow=(10, 40, 20), familia="titulo").copy()
            carimbo.set_alpha(fade)
            centro(tela, carimbo, 470 + tremida)
```

Desenha "AGENDADO!" em verde.

### Linhas 253 a 255

```python
            info = font.render(f"{self.quando} com {self.pessoa}", 3, (255, 255, 255), shadow=(20, 20, 30)).copy()
            info.set_alpha(fade)
            centro(tela, info, 540)
```

Embaixo, quando e com quem.

### Linhas 256 a 257

```python
        if self.confete:
            self.confete.draw(tela)
```

Desenha o confete.

### Linhas 260 a 261

```python
class Alarme(Efeito):
    """Alarme do celular: despertador tremendo, borda piscando. Fica até fechar."""
```

Alarme do celular: despertador tremendo e borda piscando, até o usuário fechar.

### Linhas 262 a 263

```python
    dur = 45.0
    bloqueia = True
```

Duração máxima de 45 segundos e bloqueia (não some sozinho antes disso).

### Linhas 265 a 268

```python
    def __init__(self, titulo, texto):
        super().__init__()
        self.titulo, self.texto = titulo, texto
        self.relogio = sprite(DESPERTADOR, 16)
```

Guarda o texto e cria a imagem do despertador.

### Linhas 270 a 273

```python
    def update(self, dt):
        super().update(dt)
        if self.t > self.dur:
            self.vivo = False
```

Fecha sozinho depois de 45 segundos.

### Linha 275

```python
    def draw(self, tela):
```

Desenha.

### Linha 276

```python
        w, h = tela.get_size()
```

Tamanho da tela.

### Linha 277

```python
        pisca = (math.sin(self.t * 10) + 1) / 2
```

Valor que oscila entre 0 e 1 rapidamente (seno).

### Linhas 278 a 279

```python
        borda = int(10 + 14 * pisca)
        cor = (255, int(60 + 80 * pisca), 60)
```

Espessura e cor da borda variam com a oscilação.

### Linhas 280 a 281

```python
        for r in [(0, 0, w, borda), (0, h - borda, w, borda), (0, 0, borda, h), (w - borda, 0, borda, h)]:
            tela.fill(cor, r)
```

Pinta as quatro bordas (cima, baixo, esquerda, direita).

### Linhas 282 a 284

```python
        fundo = pygame.Surface((w, h), pygame.SRCALPHA)
        fundo.fill((60, 0, 0, 90))
        tela.blit(fundo, (0, 0))
```

Escurece a tela com um vermelho transparente.

### Linhas 285 a 288

```python
        dx = int(math.sin(self.t * 45) * 10)
        ang = math.sin(self.t * 30) * 8
        relogio = pygame.transform.rotate(self.relogio, ang)
        tela.blit(relogio, ((w - relogio.get_width()) // 2 + dx, 110))
```

O despertador treme para os lados e gira alguns graus de um lado para o outro (`transform.rotate`).

### Linhas 289 a 291

```python
        caixa = pygame.Surface((760, 170), pygame.SRCALPHA)
        caixa.fill((30, 0, 0, 170))
        tela.blit(caixa, (w // 2 - 380, 386))
```

Caixa escura atrás do texto.

### Linhas 292 a 293

```python
        centro(tela, font.render("ALARME!", 8, (255, 240, 120), shadow=(60, 0, 0), familia="titulo"), 396, w // 2)
        centro(tela, font.render(self.texto or self.titulo, 3, (255, 255, 255), shadow=(60, 0, 0)), 476, w // 2)
```

"ALARME!" grande e a mensagem embaixo.

### Linhas 294 a 295

```python
        if int(self.t * 2) % 2:
            centro(tela, font.render("clique ou aperte qualquer tecla", 2, (255, 220, 220)), 516, w // 2)
```

Instrução para fechar, piscando a cada meio segundo.

### Linhas 298 a 299

```python
class Toast(Efeito):
    """Aviso rápido que desliza do topo."""
```

Aviso rápido que desliza do topo.

### Linha 300

```python
    dur = 6.0
```

Duração.

### Linha 301

```python
    topo_base = 140           # a tela muda para baixo quando o resumo dos e-mails está aberto
```

Altura do primeiro aviso; a tela muda conforme o layout.

### Linhas 303 a 305

```python
    def __init__(self, titulo, texto, cor=(90, 170, 255)):
        super().__init__()
        self.titulo, self.texto, self.cor = titulo, texto, cor
```

Guarda título, texto e cor.

### Linha 307

```python
    def draw(self, tela, indice=0):
```

Desenha; `indice` empilha vários avisos.

### Linhas 308 a 310

```python
        entrada = min(1.0, self.t / 0.35)
        saida = min(1.0, max(0.0, (self.dur - self.t) / 0.35))
        p = min(entrada, saida)
```

Progresso de entrada (0,35 s) e de saída (0,35 s); usa o menor dos dois.

### Linhas 311 a 312

```python
        largura, altura = 620, 80
        x = CX - largura // 2
```

Tamanho e posição centralizada.

### Linha 313

```python
        topo = Toast.topo_base + indice * (altura + 10)          # logo abaixo da barra do topo
```

Altura: cada aviso fica embaixo do anterior.

### Linha 314

```python
        y = int(topo - 40 * (1 - ease_out_back(p)))
```

Desliza 40 pixels com efeito de mola.

### Linha 315

```python
        caixa_alpha = int(255 * p)
```

Transparência acompanha o progresso.

### Linhas 316 a 318

```python
        caixa = pygame.Surface((largura, altura), pygame.SRCALPHA)
        caixa.fill((14, 16, 28, 225))
        caixa.fill(self.cor, (0, 0, 8, altura))
```

Caixa escura com uma faixa colorida à esquerda (cor da empresa).

### Linha 319

```python
        caixa.blit(font.render(font.cortar(self.titulo, largura - 40), 2, self.cor), (22, 8))
```

Título cortado para caber.

### Linhas 320 a 322

```python
        linhas = font.wrap(self.texto, largura - 40, 1)
        if len(linhas) > 2:
            linhas = [linhas[0], font.cortar(" ".join(linhas[1:]), largura - 40, 1)]
```

Texto em até duas linhas; se passar, a segunda linha é cortada com reticências.

### Linhas 323 a 324

```python
        for i, l in enumerate(linhas[:2]):
            caixa.blit(font.render(l, 1, (235, 235, 240)), (22, 36 + i * 19))
```

Desenha as linhas.

### Linhas 325 a 326

```python
        caixa.set_alpha(caixa_alpha)
        tela.blit(caixa, (x, y))
```

Aplica a transparência e desenha.
