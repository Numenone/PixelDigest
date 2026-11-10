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
import math
import random
from datetime import datetime

import pygame

W, H = 320, 180          # tamanho padrão (horizontal); a vertical usa 180x320

# (cor do topo do céu, cor do horizonte)
NOITE = ((8, 10, 30), (30, 32, 72))
AURORA = ((58, 64, 132), (246, 152, 112))
DIA = ((66, 146, 232), (170, 216, 250))
CREPUSCULO = ((64, 46, 112), (244, 118, 78))
NUBLADO_DIA = ((112, 120, 134), (156, 162, 174))
NUBLADO_NOITE = ((20, 22, 30), (38, 40, 50))
TEMPESTADE_DIA = ((62, 66, 78), (94, 98, 108))

PRESETS = {
    "sol": {"nuvens": 0.1, "chuva": 0.0, "trovoada": False, "vento": 8, "codigo": 0},
    "nublado": {"nuvens": 0.85, "chuva": 0.0, "trovoada": False, "vento": 14, "codigo": 3},
    "chuva": {"nuvens": 0.95, "chuva": 0.55, "trovoada": False, "vento": 18, "codigo": 63},
    "tempestade": {"nuvens": 1.0, "chuva": 1.0, "trovoada": True, "vento": 30, "codigo": 95},
}


def mix(a, b, t):
    """Mistura duas cores: t=0 -> a, t=1 -> b."""
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def mix_par(p1, p2, t):
    return mix(p1[0], p2[0], t), mix(p1[1], p2[1], t)


def minutos(dt):
    return dt.hour * 60 + dt.minute + dt.second / 60


def fase_do_dia(agora, nascer=None, por=None):
    """Devolve (paleta do céu, luz 0..1, posição do sol 0..1)."""
    m = minutos(agora)
    n = minutos(nascer) if nascer else 6 * 60
    p = minutos(por) if por else 18 * 60 + 30
    sol = (m - n) / max(1, (p - n))
    if m < n - 50 or m > p + 50:
        return NOITE, 0.0, sol
    if m < n:
        return mix_par(NOITE, AURORA, (m - (n - 50)) / 50), 0.3 * (m - (n - 50)) / 50, sol
    if m < n + 60:
        return mix_par(AURORA, DIA, (m - n) / 60), 0.3 + 0.7 * (m - n) / 60, sol
    if m < p - 60:
        return DIA, 1.0, sol
    if m < p:
        return mix_par(DIA, CREPUSCULO, (m - (p - 60)) / 60), 1.0 - 0.6 * (m - (p - 60)) / 60, sol
    return mix_par(CREPUSCULO, NOITE, (m - p) / 50), 0.4 - 0.4 * (m - p) / 50, sol


def limitar(v):
    return max(0.0, min(1.0, v))


class Cena:
    def __init__(self, largura=W, altura=H, semente=7):
        self.W, self.H = largura, altura
        self.CHAO = altura - 22
        self.rng = random.Random(semente)
        self.surf = pygame.Surface((largura, altura))
        self.vis = dict(PRESETS["sol"])        # clima mostrado agora (vai suavizando)
        self.alvo = dict(PRESETS["sol"])       # clima de destino
        self.nascer = None
        self.por = None
        self.tempo = 0.0
        self.gotas, self.respingos, self.flocos = [], [], []
        self.flash = 0.0
        self.raio = None
        self.luz_janelas = 0.0
        self.janelas_forcadas = 0.0           # animação das 18h acende tudo
        self._sprites = {}                    # nuvens já desenhadas (por forma, tamanho e cor)
        self._camadas = {}                    # superfícies transparentes reaproveitadas
        self._gerar_cidade()
        self._gerar_ceu()

    # ---------- geração (uma vez só, com semente fixa) ----------
    def _gerar_cidade(self):
        r = self.rng
        self.predios = []
        x = -4
        alto = int(self.H * 0.52)
        while x < self.W:
            w = r.randint(16, 38)
            h = r.randint(28, max(40, alto))
            cor = mix((34, 38, 58), (58, 60, 84), r.random())
            janelas = []
            for jy in range(self.CHAO - h + 6, self.CHAO - 6, 7):
                for jx in range(x + 4, x + w - 4, 6):
                    janelas.append((jx, jy, r.random()))       # 3º valor: quando essa janela acende
            antena = r.random() < 0.3
            self.predios.append((x, w, h, cor, janelas, antena))
            x += w + r.randint(0, 3)

    def _gerar_ceu(self):
        r = self.rng
        topo_cidade = self.CHAO - int(self.H * 0.52)
        self.estrelas = [(r.randint(0, self.W - 1), r.randint(0, max(20, topo_cidade)), r.random() * 6.28) for _ in range(70)]
        self.nuvens = []
        for i in range(24):
            forma = [(r.randint(-14, 14), r.randint(-5, 2), r.randint(5, 10)) for _ in range(r.randint(4, 7))]
            self.nuvens.append({"x": r.uniform(-30, self.W + 30), "y": r.uniform(10, max(30, topo_cidade * 0.8)),
                                "forma": forma, "vel": r.uniform(0.4, 1.0), "ordem": r.random(), "id": i})
        self.nuvens.sort(key=lambda n: n["ordem"])
        self.teto = [[(r.randint(-12, 12), r.randint(-3, 3), r.randint(9, 14)) for _ in range(5)] for _ in range(6)]

    # ---------- clima ----------
    def definir_clima(self, clima=None, preset=None):
        """Recebe o Clima real (Open-Meteo) ou um preset da demonstração."""
        if preset:
            self.alvo = dict(PRESETS[preset])
        elif clima:
            self.alvo = {"nuvens": clima.nuvens / 100, "chuva": clima.intensidade_chuva,
                         "trovoada": clima.trovoada, "vento": clima.vento_kmh, "codigo": clima.codigo}
            self.nascer, self.por = clima.nascer, clima.por_do_sol

    @property
    def escuro(self):
        """0 = céu normal, 1 = bem escuro. Nuvens escurecem um pouco; chuva escurece muito."""
        return min(1.0, 0.18 * self.vis["nuvens"] + 0.62 * self.vis["chuva"])

    @property
    def cobertura(self):
        """0 = céu aberto, 1 = céu totalmente fechado (cinza). Chuva fecha o céu rápido."""
        return limitar(max((self.vis["nuvens"] - 0.45) / 0.5, self.vis["chuva"] * 2.5))

    def acender_janelas(self):
        self.janelas_forcadas = 1.0

    def _camada(self, nome):
        """Superfície transparente do tamanho da cena, criada uma vez só."""
        if nome not in self._camadas:
            self._camadas[nome] = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        return self._camadas[nome]

    # ---------- animação ----------
    def update(self, dt, agora):
        self.tempo += dt
        k = min(1.0, dt * 0.8)                       # transição de clima em ~3 segundos
        for chave in ("nuvens", "chuva", "vento"):
            self.vis[chave] += (self.alvo[chave] - self.vis[chave]) * k
        self.vis["trovoada"] = self.alvo["trovoada"]
        self.vis["codigo"] = self.alvo.get("codigo", 0)

        _, luz, _ = fase_do_dia(agora, self.nascer, self.por)
        alvo_janelas = 0.08 + 0.6 * (1 - luz) + 0.25 * self.escuro
        alvo_janelas = max(alvo_janelas, self.janelas_forcadas * 0.9)
        self.luz_janelas += (alvo_janelas - self.luz_janelas) * min(1.0, dt * 0.7)
        self.janelas_forcadas = max(0.0, self.janelas_forcadas - dt * 0.02)

        vento = self.vis["vento"]
        for n in self.nuvens:
            n["x"] += (2 + vento * 0.25) * n["vel"] * dt
            if n["x"] > self.W + 45:
                n["x"] = -45

        # chuva: nasce em cima, cai inclinada com o vento, vira respingo no chão
        chuva, W, CHAO = self.vis["chuva"], self.W, self.CHAO
        nascem = chuva * 3.2 * W * dt
        while nascem > 0 and len(self.gotas) < 1100:
            if nascem < 1 and self.rng.random() > nascem:
                break
            perto = self.rng.random() < 0.35                       # gotas "perto" são maiores e mais claras
            self.gotas.append([self.rng.uniform(-40, W + 10), self.rng.uniform(-24, 0),
                               self.rng.uniform(230, 290) if perto else self.rng.uniform(170, 210),
                               CHAO + self.rng.uniform(-2, 20), perto])
            nascem -= 1
        vx = vento * 1.3
        vivas = []
        for g in self.gotas:
            g[0] += vx * dt
            g[1] += g[2] * dt
            if g[1] >= g[3]:
                self.respingos.append([g[0], g[3], 0.18])
            else:
                vivas.append(g)
        self.gotas = vivas
        self.respingos = [[x, y, t - dt] for x, y, t in self.respingos if t - dt > 0]

        # neve (códigos 71 a 77, 85, 86)
        codigo = self.vis["codigo"]
        if 71 <= codigo <= 77 or codigo in (85, 86):
            while len(self.flocos) < 160:
                self.flocos.append([self.rng.uniform(0, W), self.rng.uniform(-self.H, 0), self.rng.uniform(14, 30), self.rng.random() * 6])
        for f in self.flocos:
            f[1] += f[2] * dt
            f[0] += math.sin(self.tempo * 1.5 + f[3]) * 0.3 + vento * 0.02
            if f[1] > CHAO + 10:
                f[1], f[0] = self.rng.uniform(-20, 0), self.rng.uniform(0, W)
        if not (71 <= codigo <= 77 or codigo in (85, 86)):
            self.flocos = []

        # relâmpago com galhos
        self.flash = max(0.0, self.flash - dt * 3.2)
        if self.vis["trovoada"] and self.rng.random() < dt * 0.25:
            self.flash = 1.0
            self.raio = self._gerar_raio(self.rng.randint(30, W - 30), 0, CHAO - 30, 0)

    def _gerar_raio(self, x, y, fim, nivel):
        pontos, galhos = [(x, y)], []
        while y < fim:
            y += self.rng.randint(5, 11)
            x += self.rng.randint(-7, 7)
            pontos.append((x, y))
            if nivel < 1 and self.rng.random() < 0.25:
                galhos.append(self._gerar_raio(x, y, y + self.rng.randint(12, 30), nivel + 1))
        return {"pontos": pontos, "galhos": galhos}

    # ---------- desenho ----------
    def _ceu(self, paleta, luz):
        nublado = mix_par(NUBLADO_NOITE, NUBLADO_DIA, luz)
        topo, horizonte = mix_par(paleta, nublado, self.cobertura * 0.95)
        tempestade = mix_par(NUBLADO_NOITE, TEMPESTADE_DIA, luz)
        topo, horizonte = mix_par((topo, horizonte), tempestade, self.vis["chuva"] * 0.7)
        for y in range(self.CHAO):
            pygame.draw.line(self.surf, mix(topo, horizonte, y / self.CHAO), (0, y), (self.W, y))

    def _astros(self, luz, sol):
        visivel = limitar(1 - self.cobertura * 1.4)           # some atrás das nuvens
        W, CHAO = self.W, self.CHAO
        altura_arco = CHAO * 0.75
        if luz < 0.35 and visivel > 0:
            for x, y, fase in self.estrelas:
                brilho = (0.5 + 0.5 * math.sin(self.tempo * 2 + fase)) * (1 - luz / 0.35) * visivel
                if brilho > 0.35:
                    self.surf.set_at((x, y), mix((60, 60, 90), (255, 255, 230), brilho))
        camada = self._camada("astros")
        camada.fill((0, 0, 0, 0))
        if 0 <= sol <= 1:
            x = int(18 + sol * (W - 36))
            y = int(CHAO - 14 - math.sin(math.pi * sol) * altura_arco)
            if visivel > 0:
                a = int(255 * visivel)
                for i in range(8):                               # raios em cruz e diagonal (pixel art)
                    ang = i * math.pi / 4 + self.tempo * 0.1
                    x2, y2 = x + math.cos(ang) * 15, y + math.sin(ang) * 15
                    pygame.draw.line(camada, (255, 214, 90, a // 2), (x, y), (int(x2), int(y2)))
                pygame.draw.circle(camada, (255, 196, 70, a), (x, y), 10)
                pygame.draw.circle(camada, (255, 232, 120, a), (x, y), 8)
                pygame.draw.circle(camada, (255, 250, 200, a), (x - 2, y - 2), 3)
        else:
            noite = (sol - 1) if sol > 1 else (sol + 1)
            noite = limitar(noite)
            x = int(18 + noite * (W - 36))
            y = int(CHAO - 20 - math.sin(math.pi * noite) * altura_arco * 0.9)
            if visivel > 0:
                a = int(255 * visivel)
                pygame.draw.circle(camada, (236, 236, 214, a), (x, y), 7)
                pygame.draw.circle(camada, (200, 200, 184, a), (x - 2, y - 1), 2)
                pygame.draw.circle(camada, (210, 210, 190, a), (x + 2, y + 3), 1)
        self.surf.blit(camada, (0, 0))

    def _cores_nuvem(self, luz):
        """Três tons da nuvem (luz, corpo, sombra), conforme hora e chuva."""
        clara = mix((96, 100, 124), (250, 250, 255), luz)
        corpo = mix(clara, mix((60, 64, 76), (132, 138, 150), luz), max(self.cobertura * 0.6, self.vis["chuva"]))
        return mix(corpo, (255, 255, 255), 0.25), corpo, mix(corpo, (20, 22, 32), 0.32)

    def _sprite_nuvem(self, forma, escala, tons, chave):
        """Nuvem em pixel art: luz em cima, sombra embaixo e base reta (guardada em cache)."""
        chave = (chave, round(escala, 1), tons)
        if chave in self._sprites:
            return self._sprites[chave]
        luz, corpo, sombra = tons
        circulos = [(dx * escala, dy * escala, max(2, r * escala)) for dx, dy, r in forma]
        x0 = min(dx - r for dx, dy, r in circulos) - 2
        x1 = max(dx + r for dx, dy, r in circulos) + 2
        y0 = min(dy - r for dx, dy, r in circulos) - 2
        base = max(dy for dx, dy, r in circulos) + 3 * escala          # linha da base reta
        w, h = int(x1 - x0) + 1, int(base - y0) + 4
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        for camada, cor, dy_extra, encolhe in ((0, sombra, 3, 0), (1, luz, -1, 0), (2, corpo, 1, 1)):
            for dx, dy, r in circulos:
                pygame.draw.circle(s, cor, (int(dx - x0), int(dy - y0 + dy_extra)), int(r - encolhe))
        corte = int(base - y0)
        s.fill((0, 0, 0, 0), (0, corte, w, h - corte))                  # corta embaixo = base reta
        for x in range(w):                                              # faixa de sombra na base
            if s.get_at((x, corte - 3)).a:
                s.fill(sombra, (x, corte - 2, 1, 2))
        if len(self._sprites) > 260:
            self._sprites.clear()
        self._sprites[chave] = s
        return s

    def _nuvens(self, luz):
        nuvens, chuva, cob = self.vis["nuvens"], self.vis["chuva"], self.cobertura
        tons = tuple(tuple(c // 6 * 6 for c in cor) for cor in self._cores_nuvem(luz))   # tons arredondados = menos sprites
        # teto de nuvens: começa a fechar o céu com a cobertura e desce com a chuva
        if cob > 0.25:
            borda = int(-28 + cob * 26 + chuva * self.H * 0.18)
            luz_t, corpo_t, sombra_t = tons
            escuro_t = (mix(luz_t, sombra_t, 0.5), sombra_t, mix(sombra_t, (10, 12, 18), 0.3))
            if borda > 0:
                self.surf.fill(sombra_t, (0, 0, self.W, borda))
            for i, x in enumerate(range(-20, self.W + 40, 34)):
                deriva = (self.tempo * (3 + self.vis["vento"] * 0.15)) % 34
                sp = self._sprite_nuvem(self.teto[i % len(self.teto)], 1.6, escuro_t, f"teto{i % len(self.teto)}")
                self.surf.blit(sp, (int(x + deriva - sp.get_width() / 2), borda - sp.get_height() + 8))
        quantas = int(2 + nuvens * 22)
        escala = 1 + chuva * 0.6
        for n in self.nuvens[:quantas]:
            y = n["y"] * (1 - 0.5 * chuva) + chuva * 12
            sp = self._sprite_nuvem(n["forma"], escala, tons, n["id"])
            self.surf.blit(sp, (int(n["x"] - sp.get_width() / 2), int(y - sp.get_height() / 2)))

    def _neblina(self, luz):
        if self.vis["codigo"] not in (45, 48):
            return
        camada = self._camada("neblina")
        camada.fill((0, 0, 0, 0))
        cor = mix((60, 64, 74), (210, 214, 220), luz)
        for i in range(6):
            y = self.CHAO - 12 - i * 16
            x = int((self.tempo * (4 + i)) % (self.W + 80)) - 80
            for k in range(-1, self.W // 120 + 2):
                pygame.draw.ellipse(camada, (*cor, 70), (x + k * 140, y, 120, 10))
        self.surf.blit(camada, (0, 0))

    def _cidade(self, luz):
        noite = 1 - luz
        CHAO = self.CHAO
        clarao = self.flash > 0.5
        for x, w, h, cor, janelas, antena in self.predios:
            c = mix(mix(cor, (92, 100, 134), luz * 0.45), (14, 16, 26), noite * 0.6 + self.escuro * 0.3)
            if clarao:
                c = mix(c, (200, 210, 240), 0.35)
            pygame.draw.rect(self.surf, c, (x, CHAO - h, w, h))
            pygame.draw.line(self.surf, mix(c, (255, 255, 255), 0.12), (x, CHAO - h), (x + w - 1, CHAO - h))
            pygame.draw.line(self.surf, mix(c, (0, 0, 0), 0.25), (x + w - 1, CHAO - h), (x + w - 1, CHAO))   # lado na sombra
            if antena:
                pygame.draw.line(self.surf, c, (x + w // 2, CHAO - h), (x + w // 2, CHAO - h - 7))
                if int(self.tempo * 1.5) % 2:
                    self.surf.set_at((x + w // 2, CHAO - h - 8), (255, 70, 70))
            for jx, jy, quando in janelas:
                if quando < self.luz_janelas:
                    cor_j = (255, 214, 120) if quando % 0.1 > 0.02 else (190, 230, 255)
                else:
                    cor_j = mix((120, 160, 210), (30, 34, 50), max(noite, self.cobertura * 0.6))
                self.surf.fill(cor_j, (jx, jy, 2, 3))
        # rua
        rua = mix((54, 54, 64), (24, 24, 32), noite)
        molhada = self.vis["chuva"] > 0.12
        if molhada:
            rua = mix(rua, (30, 34, 48), 0.4)
        pygame.draw.rect(self.surf, rua, (0, CHAO, self.W, self.H - CHAO))
        pygame.draw.line(self.surf, mix((90, 90, 100), (40, 40, 50), noite), (0, CHAO), (self.W, CHAO))
        for x in range(0, self.W, 24):
            self.surf.fill(mix((200, 190, 120), (90, 86, 60), noite), (x, CHAO + 11, 10, 1))
        if molhada:   # reflexo das janelas acesas no asfalto molhado
            for x, w, h, cor, janelas, antena in self.predios:
                acesas = sum(1 for _, _, q in janelas if q < self.luz_janelas)
                if acesas:
                    brilho = mix(rua, (255, 214, 120), min(0.5, acesas / 40))
                    for k in range(x + 3, x + w - 3, 6):
                        self.surf.fill(brilho, (k, CHAO + 3 + (k % 3), 2, 4 + (k % 4)))

    def _chuva(self):
        claro, escuro = (178, 196, 236), (118, 136, 186)
        vx = self.vis["vento"] * 1.3
        for x, y, vy, _, perto in self.gotas:
            comprimento = 6 if perto else 3
            inclina = vx * comprimento / max(vy, 1)
            pygame.draw.line(self.surf, claro if perto else escuro, (int(x), int(y)), (int(x - inclina), int(y - comprimento)))
        for x, y, t in self.respingos:                                 # "coroinha" de respingo
            abre = 2 if t < 0.09 else 1
            self.surf.set_at((int(x) - abre, int(y) - 1), claro)
            self.surf.set_at((int(x) + abre, int(y) - 1), claro)
            if t > 0.12:
                self.surf.set_at((int(x), int(y) - 2), claro)
        for x, y, _, fase in self.flocos:
            self.surf.set_at((int(x) % self.W, int(y)), (245, 248, 255))

    def _raio(self, raio, cor_brilho, cor_nucleo):
        if len(raio["pontos"]) > 1:
            deslocado = [(x + 1, y) for x, y in raio["pontos"]]
            pygame.draw.lines(self.surf, cor_brilho, False, deslocado, 1)
            pygame.draw.lines(self.surf, cor_nucleo, False, raio["pontos"], 1)
        for g in raio["galhos"]:
            self._raio(g, cor_brilho, cor_nucleo)

    def draw(self, agora: datetime):
        paleta, luz, sol = fase_do_dia(agora, self.nascer, self.por)
        self._ceu(paleta, luz)
        self._astros(luz, sol)
        self._nuvens(luz)
        if self.flash > 0.55 and self.raio:
            self._raio(self.raio, (150, 170, 255), (255, 255, 240))
        self._cidade(luz)
        self._neblina(luz)
        if self.escuro > 0.02:                    # escurece tudo conforme a chuva
            sombra = self._camada("escuro")
            sombra.fill((8, 10, 20, int(self.escuro * 110)))
            self.surf.blit(sombra, (0, 0))
        self._chuva()
        if self.flash > 0:
            clarao = self._camada("clarao")
            clarao.fill((215, 225, 255, int(self.flash * 140)))
            self.surf.blit(clarao, (0, 0))
        return self.surf
