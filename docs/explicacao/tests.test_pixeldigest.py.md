# `tests/test_pixeldigest.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../tests/test_pixeldigest.py)

Testes automáticos com o pytest. Nenhum teste usa a internet: as APIs são simuladas com `httpx.MockTransport`, que responde como se fosse o servidor. Assim os testes rodam em segundos, em qualquer computador e sem contas reais.

### Linhas 1 a 4

```python
"""Testes sem internet: as APIs são simuladas com httpx.MockTransport.

Rodar: .venv\\Scripts\\python -m pytest -q
"""
```

Docstring: explica a simulação e como rodar.

### Linha 5

```python
import json
```

Importa `json`.

### Linha 6

```python
from datetime import date, datetime, time, timedelta
```

Importa os tipos de data e hora.

### Linha 7

```python
from zoneinfo import ZoneInfo
```

Importa `ZoneInfo`.

### Linha 9

```python
import httpx
```

Importa o `httpx` (para criar o cliente falso e as respostas).

### Linha 10

```python
import pytest
```

Importa o `pytest`.

### Linhas 12 a 19

```python
from pixeldigest import config, digest, net
from pixeldigest.connectors import weather
from pixeldigest.connectors.clickup import ClickUpConector
from pixeldigest.connectors.microsoft import MicrosoftConector, espalhar, texto_puro
from pixeldigest.connectors.slack import SlackConector
from pixeldigest.meetings import eh_pedido, interpretar, janelas
from pixeldigest.models import ALTA, NORMAL, URGENTE, Horario, Item
from pixeldigest.notify import Notificador
```

Importa as partes do projeto que serão testadas.

### Linha 21

```python
FUSO = ZoneInfo("America/Sao_Paulo")
```

Fuso usado nos testes.

### Linhas 24 a 26

```python
@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    monkeypatch.setattr(net.time, "sleep", lambda s: None)
```

Fixture automática (`autouse=True`, vale para todos os testes): troca o `time.sleep` do módulo de rede por uma função que não espera. Assim os testes de nova tentativa não ficam parados segundos. `monkeypatch` desfaz a troca no fim de cada teste.

### Linhas 29 a 33

```python
@pytest.fixture(autouse=True)
def sem_arquivos_reais(monkeypatch, tmp_path):
    """Os testes nunca leem nem gravam o config.yaml/.env de verdade do usuário."""
    monkeypatch.setattr(config, "ARQ_CONFIG", tmp_path / "config-teste.yaml")
    monkeypatch.setattr(config, "ARQ_ENV", tmp_path / "env-teste")
```

Outra fixture automática: aponta o `config.yaml` e o `.env` para uma pasta temporária (`tmp_path`). Os testes nunca tocam nos arquivos reais do usuário.

### Linhas 36 a 45

```python
@pytest.fixture
def cfg(monkeypatch, tmp_path):
    monkeypatch.setenv("T_SLACK", "xoxb-teste")
    monkeypatch.setenv("T_SLACK_ID", "UEU")
    monkeypatch.setenv("T_CLICKUP", "pk_teste")
    monkeypatch.setenv("T_TEAM", "999")
    monkeypatch.setenv("T_MS", "client-id")
    arq = tmp_path / "config.yaml"
    arq.write_text("usuario: {nome: Teste}\nempresas: []\n", encoding="utf-8")
    return config.carregar(arq)
```

Fixture `cfg`: cria variáveis de ambiente falsas (tokens de teste), escreve um config mínimo numa pasta temporária e devolve a configuração carregada. Os testes que recebem um parâmetro chamado `cfg` ganham esse objeto.

### Linha 48

```python
def cliente(rotas):
```

Cria um cliente HTTP falso.

### Linha 49

```python
    """Cliente HTTP falso: rotas = {trecho_da_url: função(request) -> httpx.Response}."""
```

Docstring: as rotas ligam um pedaço da URL a uma resposta.

### Linhas 50 a 54

```python
    def handler(req):
        for trecho, resp in rotas.items():
            if trecho in str(req.url):
                return resp(req) if callable(resp) else resp
        return httpx.Response(404, json={"erro": "rota não simulada"})
```

Função que recebe cada requisição: procura a primeira rota cujo trecho aparece na URL e devolve a resposta (chamando a função, se for uma). Sem rota, devolve 404.

### Linha 55

```python
    return httpx.Client(transport=httpx.MockTransport(handler))
```

Cria o `httpx.Client` com o transporte falso.

### Linha 58

```python
# ---------- rede e erros ----------
```

Comentário: testes de rede e erros.

### Linha 59

```python
def test_tenta_de_novo_em_503_e_depois_funciona():
```

Testa a nova tentativa em erro 503.

### Linhas 60 a 64

```python
    chamadas = []

    def resp(req):
        chamadas.append(1)
        return httpx.Response(503) if len(chamadas) < 3 else httpx.Response(200, json={"ok": True})
```

A rota responde 503 nas duas primeiras chamadas e 200 na terceira.

### Linhas 65 a 66

```python
    assert net.get_json("X", "https://api.teste/a", client=cliente({"api.teste": resp})) == {"ok": True}
    assert len(chamadas) == 3
```

Confere que o resultado final veio certo e que foram exatamente 3 chamadas.

### Linhas 69 a 72

```python
def test_erro_4xx_nao_tenta_de_novo():
    with pytest.raises(net.ApiError) as e:
        net.get_json("X", "https://api.teste/a", client=cliente({"api.teste": httpx.Response(401)}))
    assert "acesso negado" in str(e.value)
```

Erro 401 não tenta de novo: lança `ApiError` com "acesso negado".

### Linhas 75 a 80

```python
def test_timeout_vira_api_error():
    def lento(req):
        raise httpx.ReadTimeout("demorou", request=req)
    with pytest.raises(net.ApiError) as e:
        net.get_json("X", "https://api.teste/a", client=cliente({"api.teste": lento}))
    assert "sem resposta" in str(e.value)
```

Timeout: a rota lança `ReadTimeout`, e o teste confere que virou um `ApiError` com "sem resposta".

### Linha 83

```python
# ---------- clima ----------
```

Comentário: clima.

### Linhas 84 a 88

```python
def test_intensidade_da_chuva():
    assert weather.intensidade(0, 0) == 0
    assert weather.intensidade(63, 0) == 0.6
    assert weather.intensidade(61, 12) == 1.0          # muita chuva medida vence o código
    assert weather.intensidade(95, 0) >= 0.95
```

Testa a intensidade da chuva: seco dá 0, código de chuva dá 0,6, muita chuva medida vence o código e trovoada fica perto de 1.

### Linha 91

```python
def test_clima_transforma_json(cfg):
```

Testa a conversão do JSON do Open-Meteo.

### Linhas 92 a 99

```python
    geo = {"results": [{"latitude": -23.5, "longitude": -46.6, "name": "São Paulo"}]}
    prev = {
        "current": {"time": "2026-11-06T14:00", "temperature_2m": 24.3, "precipitation": 2.1,
                    "cloud_cover": 90, "weather_code": 63, "wind_speed_10m": 12},
        "hourly": {"time": ["2026-11-06T13:00", "2026-11-06T14:00"], "precipitation_probability": [40, 85]},
        "daily": {"temperature_2m_max": [27], "temperature_2m_min": [18],
                  "sunrise": ["2026-11-06T05:20"], "sunset": ["2026-11-06T18:30"]},
    }
```

Respostas falsas do geocoding e do forecast, no formato real da API.

### Linha 100

```python
    weather._geo_cache.clear()
```

Limpa o cache de cidades (para o teste não depender de outro).

### Linhas 101 a 102

```python
    c = weather.buscar({"local": "São Paulo"}, "America/Sao_Paulo",
                       client=cliente({"geocoding": httpx.Response(200, json=geo), "forecast": httpx.Response(200, json=prev)}))
```

Busca o clima com o cliente falso.

### Linhas 103 a 104

```python
    assert (c.temperatura, c.prob_chuva, c.descricao) == (24.3, 85, "chuva")
    assert 0.5 < c.intensidade_chuva < 0.7
```

Confere temperatura, chance de chuva da hora certa (85, não 40), descrição e intensidade.

### Linha 107

```python
# ---------- Slack ----------
```

Comentário: Slack.

### Linha 108

```python
def test_slack_marca_mencao_como_urgente(cfg):
```

Testa que menção vira urgente.

### Linha 109

```python
    con = SlackConector("Empresa", {"token_env": "T_SLACK", "meu_id_env": "T_SLACK_ID", "canais": ["C1"]}, cfg)
```

Cria o conector com os tokens de teste.

### Linha 110

```python
    agora = datetime.now().timestamp()
```

Hora atual.

### Linhas 111 a 120

```python
    con.client = cliente({
        "conversations.info": httpx.Response(200, json={"ok": True, "channel": {"name": "geral"}}),
        "users.info": httpx.Response(200, json={"ok": True, "user": {"real_name": "Marina", "profile": {}}}),
        "conversations.history": httpx.Response(200, json={"ok": True, "messages": [
            {"user": "U2", "text": "<@UEU> pode revisar?", "ts": f"{agora:.6f}"},
            {"user": "U2", "text": "bom dia", "ts": f"{agora - 5:.6f}"},
            {"subtype": "channel_join", "text": "entrou", "ts": f"{agora:.6f}"},
            {"user": "UEU", "text": "minha própria msg", "ts": f"{agora:.6f}"},
        ]}),
    })
```

Respostas falsas: nome do canal, nome do usuário e quatro mensagens (uma com menção, uma normal, uma de sistema e uma do próprio usuário).

### Linha 121

```python
    itens = con.coletar()
```

Coleta.

### Linha 122

```python
    assert [i.prioridade for i in itens] == [URGENTE, NORMAL]
```

Só sobram duas (a de sistema e a própria foram ignoradas), na ordem urgente e normal.

### Linha 123

```python
    assert itens[0].titulo == "Marina: @Marina pode revisar?"   # <@id> vira @nome
```

A menção `<@UEU>` virou "@Marina" no texto.

### Linha 124

```python
    assert itens[0].detalhe == "#geral"
```

O detalhe é o nome do canal.

### Linhas 127 a 131

```python
def test_slack_ok_false_vira_erro(cfg):
    con = SlackConector("Empresa", {"token_env": "T_SLACK", "canais": ["C1"]}, cfg)
    con.client = cliente({"slack.com": httpx.Response(200, json={"ok": False, "error": "invalid_auth"})})
    with pytest.raises(net.ApiError, match="invalid_auth"):
        con._api("conversations.history", channel="C1")
```

`ok: false` do Slack vira `ApiError` com o código do erro. `pytest.raises(..., match=...)` confere o tipo e o texto da exceção.

### Linha 134

```python
# ---------- ClickUp ----------
```

Comentário: ClickUp.

### Linha 135

```python
def test_clickup_atrasada_vira_urgente(cfg):
```

Testa que tarefa atrasada vira urgente.

### Linha 136

```python
    con = ClickUpConector("Empresa", {"token_env": "T_CLICKUP", "equipe_id_env": "T_TEAM"}, cfg)
```

Cria o conector.

### Linhas 137 a 138

```python
    ontem = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
    amanha = int((datetime.now() + timedelta(days=1)).timestamp() * 1000)
```

Datas de ontem e amanhã em milissegundos.

### Linhas 139 a 146

```python
    con.client = cliente({
        "/user": httpx.Response(200, json={"user": {"id": 42}}),
        "/task": httpx.Response(200, json={"tasks": [
            {"id": "a", "name": "Atrasada", "due_date": str(ontem), "priority": {"id": "3"}, "status": {"status": "aberta"}},
            {"id": "b", "name": "Amanhã", "due_date": str(amanha), "priority": {"id": "2"}, "status": {"status": "aberta"}},
            {"id": "c", "name": "Sem prazo", "due_date": None},
        ]}),
    })
```

Respostas falsas: o usuário e três tarefas (atrasada, amanhã e sem prazo).

### Linhas 147 a 149

```python
    itens = con.coletar()
    assert [(i.titulo, i.prioridade) for i in itens] == [("Atrasada", URGENTE), ("Amanhã", ALTA)]
    assert itens[0].detalhe == "ATRASADA"
```

A sem prazo foi ignorada; a atrasada ficou urgente com "ATRASADA" e a de amanhã ficou alta (prioridade 2 do ClickUp).

### Linha 152

```python
# ---------- Microsoft / agendador ----------
```

Comentário: Microsoft e agendador.

### Linhas 153 a 154

```python
def test_texto_puro_do_teams():
    assert texto_puro("<p>Oi &amp; tudo <b>bem</b>?</p>") == "Oi & tudo bem ?"
```

Testa a limpeza do HTML do Teams.

### Linha 157

```python
def test_find_meeting_times(cfg, monkeypatch):
```

Testa a chamada `findMeetingTimes`.

### Linha 158

```python
    con = MicrosoftConector("Outra Empresa", {"client_id_env": "T_MS"}, cfg)
```

Cria o conector Microsoft.

### Linha 159

```python
    monkeypatch.setattr(con, "_token", lambda: "token")
```

Troca o método do token por uma função que devolve um texto fixo (sem login de verdade).

### Linha 160

```python
    enviado = {}
```

Dicionário para guardar o que foi enviado.

### Linhas 162 a 171

```python
    def responder(req):
        enviado.update(json.loads(req.content))
        return httpx.Response(200, json={"meetingTimeSuggestions": [
            {"confidence": 100, "meetingTimeSlot": {"start": {"dateTime": "2026-11-09T10:00:00.0000000"},
                                                    "end": {"dateTime": "2026-11-09T10:30:00.0000000"}}},
            {"confidence": 100, "meetingTimeSlot": {"start": {"dateTime": "2026-11-09T10:30:00.0000000"},
                                                    "end": {"dateTime": "2026-11-09T11:00:00.0000000"}}},
            {"confidence": 90, "meetingTimeSlot": {"start": {"dateTime": "2026-11-10T14:00:00.0000000"},
                                                   "end": {"dateTime": "2026-11-10T14:30:00.0000000"}}},
        ]})
```

A rota guarda o corpo enviado e responde com três sugestões (duas no dia 9 e uma no dia 10).

### Linhas 172 a 174

```python
    con.client = cliente({"findMeetingTimes": responder})
    jan = [(datetime(2026, 11, 9, 9, tzinfo=FUSO), datetime(2026, 11, 9, 18, tzinfo=FUSO))]
    hs = con.horarios_livres("ana@empresa.com", 30, jan, maximo=2)
```

Busca no máximo 2 horários.

### Linhas 175 a 176

```python
    assert enviado["meetingDuration"] == "PT30M"
    assert enviado["attendees"][0]["emailAddress"]["address"] == "ana@empresa.com"
```

Confere o formato enviado: duração "PT30M" e o e-mail da pessoa.

### Linhas 177 a 178

```python
    # espalha: um horário por dia antes de repetir o mesmo dia
    assert [h.inicio.strftime("%d %H:%M") for h in hs] == ["09 10:00", "10 14:00"]
```

Confere que a função espalhou: um horário de cada dia em vez de dois seguidos no dia 9.

### Linhas 181 a 187

```python
def test_find_meeting_times_sem_horario(cfg, monkeypatch):
    con = MicrosoftConector("Outra Empresa", {"client_id_env": "T_MS"}, cfg)
    monkeypatch.setattr(con, "_token", lambda: "token")
    con.client = cliente({"findMeetingTimes": httpx.Response(200, json={
        "meetingTimeSuggestions": [], "emptySuggestionsReason": "AttendeesUnavailable"})})
    with pytest.raises(net.ApiError, match="AttendeesUnavailable"):
        con.horarios_livres("ana@empresa.com", 30, [])
```

Sem sugestões, lança erro com o motivo dado pelo Outlook.

### Linhas 190 a 195

```python
def test_reconhece_pedido_de_reuniao():
    p = ["reunião", "call", "conversar", "alinhar"]
    assert eh_pedido("Podemos marcar uma reunião essa semana?", p)
    assert eh_pedido("bora fazer uma call amanhã", p)
    assert not eh_pedido("a reunião de ontem foi ótima", p)
    assert not eh_pedido("ok, obrigado!", p)
```

Testa o reconhecimento de pedido de reunião: os dois primeiros devem disparar, os dois últimos não.

### Linhas 198 a 203

```python
@pytest.mark.parametrize("comando, esperado", [
    ("reunião com Ana amanhã 45min sobre orçamento", ("Ana", date(2026, 11, 7), None, 45, "orçamento")),
    ("call com João Pedro na sexta-feira 1h", ("João Pedro", date(2026, 11, 13), None, 60, "Reunião com João Pedro")),
    ("reuniao com Beatriz 12/11 às 14h", ("Beatriz", date(2026, 11, 12), time(14), 30, "Reunião com Beatriz")),
    ("marcar reunião com Lucas hoje", ("Lucas", date(2026, 11, 6), None, 30, "Reunião com Lucas")),
])
```

`parametrize` roda o mesmo teste com vários dados. Cada linha tem um comando e o resultado esperado (pessoa, dia, hora, duração e assunto).

### Linhas 204 a 206

```python
def test_interpreta_comando(comando, esperado):
    r = interpretar(comando, date(2026, 11, 6))       # 06/11/2026 é uma sexta-feira
    assert (r["pessoa"], r["dia"], r["hora"], r["duracao"], r["assunto"]) == esperado
```

Interpreta tomando 06/11/2026 (uma sexta) como hoje e compara.

### Linhas 209 a 210

```python
def test_comando_que_nao_e_reuniao():
    assert interpretar("oi tudo bem", date(2026, 11, 6)) is None
```

Um texto qualquer não é comando.

### Linhas 213 a 217

```python
def test_janelas_pulam_fim_de_semana_e_respeitam_agora(cfg):
    sexta_16h = datetime(2026, 11, 6, 16, 10, tzinfo=FUSO)
    jan = janelas(cfg, FUSO, sexta_16h, dias=2)
    assert jan[0][0] == datetime(2026, 11, 6, 17, 0, tzinfo=FUSO)    # 16:10 + 30 min, arredondado
    assert jan[1][0].date() == date(2026, 11, 9)                        # pula sábado e domingo
```

Testa as janelas: numa sexta às 16:10, a primeira janela começa às 17:00 (16:10 mais 30 minutos, arredondado) e a segunda é segunda-feira (pulou o fim de semana).

### Linhas 220 a 224

```python
def test_espalhar_prefere_dias_diferentes():
    base = datetime(2026, 11, 9, 10, tzinfo=FUSO)
    hs = [Horario(base + timedelta(minutes=30 * i), base + timedelta(minutes=30 * i + 30)) for i in range(4)]
    hs.append(Horario(base + timedelta(days=1), base + timedelta(days=1, minutes=30)))
    assert len({h.inicio.date() for h in espalhar(hs, 2)}) == 2
```

Testa o `espalhar`: com quatro horários num dia e um no outro, pedindo 2, vêm dois dias diferentes.

### Linha 227

```python
# ---------- resumo e notificações ----------
```

Comentário: resumo e notificações.

### Linhas 228 a 233

```python
def test_ordena_por_prioridade_e_horario():
    agora = datetime.now(FUSO)
    itens = [Item("A", "x", "tarefa", "normal", quando=agora, prioridade=NORMAL),
             Item("A", "x", "tarefa", "urgente tarde", quando=agora + timedelta(hours=2), prioridade=URGENTE),
             Item("A", "x", "tarefa", "urgente cedo", quando=agora, prioridade=URGENTE)]
    assert [i.titulo for i in digest.ordenar(itens)] == ["urgente cedo", "urgente tarde", "normal"]
```

Testa a ordenação: urgentes primeiro e, entre eles, o mais cedo primeiro.

### Linha 236

```python
def test_fonte_com_erro_nao_derruba_o_resumo():
```

Testa que uma fonte com erro não derruba o resumo.

### Linhas 237 a 247

```python
    class Quebrado:
        nome = "Quebrado"

        def coletar(self):
            raise net.ApiError("Slack", "fora do ar")

    class Bom:
        nome = "Bom"

        def coletar(self):
            return [Item("A", "x", "tarefa", "ok")]
```

Duas classes falsas: uma que sempre falha e outra que devolve um item.

### Linhas 248 a 249

```python
    r = digest.coletar([Quebrado(), Bom()])
    assert len(r.itens) == 1 and "fora do ar" in r.erros[0]
```

O resumo tem o item da fonte boa e o erro da fonte quebrada.

### Linha 252

```python
def test_notifica_discord_e_celular_ao_mesmo_tempo(cfg, monkeypatch, tmp_path):
```

Testa o envio para Discord e celular ao mesmo tempo.

### Linhas 253 a 255

```python
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.test/webhook")
    monkeypatch.setenv("NTFY_TOPIC", "meu-topico")
    monkeypatch.setattr("pixeldigest.notify.PENDENTES", tmp_path / "pendentes.json")
```

Configura os dois canais e aponta a fila de pendentes para a pasta temporária.

### Linhas 256 a 262

```python
    recebidos = {}

    def guardar(nome):
        def f(req):
            recebidos[nome] = json.loads(req.content)
            return httpx.Response(204 if nome == "discord" else 200)
        return f
```

Rotas que guardam o corpo recebido por cada canal.

### Linhas 263 a 264

```python
    n = Notificador(cfg)
    n.client = cliente({"discord.test": guardar("discord"), "ntfy.sh": guardar("ntfy")})
```

Cria o notificador com o cliente falso.

### Linha 265

```python
    assert n.enviar("Título", "Texto", "#ff0000", campos=[("Empresa", "linha")]) == {"discord": True, "celular": True}
```

Os dois envios deram certo.

### Linha 266

```python
    assert recebidos["discord"]["embeds"][0]["color"] == 0xFF0000
```

A cor "#ff0000" virou o número `0xFF0000` no Discord.

### Linha 267

```python
    assert recebidos["ntfy"]["topic"] == "meu-topico" and "Empresa" in recebidos["ntfy"]["message"]
```

O ntfy recebeu o tópico e os campos dentro da mensagem.

### Linha 270

```python
def test_notificacao_que_falha_fica_pendente(cfg, monkeypatch, tmp_path):
```

Testa a fila de reenvio.

### Linhas 271 a 274

```python
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.test/webhook")
    monkeypatch.setenv("NTFY_TOPIC", "")
    pend = tmp_path / "pendentes.json"
    monkeypatch.setattr("pixeldigest.notify.PENDENTES", pend)
```

Só o Discord ligado e a fila na pasta temporária.

### Linhas 275 a 277

```python
    n = Notificador(cfg)
    n.client = cliente({"discord.test": httpx.Response(503)})
    assert n.enviar("T", "x") == {"discord": False}
```

O Discord responde 503: o envio falha.

### Linha 278

```python
    assert len(json.loads(pend.read_text())) == 1
```

A mensagem foi guardada na fila.

### Linhas 279 a 281

```python
    n.client = cliente({"discord.test": httpx.Response(204)})
    assert n.reenviar_pendentes() == 1
    assert json.loads(pend.read_text()) == []
```

Agora o Discord responde 204: o reenvio funciona e a fila fica vazia.

### Linha 284

```python
# ---------- configurações salvas pela tela ----------
```

Comentário: configurações.

### Linhas 285 a 286

```python
def test_nome_da_chave_no_env():
    assert config.nome_segredo("Minha Empresa", "slack", "token") == "PD_MINHA_EMPRESA_SLACK_TOKEN"
```

Testa o nome da variável secreta.

### Linha 289

```python
def test_salvar_separa_segredos_do_yaml(monkeypatch, tmp_path):
```

Testa que o salvar separa os segredos.

### Linhas 290 a 291

```python
    monkeypatch.setattr(config, "ARQ_CONFIG", tmp_path / "config.yaml")
    monkeypatch.setattr(config, "ARQ_ENV", tmp_path / ".env")
```

Arquivos na pasta temporária.

### Linhas 292 a 296

```python
    bruto = config.carregar_bruto()
    bruto["usuario"]["nome"] = "Felipe"
    bruto["empresas"] = [{"nome": "Acme", "cor": "#3fa7ff", "conectores": [
        {"tipo": "slack", "token_env": "PD_ACME_SLACK_TOKEN", "canais": ["C1"]}]}]
    config.salvar(bruto, {"PD_ACME_SLACK_TOKEN": "xoxb-segredo-123"})
```

Monta uma configuração com uma empresa e salva com um token.

### Linhas 297 a 298

```python
    yaml_txt = (tmp_path / "config.yaml").read_text(encoding="utf-8")
    assert "xoxb-segredo-123" not in yaml_txt and "PD_ACME_SLACK_TOKEN" in yaml_txt
```

O token não aparece no YAML; só o nome da variável aparece.

### Linha 299

```python
    assert "PD_ACME_SLACK_TOKEN=xoxb-segredo-123" in (tmp_path / ".env").read_text(encoding="utf-8")
```

O token está no `.env`.

### Linhas 300 a 301

```python
    cfg = config.preparar(config.carregar_bruto())
    assert cfg["usuario"]["nome"] == "Felipe" and cfg["horarios"]["inicio_dia"] == time(7, 0)
```

Recarrega e confere que o nome e o horário padrão vieram certos.

### Linhas 304 a 308

```python
def test_empresa_sem_nome_nao_salva():
    bruto = config.carregar_bruto()
    bruto["empresas"] = [{"nome": "", "conectores": []}]
    with pytest.raises(config.ConfigError):
        config.preparar(bruto)
```

Empresa sem nome não passa na validação.

### Linhas 311 a 313

```python
def test_lugar_curto_prefere_municipio():
    assert weather.lugar_curto({"suburb": "Centro", "city": "Sede", "municipality": "Pelotas"}) == "Centro, Pelotas"
    assert weather.lugar_curto({"suburb": "Consolação", "city": "São Paulo"}) == "Consolação, São Paulo"
```

Testa o nome curto do lugar: prefere o município ao distrito.

### Linha 316

```python
def test_slack_pula_canal_apagado_e_dm_sem_permissao(cfg):
```

Testa a resiliência do Slack.

### Linha 317

```python
    con = SlackConector("Empresa", {"token_env": "T_SLACK", "canais": ["CAPAGADO", "C1"], "incluir_dms": True}, cfg)
```

Um canal apagado, um bom e as DMs ligadas.

### Linha 318

```python
    agora = datetime.now().timestamp()
```

Hora atual.

### Linhas 320 a 323

```python
    def historico(req):
        if "CAPAGADO" in str(req.url):
            return httpx.Response(200, json={"ok": False, "error": "channel_not_found"})
        return httpx.Response(200, json={"ok": True, "messages": [{"user": "U2", "text": "oi", "ts": f"{agora:.6f}"}]})
```

Histórico: erro para o canal apagado e uma mensagem para o bom.

### Linhas 324 a 329

```python
    con.client = cliente({
        "conversations.info": httpx.Response(200, json={"ok": False, "error": "channel_not_found"}),
        "users.conversations": httpx.Response(200, json={"ok": False, "error": "missing_scope"}),
        "users.info": httpx.Response(200, json={"ok": True, "user": {"real_name": "Ana", "profile": {}}}),
        "conversations.history": historico,
    })
```

As outras rotas: nome do canal com erro, DMs sem permissão (`missing_scope`) e nome do usuário.

### Linhas 330 a 333

```python
    itens = con.coletar()
    assert len(itens) == 1                                   # o canal bom continua funcionando
    assert any("channel_not_found" in a for a in con.avisos)
    assert any("xoxp" in a for a in con.avisos)
```

O canal bom continuou funcionando, e os avisos contam o canal apagado e a falta do token de usuário.

### Linha 336

```python
def test_limpar_resumo_esconde_itens_e_lembra(monkeypatch, tmp_path):
```

Testa o botão de limpar.

### Linhas 337 a 339

```python
    from pixeldigest import core
    monkeypatch.setattr(core, "DATA", tmp_path)
    monkeypatch.setattr(digest, "DATA", tmp_path)
```

Aponta as pastas de dados para a temporária.

### Linhas 340 a 343

```python
    m = core.Motor(config.carregar(demo=True))
    m.atualizar_resumo(avisar_urgentes=False)
    total = len(m.resumo.itens)
    primeiro = m.resumo.itens[0].chave()
```

Cria o motor em modo demonstração, monta o resumo e guarda o total e a chave do primeiro item.

### Linhas 344 a 345

```python
    m.limpar([primeiro])                          # o "x" de um item só
    assert len(m.resumo.itens) == total - 1
```

Tira um item: sobra um a menos.

### Linhas 346 a 347

```python
    m.limpar()                                    # botão "Limpar"
    assert m.resumo.itens == []
```

Limpa tudo: lista vazia.

### Linhas 348 a 350

```python
    m2 = core.Motor(config.carregar(demo=True))   # abriu de novo: continua limpo
    m2.atualizar_resumo(avisar_urgentes=False)
    assert m2.resumo.itens == []
```

Um motor novo (como se o programa tivesse sido reaberto) continua com a lista vazia, porque as chaves foram salvas.

### Linha 353

```python
def test_nao_abre_duas_copias():
```

Testa a trava de instância única.

### Linha 354

```python
    from pixeldigest import __main__ as principal
```

Importa o módulo principal.

### Linha 355

```python
    porta = 47391 + 7                             # outra porta: o app de verdade pode estar aberto
```

Usa outra porta para não bater no programa real, que pode estar aberto.

### Linhas 356 a 357

```python
    assert principal.ja_esta_aberto(porta) is False
    primeira = principal._trava                   # a 1ª cópia segura a porta
```

A primeira cópia consegue a porta.

### Linha 358

```python
    assert principal.ja_esta_aberto(porta) is True     # a 2ª percebe e desiste
```

A segunda percebe que já está aberto.

### Linha 359

```python
    primeira.close()
```

Libera a porta.

### Linha 362

```python
# ---------- e-mails, IA e menos requisições ----------
```

Comentário: e-mails, IA e menos requisições.

### Linha 363

```python
def test_texto_do_email_tira_citacao():
```

Testa a extração do texto do e-mail.

### Linhas 364 a 368

```python
    import base64
    from pixeldigest.connectors.google import texto_do_email
    corpo = "Oi Felipe,\nPreciso da aprovação até sexta.\n\nOn Mon, Ana wrote:\n> mensagem antiga"
    payload = {"mimeType": "multipart/alternative", "parts": [
        {"mimeType": "text/plain", "body": {"data": base64.urlsafe_b64encode(corpo.encode()).decode()}}]}
```

Monta um e-mail com o corpo em Base64 e uma citação de resposta antiga.

### Linha 369

```python
    assert texto_do_email(payload) == "Oi Felipe, Preciso da aprovação até sexta."
```

O texto final não tem a citação.

### Linha 372

```python
def test_resumo_email_com_ia_e_reaproveita(monkeypatch, tmp_path):
```

Testa o resumo com IA e o reaproveitamento.

### Linhas 373 a 376

```python
    import sys
    import types
    from pixeldigest import resumo_email
    monkeypatch.setattr(resumo_email, "CACHE", tmp_path / "c.json")
```

Imports e cache na pasta temporária.

### Linha 377

```python
    chamadas = []
```

Lista das chamadas feitas.

### Linhas 379 a 383

```python
    class Resposta:
        stop_reason = "end_turn"
        content = [types.SimpleNamespace(type="text", text=json.dumps(
            {"resumo": "1 pedido urgente", "pontos": [{"titulo": "Financeiro: aprovar NF", "detalhe": "até sexta",
                                                         "prioridade": "alta", "acao": "aprovar"}]}))]
```

Resposta falsa no formato do SDK: um bloco de texto com o JSON do resumo.

### Linhas 385 a 391

```python
    class Cliente:
        def __init__(self, **kw):
            self.messages = self

        def create(self, **kw):
            chamadas.append(kw)
            return Resposta()
```

Cliente falso: `messages.create` guarda os argumentos e devolve a resposta.

### Linhas 392 a 394

```python
    falso = types.SimpleNamespace(Anthropic=Cliente, AuthenticationError=type("A", (Exception,), {}),
                                  APIError=type("B", (Exception,), {}))
    monkeypatch.setitem(sys.modules, "anthropic", falso)
```

Módulo `anthropic` falso, colocado no lugar do verdadeiro em `sys.modules`. Assim o teste não usa internet nem chave.

### Linhas 395 a 396

```python
    msgs = [{"id": "1", "de": "Financeiro", "assunto": "NF", "quando": 1794016409, "texto": "aprovar até sexta",
             "nao_lido": True, "importante": True}]
```

Um e-mail de exemplo.

### Linhas 397 a 398

```python
    r = resumo_email.resumir("felipe@x.com", msgs, "sk-ant-teste", "claude-opus-5-5")
    assert r["fonte"] == "ia" and r["pontos"][0]["acao"] == "aprovar"
```

O resumo veio da IA com a ação certa.

### Linhas 399 a 401

```python
    kw = chamadas[0]
    assert kw["model"] == "claude-opus-5-5"
    assert kw["output_config"]["format"]["type"] == "json_schema"
```

Confere o modelo e que a resposta foi pedida em JSON com schema.

### Linhas 402 a 403

```python
    resumo_email.resumir("felipe@x.com", msgs, "sk-ant-teste", "claude-opus-5-5")
    assert len(chamadas) == 1                        # mesmos e-mails: não chama a IA de novo
```

Pedindo de novo com os mesmos e-mails, a IA não é chamada outra vez.

### Linhas 406 a 411

```python
def test_resumo_email_sem_chave_faz_resumo_simples():
    from pixeldigest import resumo_email
    msgs = [{"id": "1", "de": "Ana", "assunto": "Oi", "quando": 1794016409, "texto": "tudo bem?",
             "nao_lido": True, "importante": False}]
    r = resumo_email.resumir("conta", msgs, "", "claude-opus-5-5")
    assert r["fonte"] == "simples" and r["pontos"][0]["titulo"] == "Ana: Oi"
```

Sem chave, o resumo é o simples, com "remetente: assunto".

### Linha 414

```python
def test_motor_so_busca_fonte_com_novidade(monkeypatch, tmp_path):
```

Testa que o motor só busca uma fonte quando há novidade.

### Linhas 415 a 419

```python
    from pixeldigest import core
    monkeypatch.setattr(core, "DATA", tmp_path)
    monkeypatch.setattr(digest, "DATA", tmp_path)
    m = core.Motor(config.carregar(demo=True))
    m.atualizar_resumo(avisar_urgentes=False)          # busca completa ao abrir
```

Pastas temporárias, motor de demonstração e busca completa inicial.

### Linhas 420 a 428

```python
    contagem = {"coletar": 0}
    fonte = m.fontes[0]
    fonte.conector.tem_novidade = lambda: False
    original = fonte.conector.coletar

    def coletar():
        contagem["coletar"] += 1
        return original()
    fonte.conector.coletar = coletar
```

Conta as chamadas a `coletar` e faz a fonte dizer que não há novidade.

### Linhas 429 a 431

```python
    fonte.proxima = 0
    m.conferir_fontes()
    assert contagem["coletar"] == 0                     # sem novidade: não baixa de novo
```

Força a hora da conferência: sem novidade, nenhuma coleta.

### Linhas 432 a 435

```python
    fonte.conector.tem_novidade = lambda: True
    fonte.proxima = 0
    m.conferir_fontes()
    assert contagem["coletar"] == 1
```

Agora com novidade: uma coleta.

### Linhas 438 a 444

```python
def test_empresa_desligada_nao_monta_conectores(cfg):
    cfg["demo"] = False
    cfg["empresas"] = [{"nome": "Outra Empresa", "ativa": False, "cor": "#fff",
                        "conectores": [{"tipo": "microsoft", "client_id": "x"}]}]
    from pixeldigest import connectors
    conectores, erros = connectors.montar(cfg)
    assert conectores == [] and erros == []
```

Empresa desligada não cria conectores nem erros.

### Linha 447

```python
# ---------- tela responsiva ("media queries") ----------
```

Comentário: tela responsiva.

### Linhas 448 a 452

```python
def test_orientacao_automatica_segue_a_janela():
    from pixeldigest.ui import tela
    assert tela.orientacao({"orientacao": "automatica"}, (1920, 1080)) == "horizontal"
    assert tela.orientacao({"orientacao": "automatica"}, (1080, 1920)) == "vertical"
    assert tela.orientacao({"orientacao": "vertical"}, (1920, 1080)) == "vertical"
```

Orientação automática segue a janela; a fixa ignora a janela.

### Linha 455

```python
def test_viewport_converte_clique_da_janela_para_tela_logica():
```

Testa a conversão do clique.

### Linhas 456 a 459

```python
    from pixeldigest.ui import tela
    v = tela.Viewport()
    v.ajustar((720, 1280), (1080, 1920))                 # vertical ampliada 1,5x
    assert v.para_logico((540, 960)) == (360, 640)
```

Tela vertical ampliada 1,5 vez: o centro da janela é o centro da tela lógica.

### Linhas 460 a 461

```python
    v.ajustar((1280, 720), (1280, 1000))                 # sobra faixa preta em cima e embaixo
    assert v.oy == 140 and v.para_logico((0, 140)) == (0, 0)
```

Janela mais alta que a proporção: sobram 140 pixels de faixa preta em cima, e o ponto (0, 140) da janela é o canto da tela lógica.

### Linha 464

```python
def test_cena_vertical_e_ceu_cinza_com_chuva():
```

Testa o cenário vertical e o céu cinza com chuva.

### Linhas 465 a 469

```python
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    from pixeldigest.ui.scene import Cena
    pygame.init()
```

Driver de vídeo falso e inicialização do pygame.

### Linhas 470 a 471

```python
    c = Cena(180, 320)
    assert c.draw(datetime(2026, 11, 7, 12, 0)).get_size() == (180, 320)
```

O cenário vertical desenha no tamanho certo.

### Linhas 472 a 474

```python
    c.definir_clima(preset="chuva")
    c.vis = dict(c.alvo)
    assert c.cobertura == 1.0                            # chuva fecha o céu: sem sol e sem azul
```

Com chuva, a cobertura é total: sem sol e sem céu azul.
