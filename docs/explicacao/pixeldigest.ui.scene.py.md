# `pixeldigest/ui/scene.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/ui/scene.py)

O cenário animado em pixel art: céu, sol, lua, estrelas, nuvens, cidade, chuva, relâmpago, neblina e neve. Tudo reage ao clima real e à hora do dia.

### Linhas 1 a 15

```python
"""Cenário em pixel art (320x180 na horizontal ou 180x320 na vertical, ampliado 4x).

O que muda com o clima real:
- cobertura do céu: com muitas nuvens ou chuva o céu fica CINZA (nada de céu azul
  com chuva) e o sol/lua some atrás das nuvens;
- nuvens: desenhadas como em jogo antigo (luz em cima, sombra embaixo, base reta);
  com chuva forma um "teto" de nuvens que vai descendo;
- chuva: gotas em dois tons inclinadas pelo vento, respingos e rua molhada que
  reflete as janelas; trovoada tem relâmpago com galhos e clarão;
- neblina e neve também aparecem quando o código do tempo pede;
- hora do dia: madrugada, amanhecer, dia, pôr do sol e noite, com janelas acendendo.

Tudo é desenhado numa Surface pequena sem suavização; ao ampliar 4x com
"vizinho mais próximo" cada pixel vira um quadradinho.
"""
```

Docstring: o cenário é desenhado numa superfície pequena (320x180 ou 180x320) e ampliado 4 vezes sem suavizar, então cada pixel vira um quadradinho. Lista o que muda com o clima: céu cinza com chuva (sem céu azul), nuvens no estilo de jogo antigo, chuva em dois tons com respingos e rua molhada, relâmpago, neblina, neve e as fases do dia.

### Linha 16

```python
import math
```

Importa `math` (seno, cosseno, pi).

### Linha 17

```python
import random
```

Importa `random`.

### Linha 18

```python
from datetime import datetime
```

Importa `datetime`.

### Linha 20

```python
import pygame
```

Importa o pygame.

### Linha 22

```python
W, H = 320, 180          # tamanho padrão (horizontal); a vertical usa 180x320
```

Tamanho padrão do cenário.

### Linha 24

```python
# (cor do topo do céu, cor do horizonte)
```

Comentário: cada paleta de céu é (cor do topo, cor do horizonte).

### Linhas 25 a 31

```python
NOITE = ((8, 10, 30), (30, 32, 72))
AURORA = ((58, 64, 132), (246, 152, 112))
DIA = ((66, 146, 232), (170, 216, 250))
CREPUSCULO = ((64, 46, 112), (244, 118, 78))
NUBLADO_DIA = ((112, 120, 134), (156, 162, 174))
NUBLADO_NOITE = ((20, 22, 30), (38, 40, 50))
TEMPESTADE_DIA = ((62, 66, 78), (94, 98, 108))
```

Paletas: noite, aurora, dia, crepúsculo, nublado de dia, nublado de noite e tempestade de dia.

### Linhas 33 a 38

```python
PRESETS = {
    "sol": {"nuvens": 0.1, "chuva": 0.0, "trovoada": False, "vento": 8, "codigo": 0},
    "nublado": {"nuvens": 0.85, "chuva": 0.0, "trovoada": False, "vento": 14, "codigo": 3},
    "chuva": {"nuvens": 0.95, "chuva": 0.55, "trovoada": False, "vento": 18, "codigo": 63},
    "tempestade": {"nuvens": 1.0, "chuva": 1.0, "trovoada": True, "vento": 30, "codigo": 95},
}
```

Climas prontos para a demonstração (teclas e imagens do README): quantidade de nuvens (0 a 1), chuva (0 a 1), trovoada, vento e código WMO.

### Linha 41

```python
def mix(a, b, t):
```

Mistura duas cores.

### Linha 42

```python
    """Mistura duas cores: t=0 -> a, t=1 -> b."""
```

Docstring.

### Linha 43

```python
    t = max(0.0, min(1.0, t))
```

Limita `t` entre 0 e 1.

### Linha 44

```python
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
```

Interpolação linear em cada canal (R, G e B): começa em `a` e anda a fração `t` do caminho até `b`.

### Linhas 47 a 48

```python
def mix_par(p1, p2, t):
    return mix(p1[0], p2[0], t), mix(p1[1], p2[1], t)
```

Mistura dois pares de cores (topo e horizonte).

### Linhas 51 a 52

```python
def minutos(dt):
    return dt.hour * 60 + dt.minute + dt.second / 60
```

Converte um horário em minutos desde a meia-noite (com fração dos segundos).

### Linha 55

```python
def fase_do_dia(agora, nascer=None, por=None):
```

Calcula a fase do dia.

### Linha 56

```python
    """Devolve (paleta do céu, luz 0..1, posição do sol 0..1)."""
```

Docstring: devolve a paleta do céu, a luz de 0 a 1 e a posição do sol de 0 (nascendo) a 1 (se pondo).

### Linhas 57 a 59

```python
    m = minutos(agora)
    n = minutos(nascer) if nascer else 6 * 60
    p = minutos(por) if por else 18 * 60 + 30
```

Minutos de agora, do nascer (padrão 6h) e do pôr do sol (padrão 18h30).

### Linha 60

```python
    sol = (m - n) / max(1, (p - n))
```

Posição do sol: quanto do caminho entre nascer e pôr já passou. `max(1, ...)` evita divisão por zero.

### Linhas 61 a 62

```python
    if m < n - 50 or m > p + 50:
        return NOITE, 0.0, sol
```

Mais de 50 minutos antes do nascer ou depois do pôr: noite, luz zero.

### Linhas 63 a 64

```python
    if m < n:
        return mix_par(NOITE, AURORA, (m - (n - 50)) / 50), 0.3 * (m - (n - 50)) / 50, sol
```

Nos 50 minutos antes do nascer: vai de noite para aurora, luz até 0,3.

### Linhas 65 a 66

```python
    if m < n + 60:
        return mix_par(AURORA, DIA, (m - n) / 60), 0.3 + 0.7 * (m - n) / 60, sol
```

Na primeira hora depois do nascer: de aurora para dia, luz de 0,3 a 1.

### Linhas 67 a 68

```python
    if m < p - 60:
        return DIA, 1.0, sol
```

Até 1 hora antes do pôr: dia pleno.

### Linhas 69 a 70

```python
    if m < p:
        return mix_par(DIA, CREPUSCULO, (m - (p - 60)) / 60), 1.0 - 0.6 * (m - (p - 60)) / 60, sol
```

Na última hora antes do pôr: de dia para crepúsculo, luz caindo.

### Linha 71

```python
    return mix_par(CREPUSCULO, NOITE, (m - p) / 50), 0.4 - 0.4 * (m - p) / 50, sol
```

Depois do pôr: de crepúsculo para noite.

### Linhas 74 a 75

```python
def limitar(v):
    return max(0.0, min(1.0, v))
```

Limita um valor entre 0 e 1.

### Linha 78

```python
class Cena:
```

Classe do cenário.

### Linha 79

```python
    def __init__(self, largura=W, altura=H, semente=7):
```

Construtor; a semente fixa faz a cidade sair sempre igual.

### Linha 80

```python
        self.W, self.H = largura, altura
```

Guarda o tamanho.

### Linha 81

```python
        self.CHAO = altura - 22
```

Linha do chão, 22 pixels acima do fim.

### Linha 82

```python
        self.rng = random.Random(semente)
```

Gerador aleatório próprio com semente (não interfere no `random` global).

### Linha 83

```python
        self.surf = pygame.Surface((largura, altura))
```

Superfície do cenário.

### Linha 84

```python
        self.vis = dict(PRESETS["sol"])        # clima mostrado agora (vai suavizando)
```

Clima mostrado agora, que vai se aproximando do alvo aos poucos.

### Linha 85

```python
        self.alvo = dict(PRESETS["sol"])       # clima de destino
```

Clima de destino.

### Linhas 86 a 87

```python
        self.nascer = None
        self.por = None
```

Horários de nascer e pôr do sol.

### Linha 88

```python
        self.tempo = 0.0
```

Tempo total da animação.

### Linha 89

```python
        self.gotas, self.respingos, self.flocos = [], [], []
```

Listas de gotas, respingos e flocos.

### Linhas 90 a 91

```python
        self.flash = 0.0
        self.raio = None
```

Clarão do relâmpago e o desenho do raio atual.

### Linha 92

```python
        self.luz_janelas = 0.0
```

Quanto das janelas está acesa.

### Linha 93

```python
        self.janelas_forcadas = 0.0           # animação das 18h acende tudo
```

Força extra para acender as janelas (animação das 18h).

### Linha 94

```python
        self._sprites = {}                    # nuvens já desenhadas (por forma, tamanho e cor)
```

Cache das imagens de nuvem.

### Linha 95

```python
        self._camadas = {}                    # superfícies transparentes reaproveitadas
```

Cache das camadas transparentes (criar uma superfície por quadro gastaria memória).

### Linhas 96 a 97

```python
        self._gerar_cidade()
        self._gerar_ceu()
```

Gera a cidade e o céu uma vez só.

### Linha 99

```python
    # ---------- geração (uma vez só, com semente fixa) ----------
```

Comentário: geração com semente fixa.

### Linha 100

```python
    def _gerar_cidade(self):
```

Gera os prédios.

### Linhas 101 a 104

```python
        r = self.rng
        self.predios = []
        x = -4
        alto = int(self.H * 0.52)
```

Atalho para o gerador, lista de prédios, posição inicial (um pouco fora da tela) e altura máxima (52% da cena).

### Linha 105

```python
        while x < self.W:
```

Enquanto não preencher a largura.

### Linhas 106 a 108

```python
            w = r.randint(16, 38)
            h = r.randint(28, max(40, alto))
            cor = mix((34, 38, 58), (58, 60, 84), r.random())
```

Largura, altura e cor aleatórias (entre dois tons de azul escuro).

### Linhas 109 a 112

```python
            janelas = []
            for jy in range(self.CHAO - h + 6, self.CHAO - 6, 7):
                for jx in range(x + 4, x + w - 4, 6):
                    janelas.append((jx, jy, r.random()))       # 3º valor: quando essa janela acende
```

Janelas em grade (a cada 7 pixels na vertical e 6 na horizontal). O terceiro valor é aleatório e define quando aquela janela acende: as janelas com valor menor acendem primeiro.

### Linha 113

```python
            antena = r.random() < 0.3
```

30% dos prédios têm antena.

### Linha 114

```python
            self.predios.append((x, w, h, cor, janelas, antena))
```

Guarda o prédio.

### Linha 115

```python
            x += w + r.randint(0, 3)
```

Próximo prédio, com um vão de até 3 pixels.

### Linha 117

```python
    def _gerar_ceu(self):
```

Gera o céu.

### Linhas 118 a 119

```python
        r = self.rng
        topo_cidade = self.CHAO - int(self.H * 0.52)
```

Gerador e altura do topo da cidade.

### Linha 120

```python
        self.estrelas = [(r.randint(0, self.W - 1), r.randint(0, max(20, topo_cidade)), r.random() * 6.28) for _ in range(70)]
```

70 estrelas com posição e uma fase para piscar.

### Linha 121

```python
        self.nuvens = []
```

Lista de nuvens.

### Linhas 122 a 125

```python
        for i in range(24):
            forma = [(r.randint(-14, 14), r.randint(-5, 2), r.randint(5, 10)) for _ in range(r.randint(4, 7))]
            self.nuvens.append({"x": r.uniform(-30, self.W + 30), "y": r.uniform(10, max(30, topo_cidade * 0.8)),
                                "forma": forma, "vel": r.uniform(0.4, 1.0), "ordem": r.random(), "id": i})
```

24 nuvens, cada uma formada por 4 a 7 círculos (deslocamento x, y e raio), com posição, velocidade, ordem de desenho e id.

### Linha 126

```python
        self.nuvens.sort(key=lambda n: n["ordem"])
```

Ordena pela ordem de desenho.

### Linha 127

```python
        self.teto = [[(r.randint(-12, 12), r.randint(-3, 3), r.randint(9, 14)) for _ in range(5)] for _ in range(6)]
```

Formas do "teto" de nuvens (6 formas de 5 círculos), usado com chuva.

### Linha 129

```python
    # ---------- clima ----------
```

Comentário: clima.

### Linha 130

```python
    def definir_clima(self, clima=None, preset=None):
```

Define o clima de destino.

### Linha 131

```python
        """Recebe o Clima real (Open-Meteo) ou um preset da demonstração."""
```

Docstring.

### Linhas 132 a 133

```python
        if preset:
            self.alvo = dict(PRESETS[preset])
```

Com preset: copia o clima pronto.

### Linhas 134 a 137

```python
        elif clima:
            self.alvo = {"nuvens": clima.nuvens / 100, "chuva": clima.intensidade_chuva,
                         "trovoada": clima.trovoada, "vento": clima.vento_kmh, "codigo": clima.codigo}
            self.nascer, self.por = clima.nascer, clima.por_do_sol
```

Com clima real: converte nuvens de porcentagem para 0 a 1, usa a intensidade da chuva, trovoada, vento e código, e guarda nascer e pôr do sol.

### Linhas 139 a 142

```python
    @property
    def escuro(self):
        """0 = céu normal, 1 = bem escuro. Nuvens escurecem um pouco; chuva escurece muito."""
        return min(1.0, 0.18 * self.vis["nuvens"] + 0.62 * self.vis["chuva"])
```

Propriedade `escuro`: quanto a tela escurece. Nuvens pesam 18% e chuva 62%, com teto de 1. É a regra "mais chuva, mais escuro".

### Linhas 144 a 147

```python
    @property
    def cobertura(self):
        """0 = céu aberto, 1 = céu totalmente fechado (cinza). Chuva fecha o céu rápido."""
        return limitar(max((self.vis["nuvens"] - 0.45) / 0.5, self.vis["chuva"] * 2.5))
```

Propriedade `cobertura`: quanto o céu está fechado. Começa a fechar com 45% de nuvens e a chuva fecha rápido (multiplicada por 2,5).

### Linhas 149 a 150

```python
    def acender_janelas(self):
        self.janelas_forcadas = 1.0
```

Acende todas as janelas (animação das 18h).

### Linhas 152 a 156

```python
    def _camada(self, nome):
        """Superfície transparente do tamanho da cena, criada uma vez só."""
        if nome not in self._camadas:
            self._camadas[nome] = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        return self._camadas[nome]
```

Devolve uma camada transparente do tamanho da cena, criando só na primeira vez.

### Linha 158

```python
    # ---------- animação ----------
```

Comentário: animação.

### Linha 159

```python
    def update(self, dt, agora):
```

Atualiza o cenário a cada quadro (`dt` é o tempo do quadro).

### Linha 160

```python
        self.tempo += dt
```

Soma o tempo.

### Linha 161

```python
        k = min(1.0, dt * 0.8)                       # transição de clima em ~3 segundos
```

Fator de aproximação: a transição de clima leva uns 3 segundos.

### Linhas 162 a 163

```python
        for chave in ("nuvens", "chuva", "vento"):
            self.vis[chave] += (self.alvo[chave] - self.vis[chave]) * k
```

Aproxima nuvens, chuva e vento do alvo um pouco a cada quadro (suavização exponencial).

### Linhas 164 a 165

```python
        self.vis["trovoada"] = self.alvo["trovoada"]
        self.vis["codigo"] = self.alvo.get("codigo", 0)
```

Trovoada e código mudam na hora.

### Linha 167

```python
        _, luz, _ = fase_do_dia(agora, self.nascer, self.por)
```

Luz atual.

### Linha 168

```python
        alvo_janelas = 0.08 + 0.6 * (1 - luz) + 0.25 * self.escuro
```

Quanto as janelas deveriam estar acesas: um pouco sempre, muito mais à noite e um pouco mais com tempo escuro.

### Linha 169

```python
        alvo_janelas = max(alvo_janelas, self.janelas_forcadas * 0.9)
```

Se a animação das 18h está ativa, acende quase tudo.

### Linha 170

```python
        self.luz_janelas += (alvo_janelas - self.luz_janelas) * min(1.0, dt * 0.7)
```

Aproxima suavemente.

### Linha 171

```python
        self.janelas_forcadas = max(0.0, self.janelas_forcadas - dt * 0.02)
```

A força da animação das 18h vai acabando devagar.

### Linha 173

```python
        vento = self.vis["vento"]
```

Vento atual.

### Linhas 174 a 177

```python
        for n in self.nuvens:
            n["x"] += (2 + vento * 0.25) * n["vel"] * dt
            if n["x"] > self.W + 45:
                n["x"] = -45
```

Move cada nuvem para a direita conforme o vento e a velocidade dela. Quando sai pela direita, volta pela esquerda.

### Linha 179

```python
        # chuva: nasce em cima, cai inclinada com o vento, vira respingo no chão
```

Comentário: chuva.

### Linha 180

```python
        chuva, W, CHAO = self.vis["chuva"], self.W, self.CHAO
```

Atalhos.

### Linha 181

```python
        nascem = chuva * 3.2 * W * dt
```

Quantas gotas nascem neste quadro: proporcional à chuva, à largura e ao tempo.

### Linhas 182 a 184

```python
        while nascem > 0 and len(self.gotas) < 1100:
            if nascem < 1 and self.rng.random() > nascem:
                break
```

Cria gotas até o limite de 1100. Quando falta menos de uma gota, sorteia se cria ou não (assim a média fica certa mesmo com valores fracionários).

### Linha 185

```python
            perto = self.rng.random() < 0.35                       # gotas "perto" são maiores e mais claras
```

35% das gotas ficam "perto": maiores, mais claras e mais rápidas (dá profundidade).

### Linhas 186 a 188

```python
            self.gotas.append([self.rng.uniform(-40, W + 10), self.rng.uniform(-24, 0),
                               self.rng.uniform(230, 290) if perto else self.rng.uniform(170, 210),
                               CHAO + self.rng.uniform(-2, 20), perto])
```

Cada gota: x, y (logo acima da tela), velocidade de queda, altura do chão onde ela cai (varia para parecer perspectiva) e se está perto.

### Linha 189

```python
            nascem -= 1
```

Uma gota a menos para criar.

### Linha 190

```python
        vx = vento * 1.3
```

Velocidade horizontal pelo vento.

### Linhas 191 a 199

```python
        vivas = []
        for g in self.gotas:
            g[0] += vx * dt
            g[1] += g[2] * dt
            if g[1] >= g[3]:
                self.respingos.append([g[0], g[3], 0.18])
            else:
                vivas.append(g)
        self.gotas = vivas
```

Move cada gota. Quando chega no chão, vira respingo de 0,18 segundo; senão continua viva.

### Linha 200

```python
        self.respingos = [[x, y, t - dt] for x, y, t in self.respingos if t - dt > 0]
```

Diminui o tempo dos respingos e remove os que acabaram.

### Linha 202

```python
        # neve (códigos 71 a 77, 85, 86)
```

Comentário: neve.

### Linhas 203 a 206

```python
        codigo = self.vis["codigo"]
        if 71 <= codigo <= 77 or codigo in (85, 86):
            while len(self.flocos) < 160:
                self.flocos.append([self.rng.uniform(0, W), self.rng.uniform(-self.H, 0), self.rng.uniform(14, 30), self.rng.random() * 6])
```

Se o código é de neve, mantém 160 flocos com posição, velocidade e fase.

### Linhas 207 a 211

```python
        for f in self.flocos:
            f[1] += f[2] * dt
            f[0] += math.sin(self.tempo * 1.5 + f[3]) * 0.3 + vento * 0.02
            if f[1] > CHAO + 10:
                f[1], f[0] = self.rng.uniform(-20, 0), self.rng.uniform(0, W)
```

Cada floco cai e balança para os lados com um seno. Quando passa do chão, volta para cima numa posição aleatória.

### Linhas 212 a 213

```python
        if not (71 <= codigo <= 77 or codigo in (85, 86)):
            self.flocos = []
```

Sem neve, apaga os flocos.

### Linha 215

```python
        # relâmpago com galhos
```

Comentário: relâmpago.

### Linha 216

```python
        self.flash = max(0.0, self.flash - dt * 3.2)
```

O clarão vai apagando.

### Linhas 217 a 219

```python
        if self.vis["trovoada"] and self.rng.random() < dt * 0.25:
            self.flash = 1.0
            self.raio = self._gerar_raio(self.rng.randint(30, W - 30), 0, CHAO - 30, 0)
```

Com trovoada, há uma pequena chance por quadro de cair um raio: clarão máximo e um raio novo em posição aleatória.

### Linha 221

```python
    def _gerar_raio(self, x, y, fim, nivel):
```

Gera um raio com galhos (função recursiva).

### Linha 222

```python
        pontos, galhos = [(x, y)], []
```

Pontos do raio e galhos.

### Linhas 223 a 226

```python
        while y < fim:
            y += self.rng.randint(5, 11)
            x += self.rng.randint(-7, 7)
            pontos.append((x, y))
```

Desce em passos de 5 a 11 pixels, desviando até 7 para os lados.

### Linhas 227 a 228

```python
            if nivel < 1 and self.rng.random() < 0.25:
                galhos.append(self._gerar_raio(x, y, y + self.rng.randint(12, 30), nivel + 1))
```

No raio principal (nível 0), 25% de chance por passo de criar um galho curto (nível 1, que não cria mais galhos).

### Linha 229

```python
        return {"pontos": pontos, "galhos": galhos}
```

Devolve os pontos e os galhos.

### Linha 231

```python
    # ---------- desenho ----------
```

Comentário: desenho.

### Linha 232

```python
    def _ceu(self, paleta, luz):
```

Desenha o céu.

### Linha 233

```python
        nublado = mix_par(NUBLADO_NOITE, NUBLADO_DIA, luz)
```

Cor de céu nublado para a luz atual.

### Linha 234

```python
        topo, horizonte = mix_par(paleta, nublado, self.cobertura * 0.95)
```

Mistura o céu normal com o nublado conforme a cobertura. Com chuva, o céu azul some de verdade.

### Linhas 235 a 236

```python
        tempestade = mix_par(NUBLADO_NOITE, TEMPESTADE_DIA, luz)
        topo, horizonte = mix_par((topo, horizonte), tempestade, self.vis["chuva"] * 0.7)
```

Com chuva, mistura ainda com a cor de tempestade.

### Linhas 237 a 238

```python
        for y in range(self.CHAO):
            pygame.draw.line(self.surf, mix(topo, horizonte, y / self.CHAO), (0, y), (self.W, y))
```

Pinta uma linha horizontal por altura, degradê do topo até o horizonte.

### Linha 240

```python
    def _astros(self, luz, sol):
```

Desenha estrelas, sol e lua.

### Linha 241

```python
        visivel = limitar(1 - self.cobertura * 1.4)           # some atrás das nuvens
```

Visibilidade: com o céu fechado, os astros somem atrás das nuvens.

### Linhas 242 a 243

```python
        W, CHAO = self.W, self.CHAO
        altura_arco = CHAO * 0.75
```

Atalhos e altura do arco que o sol faz.

### Linhas 244 a 248

```python
        if luz < 0.35 and visivel > 0:
            for x, y, fase in self.estrelas:
                brilho = (0.5 + 0.5 * math.sin(self.tempo * 2 + fase)) * (1 - luz / 0.35) * visivel
                if brilho > 0.35:
                    self.surf.set_at((x, y), mix((60, 60, 90), (255, 255, 230), brilho))
```

Com pouca luz, desenha as estrelas piscando (seno com a fase de cada uma), mais fracas conforme a luz e a cobertura.

### Linhas 249 a 250

```python
        camada = self._camada("astros")
        camada.fill((0, 0, 0, 0))
```

Camada transparente dos astros, limpa a cada quadro.

### Linha 251

```python
        if 0 <= sol <= 1:
```

Se o sol está entre o nascer e o pôr.

### Linhas 252 a 253

```python
            x = int(18 + sol * (W - 36))
            y = int(CHAO - 14 - math.sin(math.pi * sol) * altura_arco)
```

Posição do sol: anda da esquerda para a direita e sobe e desce num arco (seno).

### Linhas 254 a 255

```python
            if visivel > 0:
                a = int(255 * visivel)
```

Se visível, transparência pela visibilidade.

### Linhas 256 a 259

```python
                for i in range(8):                               # raios em cruz e diagonal (pixel art)
                    ang = i * math.pi / 4 + self.tempo * 0.1
                    x2, y2 = x + math.cos(ang) * 15, y + math.sin(ang) * 15
                    pygame.draw.line(camada, (255, 214, 90, a // 2), (x, y), (int(x2), int(y2)))
```

Oito raios girando devagar.

### Linhas 260 a 262

```python
                pygame.draw.circle(camada, (255, 196, 70, a), (x, y), 10)
                pygame.draw.circle(camada, (255, 232, 120, a), (x, y), 8)
                pygame.draw.circle(camada, (255, 250, 200, a), (x - 2, y - 2), 3)
```

Três círculos: borda, corpo e um brilho no canto.

### Linhas 263 a 265

```python
        else:
            noite = (sol - 1) if sol > 1 else (sol + 1)
            noite = limitar(noite)
```

Senão, é noite: calcula a posição da lua no arco noturno.

### Linhas 266 a 267

```python
            x = int(18 + noite * (W - 36))
            y = int(CHAO - 20 - math.sin(math.pi * noite) * altura_arco * 0.9)
```

Posição da lua.

### Linhas 268 a 272

```python
            if visivel > 0:
                a = int(255 * visivel)
                pygame.draw.circle(camada, (236, 236, 214, a), (x, y), 7)
                pygame.draw.circle(camada, (200, 200, 184, a), (x - 2, y - 1), 2)
                pygame.draw.circle(camada, (210, 210, 190, a), (x + 2, y + 3), 1)
```

Desenha a lua com duas crateras.

### Linha 273

```python
        self.surf.blit(camada, (0, 0))
```

Copia a camada para o cenário.

### Linha 275

```python
    def _cores_nuvem(self, luz):
```

Cores da nuvem.

### Linha 276

```python
        """Três tons da nuvem (luz, corpo, sombra), conforme hora e chuva."""
```

Docstring: três tons (luz, corpo e sombra).

### Linha 277

```python
        clara = mix((96, 100, 124), (250, 250, 255), luz)
```

Tom claro: mais escuro à noite e branco de dia.

### Linha 278

```python
        corpo = mix(clara, mix((60, 64, 76), (132, 138, 150), luz), max(self.cobertura * 0.6, self.vis["chuva"]))
```

Corpo: escurece com a cobertura e com a chuva.

### Linha 279

```python
        return mix(corpo, (255, 255, 255), 0.25), corpo, mix(corpo, (20, 22, 32), 0.32)
```

Devolve luz (corpo misturado com branco), corpo e sombra (corpo misturado com quase preto).

### Linha 281

```python
    def _sprite_nuvem(self, forma, escala, tons, chave):
```

Desenha uma nuvem.

### Linha 282

```python
        """Nuvem em pixel art: luz em cima, sombra embaixo e base reta (guardada em cache)."""
```

Docstring.

### Linhas 283 a 285

```python
        chave = (chave, round(escala, 1), tons)
        if chave in self._sprites:
            return self._sprites[chave]
```

Chave do cache e devolução se já existir.

### Linha 286

```python
        luz, corpo, sombra = tons
```

Separa os tons.

### Linha 287

```python
        circulos = [(dx * escala, dy * escala, max(2, r * escala)) for dx, dy, r in forma]
```

Círculos da forma aumentados pela escala.

### Linhas 288 a 292

```python
        x0 = min(dx - r for dx, dy, r in circulos) - 2
        x1 = max(dx + r for dx, dy, r in circulos) + 2
        y0 = min(dy - r for dx, dy, r in circulos) - 2
        base = max(dy for dx, dy, r in circulos) + 3 * escala          # linha da base reta
        w, h = int(x1 - x0) + 1, int(base - y0) + 4
```

Calcula os limites da nuvem e a linha da base reta, e o tamanho da imagem.

### Linha 293

```python
        s = pygame.Surface((w, h), pygame.SRCALPHA)
```

Superfície transparente.

### Linhas 294 a 296

```python
        for camada, cor, dy_extra, encolhe in ((0, sombra, 3, 0), (1, luz, -1, 0), (2, corpo, 1, 1)):
            for dx, dy, r in circulos:
                pygame.draw.circle(s, cor, (int(dx - x0), int(dy - y0 + dy_extra)), int(r - encolhe))
```

Desenha três vezes os mesmos círculos: a sombra deslocada para baixo, a luz deslocada para cima e o corpo no meio, um pouco menor. Sobram uma borda clara em cima e uma escura embaixo, o visual de nuvem de jogo antigo.

### Linhas 297 a 298

```python
        corte = int(base - y0)
        s.fill((0, 0, 0, 0), (0, corte, w, h - corte))                  # corta embaixo = base reta
```

Apaga tudo abaixo da linha da base: a nuvem fica com a base reta.

### Linhas 299 a 301

```python
        for x in range(w):                                              # faixa de sombra na base
            if s.get_at((x, corte - 3)).a:
                s.fill(sombra, (x, corte - 2, 1, 2))
```

Desenha uma faixa de sombra na base.

### Linhas 302 a 303

```python
        if len(self._sprites) > 260:
            self._sprites.clear()
```

Se o cache passou de 260 imagens, esvazia.

### Linhas 304 a 305

```python
        self._sprites[chave] = s
        return s
```

Guarda e devolve.

### Linha 307

```python
    def _nuvens(self, luz):
```

Desenha as nuvens.

### Linha 308

```python
        nuvens, chuva, cob = self.vis["nuvens"], self.vis["chuva"], self.cobertura
```

Atalhos.

### Linha 309

```python
        tons = tuple(tuple(c // 6 * 6 for c in cor) for cor in self._cores_nuvem(luz))   # tons arredondados = menos sprites
```

Tons arredondados para múltiplos de 6, para reaproveitar mais imagens do cache.

### Linha 310

```python
        # teto de nuvens: começa a fechar o céu com a cobertura e desce com a chuva
```

Comentário: o teto de nuvens.

### Linha 311

```python
        if cob > 0.25:
```

Só aparece com o céu bem fechado.

### Linha 312

```python
            borda = int(-28 + cob * 26 + chuva * self.H * 0.18)
```

Borda do teto: desce com a cobertura e com a chuva.

### Linhas 313 a 314

```python
            luz_t, corpo_t, sombra_t = tons
            escuro_t = (mix(luz_t, sombra_t, 0.5), sombra_t, mix(sombra_t, (10, 12, 18), 0.3))
```

Tons mais escuros para o teto.

### Linhas 315 a 316

```python
            if borda > 0:
                self.surf.fill(sombra_t, (0, 0, self.W, borda))
```

Acima da borda, pinta tudo da cor de sombra.

### Linhas 317 a 320

```python
            for i, x in enumerate(range(-20, self.W + 40, 34)):
                deriva = (self.tempo * (3 + self.vis["vento"] * 0.15)) % 34
                sp = self._sprite_nuvem(self.teto[i % len(self.teto)], 1.6, escuro_t, f"teto{i % len(self.teto)}")
                self.surf.blit(sp, (int(x + deriva - sp.get_width() / 2), borda - sp.get_height() + 8))
```

Uma fileira de nuvens grandes ao longo da borda, andando com o vento.

### Linha 321

```python
        quantas = int(2 + nuvens * 22)
```

Quantidade de nuvens soltas: de 2 a 24 conforme as nuvens.

### Linha 322

```python
        escala = 1 + chuva * 0.6
```

Com chuva as nuvens ficam maiores.

### Linhas 323 a 326

```python
        for n in self.nuvens[:quantas]:
            y = n["y"] * (1 - 0.5 * chuva) + chuva * 12
            sp = self._sprite_nuvem(n["forma"], escala, tons, n["id"])
            self.surf.blit(sp, (int(n["x"] - sp.get_width() / 2), int(y - sp.get_height() / 2)))
```

Desenha cada nuvem; com chuva elas descem um pouco.

### Linha 328

```python
    def _neblina(self, luz):
```

Desenha a neblina.

### Linhas 329 a 330

```python
        if self.vis["codigo"] not in (45, 48):
            return
```

Só nos códigos 45 e 48.

### Linhas 331 a 333

```python
        camada = self._camada("neblina")
        camada.fill((0, 0, 0, 0))
        cor = mix((60, 64, 74), (210, 214, 220), luz)
```

Camada transparente e cor da névoa conforme a luz.

### Linhas 334 a 338

```python
        for i in range(6):
            y = self.CHAO - 12 - i * 16
            x = int((self.tempo * (4 + i)) % (self.W + 80)) - 80
            for k in range(-1, self.W // 120 + 2):
                pygame.draw.ellipse(camada, (*cor, 70), (x + k * 140, y, 120, 10))
```

Seis faixas de elipses translúcidas em alturas diferentes, andando em velocidades diferentes.

### Linha 339

```python
        self.surf.blit(camada, (0, 0))
```

Copia para o cenário.

### Linha 341

```python
    def _cidade(self, luz):
```

Desenha a cidade.

### Linhas 342 a 344

```python
        noite = 1 - luz
        CHAO = self.CHAO
        clarao = self.flash > 0.5
```

Noite (oposto da luz), chão e se o relâmpago está clareando.

### Linha 345

```python
        for x, w, h, cor, janelas, antena in self.predios:
```

Para cada prédio.

### Linha 346

```python
            c = mix(mix(cor, (92, 100, 134), luz * 0.45), (14, 16, 26), noite * 0.6 + self.escuro * 0.3)
```

Cor do prédio: clareia de dia, escurece à noite e com tempo ruim.

### Linhas 347 a 348

```python
            if clarao:
                c = mix(c, (200, 210, 240), 0.35)
```

No clarão do raio, o prédio fica mais claro.

### Linha 349

```python
            pygame.draw.rect(self.surf, c, (x, CHAO - h, w, h))
```

Retângulo do prédio.

### Linha 350

```python
            pygame.draw.line(self.surf, mix(c, (255, 255, 255), 0.12), (x, CHAO - h), (x + w - 1, CHAO - h))
```

Linha clara no topo (luz).

### Linha 351

```python
            pygame.draw.line(self.surf, mix(c, (0, 0, 0), 0.25), (x + w - 1, CHAO - h), (x + w - 1, CHAO))   # lado na sombra
```

Linha escura no lado direito (sombra).

### Linhas 352 a 355

```python
            if antena:
                pygame.draw.line(self.surf, c, (x + w // 2, CHAO - h), (x + w // 2, CHAO - h - 7))
                if int(self.tempo * 1.5) % 2:
                    self.surf.set_at((x + w // 2, CHAO - h - 8), (255, 70, 70))
```

Antena com uma luz vermelha piscando.

### Linhas 356 a 361

```python
            for jx, jy, quando in janelas:
                if quando < self.luz_janelas:
                    cor_j = (255, 214, 120) if quando % 0.1 > 0.02 else (190, 230, 255)
                else:
                    cor_j = mix((120, 160, 210), (30, 34, 50), max(noite, self.cobertura * 0.6))
                self.surf.fill(cor_j, (jx, jy, 2, 3))
```

Janelas: acesas (amarelas, algumas azuladas, como televisões) se o valor delas for menor que a luz das janelas; apagadas em azul-acinzentado.

### Linha 362

```python
        # rua
```

Comentário: rua.

### Linha 363

```python
        rua = mix((54, 54, 64), (24, 24, 32), noite)
```

Cor da rua conforme a hora.

### Linhas 364 a 366

```python
        molhada = self.vis["chuva"] > 0.12
        if molhada:
            rua = mix(rua, (30, 34, 48), 0.4)
```

Com chuva, a rua fica molhada e mais escura.

### Linhas 367 a 368

```python
        pygame.draw.rect(self.surf, rua, (0, CHAO, self.W, self.H - CHAO))
        pygame.draw.line(self.surf, mix((90, 90, 100), (40, 40, 50), noite), (0, CHAO), (self.W, CHAO))
```

Desenha a rua e a guia.

### Linhas 369 a 370

```python
        for x in range(0, self.W, 24):
            self.surf.fill(mix((200, 190, 120), (90, 86, 60), noite), (x, CHAO + 11, 10, 1))
```

Faixas amarelas tracejadas.

### Linhas 371 a 377

```python
        if molhada:   # reflexo das janelas acesas no asfalto molhado
            for x, w, h, cor, janelas, antena in self.predios:
                acesas = sum(1 for _, _, q in janelas if q < self.luz_janelas)
                if acesas:
                    brilho = mix(rua, (255, 214, 120), min(0.5, acesas / 40))
                    for k in range(x + 3, x + w - 3, 6):
                        self.surf.fill(brilho, (k, CHAO + 3 + (k % 3), 2, 4 + (k % 4)))
```

Rua molhada: desenha o reflexo das janelas acesas de cada prédio no asfalto, mais forte quanto mais janelas acesas.

### Linha 379

```python
    def _chuva(self):
```

Desenha a chuva e a neve.

### Linhas 380 a 381

```python
        claro, escuro = (178, 196, 236), (118, 136, 186)
        vx = self.vis["vento"] * 1.3
```

Dois tons e a velocidade horizontal.

### Linhas 382 a 385

```python
        for x, y, vy, _, perto in self.gotas:
            comprimento = 6 if perto else 3
            inclina = vx * comprimento / max(vy, 1)
            pygame.draw.line(self.surf, claro if perto else escuro, (int(x), int(y)), (int(x - inclina), int(y - comprimento)))
```

Cada gota é uma linha inclinada pelo vento (a inclinação depende da razão entre velocidade horizontal e vertical). Gotas perto são maiores e mais claras.

### Linhas 386 a 391

```python
        for x, y, t in self.respingos:                                 # "coroinha" de respingo
            abre = 2 if t < 0.09 else 1
            self.surf.set_at((int(x) - abre, int(y) - 1), claro)
            self.surf.set_at((int(x) + abre, int(y) - 1), claro)
            if t > 0.12:
                self.surf.set_at((int(x), int(y) - 2), claro)
```

Respingos: dois pontos abrindo para os lados e um ponto em cima no começo, como uma pequena coroa.

### Linhas 392 a 393

```python
        for x, y, _, fase in self.flocos:
            self.surf.set_at((int(x) % self.W, int(y)), (245, 248, 255))
```

Flocos de neve como pontos brancos.

### Linha 395

```python
    def _raio(self, raio, cor_brilho, cor_nucleo):
```

Desenha um raio.

### Linhas 396 a 399

```python
        if len(raio["pontos"]) > 1:
            deslocado = [(x + 1, y) for x, y in raio["pontos"]]
            pygame.draw.lines(self.surf, cor_brilho, False, deslocado, 1)
            pygame.draw.lines(self.surf, cor_nucleo, False, raio["pontos"], 1)
```

Desenha a linha do raio duas vezes: uma azulada deslocada 1 pixel (brilho) e uma quase branca (núcleo).

### Linhas 400 a 401

```python
        for g in raio["galhos"]:
            self._raio(g, cor_brilho, cor_nucleo)
```

Desenha os galhos (recursão).

### Linha 403

```python
    def draw(self, agora: datetime):
```

Desenha o cenário completo, na ordem de trás para a frente.

### Linha 404

```python
        paleta, luz, sol = fase_do_dia(agora, self.nascer, self.por)
```

Calcula a fase do dia.

### Linhas 405 a 407

```python
        self._ceu(paleta, luz)
        self._astros(luz, sol)
        self._nuvens(luz)
```

Céu, astros e nuvens.

### Linhas 408 a 409

```python
        if self.flash > 0.55 and self.raio:
            self._raio(self.raio, (150, 170, 255), (255, 255, 240))
```

Raio, se o clarão estiver forte.

### Linhas 410 a 411

```python
        self._cidade(luz)
        self._neblina(luz)
```

Cidade e neblina.

### Linhas 412 a 415

```python
        if self.escuro > 0.02:                    # escurece tudo conforme a chuva
            sombra = self._camada("escuro")
            sombra.fill((8, 10, 20, int(self.escuro * 110)))
            self.surf.blit(sombra, (0, 0))
```

Escurece tudo conforme o tempo (a regra da chuva).

### Linha 416

```python
        self._chuva()
```

Chuva por cima de tudo.

### Linhas 417 a 420

```python
        if self.flash > 0:
            clarao = self._camada("clarao")
            clarao.fill((215, 225, 255, int(self.flash * 140)))
            self.surf.blit(clarao, (0, 0))
```

Clarão do relâmpago na tela inteira.

### Linha 421

```python
        return self.surf
```

Devolve a superfície pronta.
