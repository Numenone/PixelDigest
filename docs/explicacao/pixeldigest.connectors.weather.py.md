# `pixeldigest/connectors/weather.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/connectors/weather.py)

Clima e tempo pelo Open-Meteo, uma API pública que não precisa de chave. O resultado controla o cenário da tela.

### Linhas 1 a 5

```python
"""Clima e tempo pelo Open-Meteo (API pública, sem chave).

1. Geocoding: nome da cidade -> latitude/longitude (uma vez só, guardado em cache).
2. Forecast: clima atual + previsão do dia, em JSON.
"""
```

Docstring: dois passos, geocoding (nome para coordenadas, guardado em cache) e forecast (clima atual e previsão).

### Linha 6

```python
from datetime import datetime
```

Importa `datetime`.

### Linhas 8 a 9

```python
from .. import net
from ..models import Clima
```

Importa `net` e a classe `Clima`.

### Linhas 11 a 12

```python
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
```

Endereços das duas APIs.

### Linhas 14 a 24

```python
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
```

Dicionário dos códigos WMO (padrão da Organização Meteorológica Mundial usado pelo Open-Meteo) para descrições em português.

### Linhas 26 a 28

```python
# Quanto cada tipo de tempo "pesa" na animação (0 = seco, 1 = tempestade)
PESO_CODIGO = {51: 0.2, 53: 0.3, 55: 0.4, 61: 0.45, 63: 0.6, 65: 0.8, 66: 0.5, 67: 0.8,
               80: 0.5, 81: 0.7, 82: 0.9, 95: 0.95, 96: 1.0, 99: 1.0}
```

Quanto cada tipo de tempo pesa na animação, de 0 (seco) a 1 (tempestade). Códigos que não estão aqui (céu limpo, nublado) pesam 0.

### Linha 30

```python
_geo_cache = {}
```

Cache das cidades já localizadas.

### Linha 33

```python
def intensidade(codigo, chuva_mm):
```

Calcula a intensidade da chuva de 0 a 1.

### Linhas 34 a 38

```python
    """Junta o código do tempo e os milímetros de chuva num número de 0 a 1.

    Usa o maior dos dois: assim uma 'chuva forte' sem medição ainda escurece a tela,
    e 10 mm medidos contam como tempestade mesmo se o código for só 'chuva'.
    """
```

Docstring: usa o maior entre o peso do código e os milímetros medidos, para que um código de chuva forte sem medição escureça a tela e 10 mm medidos contem como tempestade.

### Linha 39

```python
    pelo_codigo = PESO_CODIGO.get(codigo, 0.0)
```

Peso pelo código.

### Linha 40

```python
    pelos_mm = min(1.0, max(0.0, chuva_mm) / 10.0)
```

Peso pelos milímetros: 10 mm ou mais vira 1. `max(0.0, ...)` evita valores negativos e `min(1.0, ...)` limita em 1.

### Linha 41

```python
    return max(pelo_codigo, pelos_mm)
```

Devolve o maior.

### Linhas 44 a 45

```python
def descricao(codigo):
    return DESCRICOES.get(codigo, "tempo indefinido")
```

Descrição do código ou "tempo indefinido".

### Linha 48

```python
def localizar(cidade, client=None):
```

Localiza uma cidade pelo nome.

### Linha 49

```python
    """Cidade -> (lat, lon, nome oficial). Falha com ApiError se não achar."""
```

Docstring.

### Linhas 50 a 51

```python
    if cidade in _geo_cache:
        return _geo_cache[cidade]
```

Se já está no cache, devolve sem chamar a API.

### Linhas 52 a 53

```python
    dados = net.get_json("Open-Meteo", GEO_URL, client=client,
                         params={"name": cidade, "count": 1, "language": "pt", "format": "json"})
```

Chama o geocoding pedindo 1 resultado em português.

### Linhas 54 a 56

```python
    resultados = dados.get("results") or []
    if not resultados:
        raise net.ApiError("Open-Meteo", f"cidade '{cidade}' não encontrada")
```

Se não veio resultado, lança erro.

### Linhas 57 a 59

```python
    r = resultados[0]
    _geo_cache[cidade] = (r["latitude"], r["longitude"], r["name"])
    return _geo_cache[cidade]
```

Guarda latitude, longitude e nome oficial no cache e devolve.

### Linha 62

```python
_nomes = {}
```

Cache dos nomes de lugar.

### Linha 65

```python
def nome_do_lugar(lat, lon, client=None):
```

Converte coordenadas num nome curto (geocoding reverso).

### Linha 66

```python
    """Coordenadas -> 'Centro, Pelotas' (OpenStreetMap). Guardado em cache; sem internet devolve ''."""
```

Docstring.

### Linhas 67 a 68

```python
    if (lat, lon) in _nomes:
        return _nomes[(lat, lon)]
```

Se já está no cache, devolve.

### Linhas 69 a 72

```python
    try:
        d = net.get_json("OpenStreetMap", "https://nominatim.openstreetmap.org/reverse", client=client, retries=1,
                         headers={"User-Agent": "PixelDigest/1.0 (projeto academico de automacao)"},
                         params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 14, "accept-language": "pt-BR"})
```

Chama o Nominatim reverso (só 1 tentativa, porque é opcional) com o `User-Agent` obrigatório, nível de detalhe 14 (bairro) e nomes em português.

### Linha 73

```python
        _nomes[(lat, lon)] = lugar_curto(d.get("address", {}))
```

Guarda o nome curto.

### Linhas 74 a 75

```python
    except net.ApiError:
        return ""
```

Sem internet, devolve vazio (o programa usa outro nome).

### Linha 76

```python
    return _nomes[(lat, lon)]
```

Devolve.

### Linha 79

```python
def lugar_curto(endereco):
```

Monta "bairro, cidade" a partir do endereço do OpenStreetMap.

### Linha 80

```python
    """Do endereço completo do OpenStreetMap, pega só 'bairro, cidade'."""
```

Docstring.

### Linhas 81 a 82

```python
    # no Brasil o OpenStreetMap às vezes chama o distrito de "city" e o município de "municipality"
    cidade = next((endereco[k] for k in ("municipality", "city", "town", "village") if endereco.get(k)), "")
```

O comentário explica a particularidade brasileira. Procura a cidade na ordem de preferência das chaves; `next(..., "")` devolve a primeira encontrada ou vazio.

### Linha 83

```python
    bairro = next((endereco[k] for k in ("suburb", "neighbourhood", "city_district") if endereco.get(k)), "")
```

Mesma ideia para o bairro.

### Linha 84

```python
    return ", ".join(p for p in (bairro, cidade) if p)
```

Junta os dois que existirem com vírgula.

### Linha 87

```python
def buscar(local, fuso, client=None):
```

Busca o clima e monta o objeto `Clima`.

### Linhas 88 a 92

```python
    """Busca o clima e transforma o JSON do Open-Meteo num objeto Clima.

    local: {"local": "Av. Paulista, São Paulo", "lat": -23.56, "lon": -46.65}
    (lat/lon vêm da busca de endereço nas Configurações; sem elas, procura pelo nome).
    """
```

Docstring com o formato do parâmetro `local`.

### Linhas 93 a 94

```python
    if isinstance(local, str):
        local = {"local": local}
```

Aceita também um texto simples (formato antigo).

### Linhas 95 a 97

```python
    if local.get("lat") is not None and local.get("lon") is not None:
        lat, lon = local["lat"], local["lon"]
        nome = local.get("cidade") or nome_do_lugar(lat, lon, client) or (local.get("local") or "Local").split(",")[0]
```

Se há coordenadas, usa elas; o nome vem da cidade salva, do geocoding reverso ou da primeira parte do endereço.

### Linhas 98 a 99

```python
    else:
        lat, lon, nome = localizar(local.get("local") or "São Paulo", client)
```

Senão, localiza pelo nome (padrão São Paulo).

### Linhas 100 a 105

```python
    dados = net.get_json("Open-Meteo", FORECAST_URL, client=client, params={
        "latitude": lat, "longitude": lon, "timezone": fuso, "forecast_days": 2,
        "current": "temperature_2m,precipitation,cloud_cover,weather_code,wind_speed_10m",
        "hourly": "precipitation_probability,temperature_2m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,sunrise,sunset",
    })
```

Chama o forecast: coordenadas, fuso, 2 dias, e as variáveis pedidas no clima atual (temperatura, chuva, nuvens, código, vento), por hora (chance de chuva, temperatura, código) e por dia (máxima, mínima, nascer e pôr do sol).

### Linhas 106 a 107

```python
    atual = dados["current"]
    diario = dados["daily"]
```

Atalhos para as partes atual e diária.

### Linha 109

```python
    # Lista horária: acha a hora atual e pega a chance de chuva dela + as próximas 6 horas
```

Comentário: achar a hora atual na lista horária.

### Linha 110

```python
    horaria = dados["hourly"]
```

Atalho para a parte horária.

### Linha 111

```python
    hora_atual = atual["time"][:13]          # "2026-11-06T14"
```

Os 13 primeiros caracteres da hora atual, como "2026-11-06T14".

### Linha 112

```python
    horas = horaria["time"]
```

Lista das horas.

### Linha 113

```python
    i = next((k for k, t in enumerate(horas) if t.startswith(hora_atual)), 0)
```

Posição da hora atual na lista (ou 0 se não achar). `enumerate` dá posição e valor.

### Linha 114

```python
    prob = (horaria["precipitation_probability"][i] or 0) if horas else 0
```

Chance de chuva da hora atual (0 se vier `null` ou se a lista estiver vazia).

### Linha 115

```python
    proximas = []
```

Lista das próximas horas.

### Linhas 116 a 120

```python
    for k in range(i + 1, min(i + 7, len(horas))):
        proximas.append((horas[k][11:13] + "h",
                         (horaria.get("temperature_2m") or [None] * len(horas))[k],
                         (horaria.get("weather_code") or [0] * len(horas))[k] or 0,
                         horaria["precipitation_probability"][k] or 0))
```

Para as 6 horas seguintes: hora ("15h"), temperatura, código e chance de chuva. Os `or [None] * len(horas)` protegem caso a API não devolva alguma lista.

### Linha 122

```python
    codigo = int(atual.get("weather_code") or 0)
```

Código atual como inteiro.

### Linhas 123 a 137

```python
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
```

Monta o objeto `Clima` convertendo cada valor para o tipo certo (`float`, `int`) e tratando nulos com `or 0`. Nascer e pôr do sol são do primeiro dia (`[0]`).
