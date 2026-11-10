"""Agendador simples de tarefas (os gatilhos de tempo do requisito 5).

- Diario: roda uma vez por dia num horário (07:00 resumo, 18:00 fim do expediente).
  Se o PC ligar atrasado (até 2 h depois), ainda roda. Lembra o último dia em
  data/agenda.json para não repetir se o programa reiniciar.
- Intervalo: roda a cada N segundos (clima, resumo, Teams, reenvio de notificações).
"""
import json
import logging
from datetime import datetime, timedelta

from .config import DATA

log = logging.getLogger(__name__)
ESTADO = DATA / "agenda.json"


def _ler_estado():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


class Diario:
    def __init__(self, nome, hora, funcao, tolerancia_h=2):
        self.nome, self.hora, self.funcao = nome, hora, funcao
        self.tolerancia = timedelta(hours=tolerancia_h)
        self.ultima = _ler_estado().get(nome)        # "2026-11-06"

    def na_hora(self, agora):
        alvo = datetime.combine(agora.date(), self.hora, agora.tzinfo)
        return alvo <= agora <= alvo + self.tolerancia and self.ultima != agora.date().isoformat()

    def marcar(self, agora):
        self.ultima = agora.date().isoformat()
        estado = _ler_estado()
        estado[self.nome] = self.ultima
        ESTADO.write_text(json.dumps(estado), encoding="utf-8")


class Intervalo:
    def __init__(self, nome, segundos, funcao, ja=False):
        self.nome, self.segundos, self.funcao = nome, segundos, funcao
        self.proxima = None if ja else datetime.now().astimezone() + timedelta(seconds=segundos)

    def na_hora(self, agora):
        return self.proxima is None or agora >= self.proxima

    def marcar(self, agora):
        self.proxima = agora + timedelta(seconds=self.segundos)


class Agenda:
    def __init__(self):
        self.tarefas = []

    def adicionar(self, tarefa):
        self.tarefas.append(tarefa)

    def tick(self, agora):
        """Roda o que estiver na hora. Um erro numa tarefa não para as outras."""
        for t in self.tarefas:
            if t.na_hora(agora):
                t.marcar(agora)
                try:
                    t.funcao()
                except Exception:
                    log.exception("tarefa '%s' falhou", t.nome)
