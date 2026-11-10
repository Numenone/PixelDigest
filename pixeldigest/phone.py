"""Ouve o alarme do celular.

Como funciona: no Android, o app MacroDroid detecta o alarme tocando e faz um
POST no ntfy (ex.: https://ntfy.sh/<NTFY_TOPIC_ALARME>). Este módulo fica
conectado nesse tópico recebendo os eventos em tempo real (streaming JSON,
uma linha por mensagem). Não precisa abrir porta no roteador.

Se a conexão cair, reconecta sozinho com espera crescente (5 s, 10 s ... até 60 s).
"""
import json
import logging
import threading
import time

import httpx

from .config import env

log = logging.getLogger(__name__)


class OuvinteAlarme(threading.Thread):
    def __init__(self, ao_receber):
        super().__init__(daemon=True, name="alarme")
        self.ao_receber = ao_receber      # função chamada com (titulo, mensagem)
        self.topico = env("NTFY_TOPIC_ALARME", obrigatorio=False)
        self.servidor = (env("NTFY_SERVER", obrigatorio=False) or "https://ntfy.sh").rstrip("/")
        self.token = env("NTFY_TOKEN", obrigatorio=False)
        self.parar = threading.Event()
        self.conectado = False         # a bolinha "Alarme" no topo fica verde só quando True
        self.ultima = None             # (hora, mensagem) do último alarme recebido

    def configurado(self):
        return bool(self.topico)

    def run(self):
        espera = 5
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        url = f"{self.servidor}/{self.topico}/json"
        while not self.parar.is_set():
            try:
                # A conexão fica aberta; o ntfy manda um "keepalive" a cada ~45 s.
                # Se ficar 2 min sem nada, consideramos caída e reconectamos.
                with httpx.stream("GET", url, headers=headers, timeout=httpx.Timeout(10, read=120)) as resp:
                    resp.raise_for_status()
                    self.conectado = True
                    espera = 5
                    for linha in resp.iter_lines():
                        if self.parar.is_set():
                            return
                        if not linha.strip():
                            continue
                        evento = json.loads(linha)
                        if evento.get("event") == "message":
                            self.ultima = (time.strftime("%H:%M"), evento.get("message") or "")
                            self.ao_receber(evento.get("title") or "Alarme", evento.get("message") or "")
            except (httpx.HTTPError, ValueError) as exc:
                self.conectado = False
                log.warning("ouvinte do alarme desconectado (%s); tentando em %ss", exc, espera)
                self.parar.wait(espera)
                espera = min(espera * 2, 60)
