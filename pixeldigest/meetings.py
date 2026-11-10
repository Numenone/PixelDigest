"""Agendador de reuniões (Teams/Outlook).

Dois caminhos:
1. Alguém escreve no Teams "podemos marcar uma reunião?" -> eh_pedido() reconhece,
   o Agendador busca horários livres para os dois e sugere (na tela, no celular,
   no Discord e, se ligado, respondendo no próprio chat).
2. Você digita "reunião com Ana amanhã 45min sobre orçamento" -> interpretar()
   separa pessoa, dia, duração e assunto; o Agendador acha a pessoa e os horários.
"""
import re
import unicodedata
from datetime import date, datetime, time, timedelta

from . import net
from .models import Horario, PedidoReuniao

DIAS_SEMANA = {"segunda": 0, "terca": 1, "quarta": 2, "quinta": 3, "sexta": 4, "sabado": 5, "domingo": 6}
NOMES_DIA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
INTENCAO = re.compile(r"\b(podemos|podemo|vamos|bora|consegue|conseguimos|pode|poderia|tem (um )?tempo|"
                      r"marcar|agendar|disponivel|livre|horario)\b")


def normalizar(texto):
    """Minúsculas e sem acento, para comparar palavras: 'Reunião' -> 'reuniao'."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def eh_pedido(texto, palavras):
    """True se a mensagem parece um pedido de reunião.

    Precisa ter uma palavra de reunião (configurável no YAML) E uma intenção
    (pergunta ou verbo como 'marcar', 'podemos'). Assim 'a reunião foi ótima'
    não dispara, mas 'podemos fazer uma call?' dispara.
    """
    t = normalizar(texto)
    tem_palavra = any(re.search(rf"\b{re.escape(normalizar(p))}\b", t) for p in palavras)
    tem_intencao = "?" in texto or bool(INTENCAO.search(t))
    return tem_palavra and tem_intencao


def _plano(texto):
    """Tira acentos SEM mudar o tamanho do texto (cada letra continua no mesmo lugar).

    Assim dá para procurar 'amanha' no texto plano e cortar a mesma posição do original.
    """
    return "".join(unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode() or c for c in texto).lower()


def _cortar(texto, m):
    return texto[:m.start()] + " " + texto[m.end():]


def _dia_semana(hoje, numero):
    """Próxima ocorrência do dia da semana (se hoje é quinta, 'quinta' = semana que vem)."""
    return hoje + timedelta(days=(numero - hoje.weekday()) % 7 or 7)


def _data(hoje, m):
    dia = date(hoje.year, int(m.group(2)), int(m.group(1)))
    return dia if dia >= hoje else date(hoje.year + 1, dia.month, dia.day)


# (padrão no texto sem acento, como calcular o dia)
PADROES_DIA = [
    (r"\bdepois de amanha\b", lambda hoje, m: hoje + timedelta(days=2)),
    (r"\bamanha\b", lambda hoje, m: hoje + timedelta(days=1)),
    (r"\bhoje\b", lambda hoje, m: hoje),
    (r"\b(\d{1,2})/(\d{1,2})\b", _data),
    (r"\b(?:na |no |nesta |nessa |proxima |proximo )?(segunda|terca|quarta|quinta|sexta|sabado|domingo)(?:-feira| feira)?\b",
     lambda hoje, m: _dia_semana(hoje, DIAS_SEMANA[m.group(1)])),
]


def interpretar(comando, hoje, duracao_padrao=30):
    """'reunião com Ana amanhã 45min sobre orçamento' -> dict com os pedaços.

    Devolve None se não for um comando de reunião.
    """
    m = re.match(r"^\s*(?:marcar\s+|agendar\s+)?(?:uma\s+)?(?:reuniao|call|meet)\s+com\s+", _plano(comando))
    if not m:
        return None
    resto = comando[m.end():]

    # assunto: tudo depois de "sobre"
    assunto = ""
    s = re.search(r"\s+sobre\s+", _plano(resto))
    if s:
        resto, assunto = resto[:s.start()], resto[s.end():]

    # horário exato: "às 14h", "as 9:30", "às 15h30"
    hora = None
    h = re.search(r"\b(?:as|a partir das)\s+(\d{1,2})(?:[:h](\d{2}))?h?\b", _plano(resto))
    if h and int(h.group(1)) < 24:
        hora = time(int(h.group(1)), int(h.group(2) or 0))
        resto = _cortar(resto, h)

    # duração: "45min", "1h", "90 minutos"
    duracao = duracao_padrao
    d = re.search(r"\b(\d+)\s*(min|minutos?|m|h|horas?)\b", _plano(resto))
    if d:
        valor = int(d.group(1))
        duracao = valor * 60 if d.group(2).startswith("h") else valor
        resto = _cortar(resto, d)

    # dia: hoje, amanhã, depois de amanhã, 12/11, sexta-feira...
    dia = None
    for padrao, calcular in PADROES_DIA:
        achou = re.search(padrao, _plano(resto))
        if achou:
            dia = calcular(hoje, achou)
            resto = _cortar(resto, achou)
            break

    # O que sobrou é o nome da pessoa (tira preposições soltas no fim)
    pessoa = " ".join(resto.split())
    pessoa = re.sub(r"\s+(de|da|do|na|no|para|pra|as|às|em)$", "", pessoa, flags=re.I).strip(" ,.")
    if not pessoa:
        return None
    return {"pessoa": pessoa, "dia": dia, "hora": hora, "duracao": duracao,
            "assunto": assunto.strip() or f"Reunião com {pessoa}"}


def janelas(cfg, fuso, agora, dias=3, dia_especifico=None):
    """Janelas de expediente onde a reunião pode acontecer.

    Pula fim de semana e nunca sugere nada a menos de 30 minutos de agora.
    """
    ini_exp, fim_exp = cfg["horarios"]["expediente"]
    candidatos = [dia_especifico] if dia_especifico else [agora.date() + timedelta(days=i) for i in range(14)]
    resultado = []
    for dia in candidatos:
        if dia.weekday() >= 5 and not dia_especifico:
            continue
        ini = max(datetime.combine(dia, ini_exp, fuso), agora + timedelta(minutes=30))
        fim = datetime.combine(dia, fim_exp, fuso)
        # arredonda o início para o próximo múltiplo de 30 min
        if ini.minute % 30 or ini.second:
            ini = ini.replace(second=0, microsecond=0) + timedelta(minutes=30 - ini.minute % 30)
        if ini < fim:
            resultado.append((ini, fim))
        if len(resultado) == dias:
            break
    return resultado


def rotulo(h: Horario, hoje=None):
    """Horario -> 'qui 07/11 14:30'."""
    return f"{NOMES_DIA[h.inicio.weekday()]} {h.inicio:%d/%m %H:%M}"


class Agendador:
    def __init__(self, cfg, conector):
        self.cfg = cfg
        self.conector = conector      # MicrosoftConector (ou DemoConector)
        self.r = cfg["reunioes"]

    def _horarios(self, email, duracao, dia=None, hora=None):
        agora = self.conector.agora()
        if hora:
            # Pediu horário exato: testa só aquele horário; se alguém estiver ocupado,
            # cai para os horários livres do mesmo dia.
            inicio = datetime.combine(dia or agora.date(), hora, self.conector.fuso)
            try:
                return self.conector.horarios_livres(email, duracao, [(inicio, inicio + timedelta(minutes=duracao))], 1)
            except net.ApiError:
                dia = inicio.date()
        jan = janelas(self.cfg, self.conector.fuso, agora, self.r["dias_para_frente"], dia)
        if not jan:
            raise ValueError("esse dia já passou ou não tem horário de expediente")
        return self.conector.horarios_livres(email, duracao, jan)

    def de_comando(self, texto):
        """Comando digitado na tela -> proposta com 3 horários."""
        pedido = interpretar(texto, self.conector.agora().date(), self.r["duracao_padrao"])
        if not pedido:
            raise ValueError("não entendi. Exemplo: reunião com Ana amanhã 45min sobre orçamento")
        pessoas = self.conector.buscar_pessoa(pedido["pessoa"])
        if not pessoas:
            raise ValueError(f"não achei '{pedido['pessoa']}' nos seus contatos do Teams")
        nome, email = pessoas[0]
        horarios = self._horarios(email, pedido["duracao"], pedido["dia"], pedido["hora"])
        return {"pessoa": nome, "email": email, "assunto": pedido["assunto"],
                "duracao": pedido["duracao"], "horarios": horarios, "chat_id": None}

    def de_mensagem(self, msg):
        """Mensagem do Teams reconhecida como pedido -> PedidoReuniao com sugestões."""
        email = self.conector.email_de(msg["user_id"])
        horarios = self._horarios(email, self.r["duracao_padrao"])
        pedido = PedidoReuniao(self.conector.empresa, msg["chat_id"], msg["nome"], email, msg["texto"], horarios)
        if self.r["responder_no_teams"] and horarios:
            self.conector.responder(msg["chat_id"], self.texto_sugestao(msg["nome"], horarios))
        return pedido

    def texto_sugestao(self, nome, horarios):
        primeiro = nome.split()[0] if nome else ""
        opcoes = "".join(f"<li>{rotulo(h)}</li>" for h in horarios)
        return (f"<p>Oi {primeiro}! Olhei a nossa agenda e esses horários estão livres para nós dois:</p>"
                f"<ul>{opcoes}</ul><p>Qual fica melhor? (sugestão automática do PixelDigest)</p>")

    def confirmar(self, email, nome, horario, assunto):
        return self.conector.agendar(email, nome, horario, assunto)
