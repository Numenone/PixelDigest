"""Testes sem internet: as APIs são simuladas com httpx.MockTransport.

Rodar: .venv\\Scripts\\python -m pytest -q
"""
import json
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest

from pixeldigest import config, digest, net
from pixeldigest.connectors import weather
from pixeldigest.connectors.clickup import ClickUpConector
from pixeldigest.connectors.microsoft import MicrosoftConector, espalhar, texto_puro
from pixeldigest.connectors.slack import SlackConector
from pixeldigest.meetings import eh_pedido, interpretar, janelas
from pixeldigest.models import ALTA, NORMAL, URGENTE, Horario, Item
from pixeldigest.notify import Notificador

FUSO = ZoneInfo("America/Sao_Paulo")


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    monkeypatch.setattr(net.time, "sleep", lambda s: None)


@pytest.fixture(autouse=True)
def sem_arquivos_reais(monkeypatch, tmp_path):
    """Os testes nunca leem nem gravam o config.yaml/.env de verdade do usuário."""
    monkeypatch.setattr(config, "ARQ_CONFIG", tmp_path / "config-teste.yaml")
    monkeypatch.setattr(config, "ARQ_ENV", tmp_path / "env-teste")


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


def cliente(rotas):
    """Cliente HTTP falso: rotas = {trecho_da_url: função(request) -> httpx.Response}."""
    def handler(req):
        for trecho, resp in rotas.items():
            if trecho in str(req.url):
                return resp(req) if callable(resp) else resp
        return httpx.Response(404, json={"erro": "rota não simulada"})
    return httpx.Client(transport=httpx.MockTransport(handler))


# ---------- rede e erros ----------
def test_tenta_de_novo_em_503_e_depois_funciona():
    chamadas = []

    def resp(req):
        chamadas.append(1)
        return httpx.Response(503) if len(chamadas) < 3 else httpx.Response(200, json={"ok": True})
    assert net.get_json("X", "https://api.teste/a", client=cliente({"api.teste": resp})) == {"ok": True}
    assert len(chamadas) == 3


def test_erro_4xx_nao_tenta_de_novo():
    with pytest.raises(net.ApiError) as e:
        net.get_json("X", "https://api.teste/a", client=cliente({"api.teste": httpx.Response(401)}))
    assert "acesso negado" in str(e.value)


def test_timeout_vira_api_error():
    def lento(req):
        raise httpx.ReadTimeout("demorou", request=req)
    with pytest.raises(net.ApiError) as e:
        net.get_json("X", "https://api.teste/a", client=cliente({"api.teste": lento}))
    assert "sem resposta" in str(e.value)


# ---------- clima ----------
def test_intensidade_da_chuva():
    assert weather.intensidade(0, 0) == 0
    assert weather.intensidade(63, 0) == 0.6
    assert weather.intensidade(61, 12) == 1.0          # muita chuva medida vence o código
    assert weather.intensidade(95, 0) >= 0.95


def test_clima_transforma_json(cfg):
    geo = {"results": [{"latitude": -23.5, "longitude": -46.6, "name": "São Paulo"}]}
    prev = {
        "current": {"time": "2026-11-06T14:00", "temperature_2m": 24.3, "precipitation": 2.1,
                    "cloud_cover": 90, "weather_code": 63, "wind_speed_10m": 12},
        "hourly": {"time": ["2026-11-06T13:00", "2026-11-06T14:00"], "precipitation_probability": [40, 85]},
        "daily": {"temperature_2m_max": [27], "temperature_2m_min": [18],
                  "sunrise": ["2026-11-06T05:20"], "sunset": ["2026-11-06T18:30"]},
    }
    weather._geo_cache.clear()
    c = weather.buscar({"local": "São Paulo"}, "America/Sao_Paulo",
                       client=cliente({"geocoding": httpx.Response(200, json=geo), "forecast": httpx.Response(200, json=prev)}))
    assert (c.temperatura, c.prob_chuva, c.descricao) == (24.3, 85, "chuva")
    assert 0.5 < c.intensidade_chuva < 0.7


# ---------- Slack ----------
def test_slack_marca_mencao_como_urgente(cfg):
    con = SlackConector("Empresa", {"token_env": "T_SLACK", "meu_id_env": "T_SLACK_ID", "canais": ["C1"]}, cfg)
    agora = datetime.now().timestamp()
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
    itens = con.coletar()
    assert [i.prioridade for i in itens] == [URGENTE, NORMAL]
    assert itens[0].titulo == "Marina: @Marina pode revisar?"   # <@id> vira @nome
    assert itens[0].detalhe == "#geral"


def test_slack_ok_false_vira_erro(cfg):
    con = SlackConector("Empresa", {"token_env": "T_SLACK", "canais": ["C1"]}, cfg)
    con.client = cliente({"slack.com": httpx.Response(200, json={"ok": False, "error": "invalid_auth"})})
    with pytest.raises(net.ApiError, match="invalid_auth"):
        con._api("conversations.history", channel="C1")


# ---------- ClickUp ----------
def test_clickup_atrasada_vira_urgente(cfg):
    con = ClickUpConector("Empresa", {"token_env": "T_CLICKUP", "equipe_id_env": "T_TEAM"}, cfg)
    ontem = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
    amanha = int((datetime.now() + timedelta(days=1)).timestamp() * 1000)
    con.client = cliente({
        "/user": httpx.Response(200, json={"user": {"id": 42}}),
        "/task": httpx.Response(200, json={"tasks": [
            {"id": "a", "name": "Atrasada", "due_date": str(ontem), "priority": {"id": "3"}, "status": {"status": "aberta"}},
            {"id": "b", "name": "Amanhã", "due_date": str(amanha), "priority": {"id": "2"}, "status": {"status": "aberta"}},
            {"id": "c", "name": "Sem prazo", "due_date": None},
        ]}),
    })
    itens = con.coletar()
    assert [(i.titulo, i.prioridade) for i in itens] == [("Atrasada", URGENTE), ("Amanhã", ALTA)]
    assert itens[0].detalhe == "ATRASADA"


# ---------- Microsoft / agendador ----------
def test_texto_puro_do_teams():
    assert texto_puro("<p>Oi &amp; tudo <b>bem</b>?</p>") == "Oi & tudo bem ?"


def test_find_meeting_times(cfg, monkeypatch):
    con = MicrosoftConector("Outra Empresa", {"client_id_env": "T_MS"}, cfg)
    monkeypatch.setattr(con, "_token", lambda: "token")
    enviado = {}

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
    con.client = cliente({"findMeetingTimes": responder})
    jan = [(datetime(2026, 11, 9, 9, tzinfo=FUSO), datetime(2026, 11, 9, 18, tzinfo=FUSO))]
    hs = con.horarios_livres("ana@empresa.com", 30, jan, maximo=2)
    assert enviado["meetingDuration"] == "PT30M"
    assert enviado["attendees"][0]["emailAddress"]["address"] == "ana@empresa.com"
    # espalha: um horário por dia antes de repetir o mesmo dia
    assert [h.inicio.strftime("%d %H:%M") for h in hs] == ["09 10:00", "10 14:00"]


def test_find_meeting_times_sem_horario(cfg, monkeypatch):
    con = MicrosoftConector("Outra Empresa", {"client_id_env": "T_MS"}, cfg)
    monkeypatch.setattr(con, "_token", lambda: "token")
    con.client = cliente({"findMeetingTimes": httpx.Response(200, json={
        "meetingTimeSuggestions": [], "emptySuggestionsReason": "AttendeesUnavailable"})})
    with pytest.raises(net.ApiError, match="AttendeesUnavailable"):
        con.horarios_livres("ana@empresa.com", 30, [])


def test_reconhece_pedido_de_reuniao():
    p = ["reunião", "call", "conversar", "alinhar"]
    assert eh_pedido("Podemos marcar uma reunião essa semana?", p)
    assert eh_pedido("bora fazer uma call amanhã", p)
    assert not eh_pedido("a reunião de ontem foi ótima", p)
    assert not eh_pedido("ok, obrigado!", p)


@pytest.mark.parametrize("comando, esperado", [
    ("reunião com Ana amanhã 45min sobre orçamento", ("Ana", date(2026, 11, 7), None, 45, "orçamento")),
    ("call com João Pedro na sexta-feira 1h", ("João Pedro", date(2026, 11, 13), None, 60, "Reunião com João Pedro")),
    ("reuniao com Beatriz 12/11 às 14h", ("Beatriz", date(2026, 11, 12), time(14), 30, "Reunião com Beatriz")),
    ("marcar reunião com Lucas hoje", ("Lucas", date(2026, 11, 6), None, 30, "Reunião com Lucas")),
])
def test_interpreta_comando(comando, esperado):
    r = interpretar(comando, date(2026, 11, 6))       # 06/11/2026 é uma sexta-feira
    assert (r["pessoa"], r["dia"], r["hora"], r["duracao"], r["assunto"]) == esperado


def test_comando_que_nao_e_reuniao():
    assert interpretar("oi tudo bem", date(2026, 11, 6)) is None


def test_janelas_pulam_fim_de_semana_e_respeitam_agora(cfg):
    sexta_16h = datetime(2026, 11, 6, 16, 10, tzinfo=FUSO)
    jan = janelas(cfg, FUSO, sexta_16h, dias=2)
    assert jan[0][0] == datetime(2026, 11, 6, 17, 0, tzinfo=FUSO)    # 16:10 + 30 min, arredondado
    assert jan[1][0].date() == date(2026, 11, 9)                        # pula sábado e domingo


def test_espalhar_prefere_dias_diferentes():
    base = datetime(2026, 11, 9, 10, tzinfo=FUSO)
    hs = [Horario(base + timedelta(minutes=30 * i), base + timedelta(minutes=30 * i + 30)) for i in range(4)]
    hs.append(Horario(base + timedelta(days=1), base + timedelta(days=1, minutes=30)))
    assert len({h.inicio.date() for h in espalhar(hs, 2)}) == 2


# ---------- resumo e notificações ----------
def test_ordena_por_prioridade_e_horario():
    agora = datetime.now(FUSO)
    itens = [Item("A", "x", "tarefa", "normal", quando=agora, prioridade=NORMAL),
             Item("A", "x", "tarefa", "urgente tarde", quando=agora + timedelta(hours=2), prioridade=URGENTE),
             Item("A", "x", "tarefa", "urgente cedo", quando=agora, prioridade=URGENTE)]
    assert [i.titulo for i in digest.ordenar(itens)] == ["urgente cedo", "urgente tarde", "normal"]


def test_fonte_com_erro_nao_derruba_o_resumo():
    class Quebrado:
        nome = "Quebrado"

        def coletar(self):
            raise net.ApiError("Slack", "fora do ar")

    class Bom:
        nome = "Bom"

        def coletar(self):
            return [Item("A", "x", "tarefa", "ok")]
    r = digest.coletar([Quebrado(), Bom()])
    assert len(r.itens) == 1 and "fora do ar" in r.erros[0]


def test_notifica_discord_e_celular_ao_mesmo_tempo(cfg, monkeypatch, tmp_path):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.test/webhook")
    monkeypatch.setenv("NTFY_TOPIC", "meu-topico")
    monkeypatch.setattr("pixeldigest.notify.PENDENTES", tmp_path / "pendentes.json")
    recebidos = {}

    def guardar(nome):
        def f(req):
            recebidos[nome] = json.loads(req.content)
            return httpx.Response(204 if nome == "discord" else 200)
        return f
    n = Notificador(cfg)
    n.client = cliente({"discord.test": guardar("discord"), "ntfy.sh": guardar("ntfy")})
    assert n.enviar("Título", "Texto", "#ff0000", campos=[("Empresa", "linha")]) == {"discord": True, "celular": True}
    assert recebidos["discord"]["embeds"][0]["color"] == 0xFF0000
    assert recebidos["ntfy"]["topic"] == "meu-topico" and "Empresa" in recebidos["ntfy"]["message"]


def test_notificacao_que_falha_fica_pendente(cfg, monkeypatch, tmp_path):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.test/webhook")
    monkeypatch.setenv("NTFY_TOPIC", "")
    pend = tmp_path / "pendentes.json"
    monkeypatch.setattr("pixeldigest.notify.PENDENTES", pend)
    n = Notificador(cfg)
    n.client = cliente({"discord.test": httpx.Response(503)})
    assert n.enviar("T", "x") == {"discord": False}
    assert len(json.loads(pend.read_text())) == 1
    n.client = cliente({"discord.test": httpx.Response(204)})
    assert n.reenviar_pendentes() == 1
    assert json.loads(pend.read_text()) == []


# ---------- configurações salvas pela tela ----------
def test_nome_da_chave_no_env():
    assert config.nome_segredo("Minha Empresa", "slack", "token") == "PD_MINHA_EMPRESA_SLACK_TOKEN"


def test_salvar_separa_segredos_do_yaml(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "ARQ_CONFIG", tmp_path / "config.yaml")
    monkeypatch.setattr(config, "ARQ_ENV", tmp_path / ".env")
    bruto = config.carregar_bruto()
    bruto["usuario"]["nome"] = "Felipe"
    bruto["empresas"] = [{"nome": "Acme", "cor": "#3fa7ff", "conectores": [
        {"tipo": "slack", "token_env": "PD_ACME_SLACK_TOKEN", "canais": ["C1"]}]}]
    config.salvar(bruto, {"PD_ACME_SLACK_TOKEN": "xoxb-segredo-123"})
    yaml_txt = (tmp_path / "config.yaml").read_text(encoding="utf-8")
    assert "xoxb-segredo-123" not in yaml_txt and "PD_ACME_SLACK_TOKEN" in yaml_txt
    assert "PD_ACME_SLACK_TOKEN=xoxb-segredo-123" in (tmp_path / ".env").read_text(encoding="utf-8")
    cfg = config.preparar(config.carregar_bruto())
    assert cfg["usuario"]["nome"] == "Felipe" and cfg["horarios"]["inicio_dia"] == time(7, 0)


def test_empresa_sem_nome_nao_salva():
    bruto = config.carregar_bruto()
    bruto["empresas"] = [{"nome": "", "conectores": []}]
    with pytest.raises(config.ConfigError):
        config.preparar(bruto)


def test_lugar_curto_prefere_municipio():
    assert weather.lugar_curto({"suburb": "Centro", "city": "Sede", "municipality": "Pelotas"}) == "Centro, Pelotas"
    assert weather.lugar_curto({"suburb": "Consolação", "city": "São Paulo"}) == "Consolação, São Paulo"


def test_slack_pula_canal_apagado_e_dm_sem_permissao(cfg):
    con = SlackConector("Empresa", {"token_env": "T_SLACK", "canais": ["CAPAGADO", "C1"], "incluir_dms": True}, cfg)
    agora = datetime.now().timestamp()

    def historico(req):
        if "CAPAGADO" in str(req.url):
            return httpx.Response(200, json={"ok": False, "error": "channel_not_found"})
        return httpx.Response(200, json={"ok": True, "messages": [{"user": "U2", "text": "oi", "ts": f"{agora:.6f}"}]})
    con.client = cliente({
        "conversations.info": httpx.Response(200, json={"ok": False, "error": "channel_not_found"}),
        "users.conversations": httpx.Response(200, json={"ok": False, "error": "missing_scope"}),
        "users.info": httpx.Response(200, json={"ok": True, "user": {"real_name": "Ana", "profile": {}}}),
        "conversations.history": historico,
    })
    itens = con.coletar()
    assert len(itens) == 1                                   # o canal bom continua funcionando
    assert any("channel_not_found" in a for a in con.avisos)
    assert any("xoxp" in a for a in con.avisos)


def test_limpar_resumo_esconde_itens_e_lembra(monkeypatch, tmp_path):
    from pixeldigest import core
    monkeypatch.setattr(core, "DATA", tmp_path)
    monkeypatch.setattr(digest, "DATA", tmp_path)
    m = core.Motor(config.carregar(demo=True))
    m.atualizar_resumo(avisar_urgentes=False)
    total = len(m.resumo.itens)
    primeiro = m.resumo.itens[0].chave()
    m.limpar([primeiro])                          # o "x" de um item só
    assert len(m.resumo.itens) == total - 1
    m.limpar()                                    # botão "Limpar"
    assert m.resumo.itens == []
    m2 = core.Motor(config.carregar(demo=True))   # abriu de novo: continua limpo
    m2.atualizar_resumo(avisar_urgentes=False)
    assert m2.resumo.itens == []


def test_nao_abre_duas_copias():
    from pixeldigest import __main__ as principal
    porta = 47391 + 7                             # outra porta: o app de verdade pode estar aberto
    assert principal.ja_esta_aberto(porta) is False
    primeira = principal._trava                   # a 1ª cópia segura a porta
    assert principal.ja_esta_aberto(porta) is True     # a 2ª percebe e desiste
    primeira.close()


# ---------- e-mails, IA e menos requisições ----------
def test_texto_do_email_tira_citacao():
    import base64
    from pixeldigest.connectors.google import texto_do_email
    corpo = "Oi Felipe,\nPreciso da aprovação até sexta.\n\nOn Mon, Ana wrote:\n> mensagem antiga"
    payload = {"mimeType": "multipart/alternative", "parts": [
        {"mimeType": "text/plain", "body": {"data": base64.urlsafe_b64encode(corpo.encode()).decode()}}]}
    assert texto_do_email(payload) == "Oi Felipe, Preciso da aprovação até sexta."


def test_resumo_email_com_ia_e_reaproveita(monkeypatch, tmp_path):
    import sys
    import types
    from pixeldigest import resumo_email
    monkeypatch.setattr(resumo_email, "CACHE", tmp_path / "c.json")
    chamadas = []

    class Resposta:
        stop_reason = "end_turn"
        content = [types.SimpleNamespace(type="text", text=json.dumps(
            {"resumo": "1 pedido urgente", "pontos": [{"titulo": "Financeiro: aprovar NF", "detalhe": "até sexta",
                                                         "prioridade": "alta", "acao": "aprovar"}]}))]

    class Cliente:
        def __init__(self, **kw):
            self.messages = self

        def create(self, **kw):
            chamadas.append(kw)
            return Resposta()
    falso = types.SimpleNamespace(Anthropic=Cliente, AuthenticationError=type("A", (Exception,), {}),
                                  APIError=type("B", (Exception,), {}))
    monkeypatch.setitem(sys.modules, "anthropic", falso)
    msgs = [{"id": "1", "de": "Financeiro", "assunto": "NF", "quando": 1794016409, "texto": "aprovar até sexta",
             "nao_lido": True, "importante": True}]
    r = resumo_email.resumir("felipe@x.com", msgs, "sk-ant-teste", "claude-opus-5-5")
    assert r["fonte"] == "ia" and r["pontos"][0]["acao"] == "aprovar"
    kw = chamadas[0]
    assert kw["model"] == "claude-opus-5-5"
    assert kw["output_config"]["format"]["type"] == "json_schema"
    resumo_email.resumir("felipe@x.com", msgs, "sk-ant-teste", "claude-opus-5-5")
    assert len(chamadas) == 1                        # mesmos e-mails: não chama a IA de novo


def test_resumo_email_sem_chave_faz_resumo_simples():
    from pixeldigest import resumo_email
    msgs = [{"id": "1", "de": "Ana", "assunto": "Oi", "quando": 1794016409, "texto": "tudo bem?",
             "nao_lido": True, "importante": False}]
    r = resumo_email.resumir("conta", msgs, "", "claude-opus-5-5")
    assert r["fonte"] == "simples" and r["pontos"][0]["titulo"] == "Ana: Oi"


def test_motor_so_busca_fonte_com_novidade(monkeypatch, tmp_path):
    from pixeldigest import core
    monkeypatch.setattr(core, "DATA", tmp_path)
    monkeypatch.setattr(digest, "DATA", tmp_path)
    m = core.Motor(config.carregar(demo=True))
    m.atualizar_resumo(avisar_urgentes=False)          # busca completa ao abrir
    contagem = {"coletar": 0}
    fonte = m.fontes[0]
    fonte.conector.tem_novidade = lambda: False
    original = fonte.conector.coletar

    def coletar():
        contagem["coletar"] += 1
        return original()
    fonte.conector.coletar = coletar
    fonte.proxima = 0
    m.conferir_fontes()
    assert contagem["coletar"] == 0                     # sem novidade: não baixa de novo
    fonte.conector.tem_novidade = lambda: True
    fonte.proxima = 0
    m.conferir_fontes()
    assert contagem["coletar"] == 1


def test_empresa_desligada_nao_monta_conectores(cfg):
    cfg["demo"] = False
    cfg["empresas"] = [{"nome": "Outra Empresa", "ativa": False, "cor": "#fff",
                        "conectores": [{"tipo": "microsoft", "client_id": "x"}]}]
    from pixeldigest import connectors
    conectores, erros = connectors.montar(cfg)
    assert conectores == [] and erros == []


# ---------- tela responsiva ("media queries") ----------
def test_orientacao_automatica_segue_a_janela():
    from pixeldigest.ui import tela
    assert tela.orientacao({"orientacao": "automatica"}, (1920, 1080)) == "horizontal"
    assert tela.orientacao({"orientacao": "automatica"}, (1080, 1920)) == "vertical"
    assert tela.orientacao({"orientacao": "vertical"}, (1920, 1080)) == "vertical"


def test_viewport_converte_clique_da_janela_para_tela_logica():
    from pixeldigest.ui import tela
    v = tela.Viewport()
    v.ajustar((720, 1280), (1080, 1920))                 # vertical ampliada 1,5x
    assert v.para_logico((540, 960)) == (360, 640)
    v.ajustar((1280, 720), (1280, 1000))                 # sobra faixa preta em cima e embaixo
    assert v.oy == 140 and v.para_logico((0, 140)) == (0, 0)


def test_cena_vertical_e_ceu_cinza_com_chuva():
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    from pixeldigest.ui.scene import Cena
    pygame.init()
    c = Cena(180, 320)
    assert c.draw(datetime(2026, 11, 7, 12, 0)).get_size() == (180, 320)
    c.definir_clima(preset="chuva")
    c.vis = dict(c.alvo)
    assert c.cobertura == 1.0                            # chuva fecha o céu: sem sol e sem azul
