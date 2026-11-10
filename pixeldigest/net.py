"""Cliente HTTP resiliente usado por todos os conectores.

Requisito 6 (tratamento de erros): toda chamada de rede passa por aqui e ganha
- tempo limite (timeout), para nada ficar travado esperando para sempre;
- novas tentativas com espera crescente em falha de rede, 429 e erros 5xx;
- erro claro (ApiError) com o nome do serviço, em vez de quebrar em silêncio.
"""
import logging
import threading
import time

import httpx

log = logging.getLogger(__name__)

# Códigos que valem tentar de novo: excesso de requisições e falhas do servidor
RETRY_STATUS = {429, 500, 502, 503, 504}


_cliente = None
_trava = threading.Lock()


def cliente_compartilhado():
    """Um único httpx.Client para o programa todo (economiza RAM e é mais rápido).

    Criar um cliente por chamada recarregava os certificados HTTPS toda vez.
    O httpx.Client pode ser usado por várias threads ao mesmo tempo.
    """
    global _cliente
    with _trava:
        if _cliente is None:
            _cliente = httpx.Client(timeout=15, limits=httpx.Limits(max_connections=10, max_keepalive_connections=5))
        return _cliente


class ApiError(Exception):
    """Falha ao falar com um serviço externo (já com mensagem amigável)."""

    def __init__(self, service, message, status=None):
        super().__init__(f"{service}: {message}")
        self.service = service
        self.status = status


def request(service, method, url, *, retries=3, timeout=15, client=None, backoff=1.5, **kwargs):
    """Faz uma requisição HTTP e devolve a resposta (status 2xx/3xx).

    service: nome que aparece nos erros e no log (ex.: "Slack").
    client:  um httpx.Client já pronto (os testes passam um cliente falso aqui).
    kwargs:  repassados ao httpx (params, json, headers, data...).
    """
    client = client or cliente_compartilhado()
    kwargs.setdefault("timeout", timeout)
    last_error = None
    for attempt in range(1, retries + 1):
        wait = backoff ** attempt
        try:
            resp = client.request(method, url, **kwargs)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            last_error = ApiError(service, f"sem resposta da rede ({type(exc).__name__})")
        else:
            if resp.status_code in RETRY_STATUS:
                last_error = ApiError(service, f"HTTP {resp.status_code}", resp.status_code)
                # Se o servidor disser quanto esperar (Retry-After), respeitamos
                retry_after = resp.headers.get("Retry-After", "")
                if retry_after.isdigit():
                    wait = min(int(retry_after), 30)
            elif resp.status_code in (401, 403):
                raise ApiError(service, f"acesso negado (HTTP {resp.status_code}). Confira o token no .env", resp.status_code)
            elif resp.status_code >= 400:
                raise ApiError(service, f"HTTP {resp.status_code}: {resp.text[:200]}", resp.status_code)
            else:
                return resp
        log.warning("%s (tentativa %d de %d)", last_error, attempt, retries)
        if attempt < retries:
            time.sleep(wait)
    raise last_error


def get_json(service, url, **kwargs):
    """Atalho: GET que já devolve o JSON."""
    return request(service, "GET", url, **kwargs).json()


def post_json(service, url, payload, **kwargs):
    """Atalho: POST com corpo JSON que devolve o JSON da resposta (ou {} se vazio)."""
    resp = request(service, "POST", url, json=payload, **kwargs)
    return resp.json() if resp.content else {}
