"""Clima e tempo pelo Open-Meteo (API pública, sem chave).

1. Geocoding: nome da cidade -> latitude/longitude (uma vez só, guardado em cache).
2. Forecast: clima atual + previsão do dia, em JSON.
"""
from datetime import datetime

from .. import net
from ..models import Clima

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Códigos WMO usados pelo Open-Meteo -> descrição em português
DESCRICOES = {
    0: "céu limpo", 1: "quase limpo", 2: "parcialmente nublado", 3: "nublado",
    45: "neblina", 48: "neblina com geada",
    51: "garoa fraca", 53: "garoa", 55: "garoa forte",
    61: "chuva fraca", 63: "chuva", 65: "chuva forte",
    66: "chuva congelante", 67: "chuva congelante forte",
    71: "neve fraca", 73: "neve", 75: "neve forte",
    80: "pancadas fracas", 81: "pancadas de chuva", 82: "pancadas fortes",
    95: "trovoada", 96: "trovoada com granizo", 99: "tempestade com granizo",
}

# Quanto cada tipo de tempo "pesa" na animação (0 = seco, 1 = tempestade)
PESO_CODIGO = {51: 0.2, 53: 0.3, 55: 0.4, 61: 0.45, 63: 0.6, 65: 0.8, 66: 0.5, 67: 0.8,
               80: 0.5, 81: 0.7, 82: 0.9, 95: 0.95, 96: 1.0, 99: 1.0}

_geo_cache = {}


def intensidade(codigo, chuva_mm):
    """Junta o código do tempo e os milímetros de chuva num número de 0 a 1.

    Usa o maior dos dois: assim uma 'chuva forte' sem medição ainda escurece a tela,
    e 10 mm medidos contam como tempestade mesmo se o código for só 'chuva'.
    """
    pelo_codigo = PESO_CODIGO.get(codigo, 0.0)
    pelos_mm = min(1.0, max(0.0, chuva_mm) / 10.0)
    return max(pelo_codigo, pelos_mm)


def descricao(codigo):
    return DESCRICOES.get(codigo, "tempo indefinido")


def localizar(cidade, client=None):
    """Cidade -> (lat, lon, nome oficial). Falha com ApiError se não achar."""
    if cidade in _geo_cache:
        return _geo_cache[cidade]
    dados = net.get_json("Open-Meteo", GEO_URL, client=client,
                         params={"name": cidade, "count": 1, "language": "pt", "format": "json"})
    resultados = dados.get("results") or []
    if not resultados:
        raise net.ApiError("Open-Meteo", f"cidade '{cidade}' não encontrada")
    r = resultados[0]
    _geo_cache[cidade] = (r["latitude"], r["longitude"], r["name"])
    return _geo_cache[cidade]


_nomes = {}


def nome_do_lugar(lat, lon, client=None):
    """Coordenadas -> 'Centro, Pelotas' (OpenStreetMap). Guardado em cache; sem internet devolve ''."""
    if (lat, lon) in _nomes:
        return _nomes[(lat, lon)]
    try:
        d = net.get_json("OpenStreetMap", "https://nominatim.openstreetmap.org/reverse", client=client, retries=1,
                         headers={"User-Agent": "PixelDigest/1.0 (projeto academico de automacao)"},
                         params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 14, "accept-language": "pt-BR"})
        _nomes[(lat, lon)] = lugar_curto(d.get("address", {}))
    except net.ApiError:
        return ""
    return _nomes[(lat, lon)]


def lugar_curto(endereco):
    """Do endereço completo do OpenStreetMap, pega só 'bairro, cidade'."""
    # no Brasil o OpenStreetMap às vezes chama o distrito de "city" e o município de "municipality"
    cidade = next((endereco[k] for k in ("municipality", "city", "town", "village") if endereco.get(k)), "")
    bairro = next((endereco[k] for k in ("suburb", "neighbourhood", "city_district") if endereco.get(k)), "")
    return ", ".join(p for p in (bairro, cidade) if p)


def buscar(local, fuso, client=None):
    """Busca o clima e transforma o JSON do Open-Meteo num objeto Clima.

    local: {"local": "Av. Paulista, São Paulo", "lat": -23.56, "lon": -46.65}
    (lat/lon vêm da busca de endereço nas Configurações; sem elas, procura pelo nome).
    """
    if isinstance(local, str):
        local = {"local": local}
    if local.get("lat") is not None and local.get("lon") is not None:
        lat, lon = local["lat"], local["lon"]
        nome = local.get("cidade") or nome_do_lugar(lat, lon, client) or (local.get("local") or "Local").split(",")[0]
    else:
        lat, lon, nome = localizar(local.get("local") or "São Paulo", client)
    dados = net.get_json("Open-Meteo", FORECAST_URL, client=client, params={
        "latitude": lat, "longitude": lon, "timezone": fuso, "forecast_days": 2,
        "current": "temperature_2m,precipitation,cloud_cover,weather_code,wind_speed_10m",
        "hourly": "precipitation_probability,temperature_2m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,sunrise,sunset",
    })
    atual = dados["current"]
    diario = dados["daily"]

    # Lista horária: acha a hora atual e pega a chance de chuva dela + as próximas 6 horas
    horaria = dados["hourly"]
    hora_atual = atual["time"][:13]          # "2026-11-06T14"
    horas = horaria["time"]
    i = next((k for k, t in enumerate(horas) if t.startswith(hora_atual)), 0)
    prob = (horaria["precipitation_probability"][i] or 0) if horas else 0
    proximas = []
    for k in range(i + 1, min(i + 7, len(horas))):
        proximas.append((horas[k][11:13] + "h",
                         (horaria.get("temperature_2m") or [None] * len(horas))[k],
                         (horaria.get("weather_code") or [0] * len(horas))[k] or 0,
                         horaria["precipitation_probability"][k] or 0))

    codigo = int(atual.get("weather_code") or 0)
    return Clima(
        cidade=nome,
        temperatura=float(atual["temperature_2m"]),
        minima=float(diario["temperature_2m_min"][0]),
        maxima=float(diario["temperature_2m_max"][0]),
        chuva_mm=float(atual.get("precipitation") or 0),
        prob_chuva=int(prob),
        nuvens=int(atual.get("cloud_cover") or 0),
        codigo=codigo,
        descricao=descricao(codigo),
        vento_kmh=float(atual.get("wind_speed_10m") or 0),
        nascer=datetime.fromisoformat(diario["sunrise"][0]),
        por_do_sol=datetime.fromisoformat(diario["sunset"][0]),
        proximas=proximas,
    )
