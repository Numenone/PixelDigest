"""Formatos de dados que circulam no programa.

Todo conector (Slack, ClickUp, Gmail, Outlook, Teams...) converte o JSON da sua API
para estes mesmos formatos. Assim o resto do programa não precisa saber de onde
cada coisa veio.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime

# Prioridades usadas para ordenar o resumo
BAIXA, NORMAL, ALTA, URGENTE = 0, 1, 2, 3


@dataclass
class Item:
    """Uma coisa que merece atenção: tarefa, mensagem, e-mail ou evento da agenda."""
    empresa: str
    fonte: str            # slack, clickup, gmail, google_agenda, outlook, teams, agenda
    tipo: str             # tarefa, mensagem, email, evento
    titulo: str
    detalhe: str = ""
    quando: datetime | None = None
    url: str = ""
    prioridade: int = NORMAL
    id: str = ""          # identificador na origem (usado para não avisar duas vezes)

    def chave(self):
        return f"{self.fonte}:{self.id or self.titulo}"

    def to_dict(self):
        d = asdict(self)
        d["quando"] = self.quando.isoformat() if self.quando else None
        return d


@dataclass
class Clima:
    """Clima atual e do dia (vem do Open-Meteo)."""
    cidade: str
    temperatura: float
    minima: float
    maxima: float
    chuva_mm: float           # chuva na última hora
    prob_chuva: int           # % de chance de chuva na próxima hora
    nuvens: int               # % do céu coberto
    codigo: int               # código WMO do tempo
    descricao: str
    vento_kmh: float
    nascer: datetime | None = None
    por_do_sol: datetime | None = None
    proximas: list = field(default_factory=list)   # próximas horas: [(hora, temp, código, % chuva)]

    @property
    def intensidade_chuva(self):
        """0 = seco, 1 = tempestade. Controla a quantidade de gotas e o escuro da tela."""
        from .connectors.weather import intensidade
        return intensidade(self.codigo, self.chuva_mm)

    @property
    def trovoada(self):
        return self.codigo >= 95

    def to_dict(self):
        d = asdict(self)
        d["nascer"] = self.nascer.isoformat() if self.nascer else None
        d["por_do_sol"] = self.por_do_sol.isoformat() if self.por_do_sol else None
        d["intensidade_chuva"] = round(self.intensidade_chuva, 2)
        return d


@dataclass
class Horario:
    """Um horário livre sugerido para reunião."""
    inicio: datetime
    fim: datetime
    confianca: float = 100.0


@dataclass
class PedidoReuniao:
    """Alguém pediu reunião no Teams."""
    empresa: str
    chat_id: str
    pessoa: str
    email: str
    texto: str
    horarios: list = field(default_factory=list)


@dataclass
class Digest:
    """O resumo do dia inteiro: itens de todas as empresas + clima + falhas."""
    gerado_em: datetime
    itens: list
    clima: Clima | None = None
    erros: list = field(default_factory=list)   # fontes que falharam (o resumo sai mesmo assim)

    def por_empresa(self):
        grupos = {}
        for it in self.itens:
            grupos.setdefault(it.empresa, []).append(it)
        return grupos

    def to_dict(self):
        return {
            "gerado_em": self.gerado_em.isoformat(),
            "clima": self.clima.to_dict() if self.clima else None,
            "erros": self.erros,
            "itens": [i.to_dict() for i in self.itens],
        }
