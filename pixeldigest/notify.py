"""Notificações: Discord (webhook) e celular (ntfy) AO MESMO TEMPO.

- Discord: POST de um "embed" (cartão colorido) no webhook do canal.
- Celular: POST no ntfy (app grátis no Android). Chega como notificação normal.

Resiliência: os dois envios rodam em paralelo; se um falhar (sem internet, 5xx),
a mensagem vai para data/pendentes.json e é reenviada depois.
"""
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from . import net
from .config import DATA, cor_rgb, env

log = logging.getLogger(__name__)
PENDENTES = DATA / "pendentes.json"


class Notificador:
    def __init__(self, cfg):
        n = cfg["notificacoes"]
        self.discord_url = env("DISCORD_WEBHOOK_URL", obrigatorio=False) if n["discord"] else ""
        self.ntfy_topico = env("NTFY_TOPIC", obrigatorio=False) if n["celular"] else ""
        self.ntfy_servidor = (env("NTFY_SERVER", obrigatorio=False) or "https://ntfy.sh").rstrip("/")
        self.ntfy_token = env("NTFY_TOKEN", obrigatorio=False)
        self.client = None              # os testes trocam por um cliente falso
        self._pool = ThreadPoolExecutor(max_workers=2)

    def ativo(self):
        return bool(self.discord_url or self.ntfy_topico)

    # ---------- montagem dos payloads (JSON) ----------
    def payload_discord(self, titulo, texto, cor, campos, url):
        embed = {
            "title": titulo[:256], "description": texto[:4000], "color": int("%02x%02x%02x" % cor_rgb(cor), 16),
            "fields": [{"name": nome[:256], "value": (valor or "-")[:1024], "inline": False} for nome, valor in (campos or [])][:25],
            "footer": {"text": "PixelDigest"}, "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if url:
            embed["url"] = url
        return {"username": "PixelDigest", "embeds": [embed]}

    def payload_ntfy(self, titulo, texto, campos, tags, prioridade, url):
        corpo = texto
        for nome, valor in campos or []:
            corpo += f"\n\n{nome}\n{valor}"
        p = {"topic": self.ntfy_topico, "title": titulo, "message": corpo[:3500],
             "tags": tags or [], "priority": prioridade}
        if url:
            p["click"] = url
        return p

    # ---------- envio ----------
    def _enviar(self, canal, payload):
        if canal == "discord":
            net.request("Discord", "POST", self.discord_url, json=payload, client=self.client)
        else:
            headers = {"Authorization": f"Bearer {self.ntfy_token}"} if self.ntfy_token else {}
            net.request("ntfy", "POST", self.ntfy_servidor, json=payload, headers=headers, client=self.client)

    def enviar(self, titulo, texto, cor="#5ab0ff", campos=None, tags=None, prioridade=3, url=""):
        """Manda para Discord e celular em paralelo. Devolve {canal: True/False}."""
        envios = {}
        if self.discord_url:
            envios["discord"] = self.payload_discord(titulo, texto, cor, campos, url)
        if self.ntfy_topico:
            envios["celular"] = self.payload_ntfy(titulo, texto, campos, tags, prioridade, url)
        futuros = {canal: self._pool.submit(self._enviar, "discord" if canal == "discord" else "ntfy", p)
                   for canal, p in envios.items()}
        resultado = {}
        for canal, futuro in futuros.items():
            try:
                futuro.result(timeout=40)
                resultado[canal] = True
            except Exception as exc:
                log.warning("notificação por %s falhou: %s (guardada para reenviar)", canal, exc)
                self._guardar(canal, envios[canal])
                resultado[canal] = False
        return resultado

    def _guardar(self, canal, payload):
        fila = self._ler_pendentes()
        fila.append({"canal": canal, "payload": payload})
        PENDENTES.write_text(json.dumps(fila[-100:], ensure_ascii=False), encoding="utf-8")

    def _ler_pendentes(self):
        try:
            return json.loads(PENDENTES.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []

    def reenviar_pendentes(self):
        """Tenta de novo o que falhou antes (roda a cada 5 minutos)."""
        fila = self._ler_pendentes()
        if not fila:
            return 0
        sobrou = []
        for item in fila:
            try:
                self._enviar("discord" if item["canal"] == "discord" else "ntfy", item["payload"])
            except Exception:
                sobrou.append(item)
        PENDENTES.write_text(json.dumps(sobrou, ensure_ascii=False), encoding="utf-8")
        return len(fila) - len(sobrou)
