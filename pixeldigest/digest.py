"""Monta o resumo do dia: coleta de todas as fontes, ordena e formata.

Se uma fonte falhar (Slack fora do ar, token vencido...), o resumo sai mesmo
assim com as outras, e a falha aparece na lista de erros.
"""
import json
import logging
from datetime import datetime, timedelta

from . import net
from .config import DATA, ConfigError
from .models import ALTA, URGENTE, Digest, Item

log = logging.getLogger(__name__)
ICONES = {"tarefa": "☑", "mensagem": "💬", "email": "✉", "evento": "📅"}


def ordenar(itens):
    """Mais urgente primeiro; empate: o que acontece/vence antes."""
    longe = datetime.max.replace(tzinfo=None)
    return sorted(itens, key=lambda i: (-i.prioridade, i.quando.replace(tzinfo=None) if i.quando else longe))


def coletar(conectores, clima=None):
    itens, erros = [], []
    for c in conectores:
        try:
            itens += c.coletar()
        except (net.ApiError, ConfigError) as exc:
            erros.append(f"{c.nome}: {exc}")
            log.warning("fonte com erro: %s", exc)
        except Exception as exc:  # nunca deixa uma fonte derrubar o resumo inteiro
            log.exception("erro inesperado em %s", c.nome)
            erros.append(f"{c.nome}: erro inesperado ({exc})")
    return Digest(gerado_em=datetime.now(), itens=ordenar(itens), clima=clima, erros=erros)


def quando_txt(dt, agora):
    if not dt:
        return ""
    dias = (dt.date() - agora.date()).days
    if dias == 0:
        return dt.strftime("%H:%M")
    if dias == 1:
        return "amanhã " + dt.strftime("%H:%M")
    if dias == -1:
        return "ontem"
    return dt.strftime("%d/%m")


def linha(item, agora):
    marca = "‼️ " if item.prioridade >= URGENTE else ("❗ " if item.prioridade >= ALTA else "")
    quando = quando_txt(item.quando, agora)
    quando = f" ({quando})" if quando else ""
    return f"{marca}{ICONES.get(item.tipo, '•')} {item.titulo}{quando}"


def texto_resumo(digest, nome, por_empresa=4):
    """Texto para Discord e celular. Devolve (título, corpo, campos por empresa)."""
    agora = datetime.now().astimezone()
    titulo = f"☀️ Bom dia, {nome}! Seu resumo de {agora:%d/%m}"
    partes = []
    if digest.clima:
        c = digest.clima
        partes.append(f"🌡️ {c.cidade}: {c.temperatura:.0f}°C, {c.descricao} "
                      f"(mín {c.minima:.0f}° / máx {c.maxima:.0f}°, chuva {c.prob_chuva}%)")
    urgentes = sum(1 for i in digest.itens if i.prioridade >= URGENTE)
    partes.append(f"📌 {len(digest.itens)} itens, {urgentes} urgentes")
    campos = []
    for empresa, itens in digest.por_empresa().items():
        linhas = [linha(i, agora) for i in itens[:por_empresa]]
        if len(itens) > por_empresa:
            linhas.append(f"... e mais {len(itens) - por_empresa}")
        campos.append((empresa, "\n".join(linhas)))
    if digest.erros:
        partes.append("⚠️ Fontes com problema: " + "; ".join(digest.erros))
    return titulo, "\n".join(partes), campos


def texto_fim(digest, nome):
    """Resumo das 18h: o que ficou para amanhã."""
    amanha = datetime.now().date() + timedelta(days=1)
    pendentes = [i for i in digest.itens if i.tipo == "tarefa"]
    eventos_amanha = [i for i in digest.itens if i.tipo == "evento" and i.quando and i.quando.date() == amanha]
    corpo = [f"✅ Expediente encerrado, {nome}! Bom descanso."]
    if pendentes:
        corpo.append(f"☑ {len(pendentes)} tarefas abertas: " + ", ".join(i.titulo for i in pendentes[:3]))
    if eventos_amanha:
        corpo.append("📅 Amanhã: " + ", ".join(f"{i.quando:%H:%M} {i.titulo}" for i in eventos_amanha[:4]))
    return "🌙 Fim do expediente", "\n".join(corpo)


def salvar(digest):
    """Grava o resumo em data/digest-AAAA-MM-DD.json (o 'artefato' de cada dia)."""
    caminho = DATA / f"digest-{digest.gerado_em:%Y-%m-%d}.json"
    caminho.write_text(json.dumps(digest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return caminho


def carregar_hoje():
    """O último resumo salvo hoje (para aparecer na hora ao abrir, antes da busca)."""
    caminho = DATA / f"digest-{datetime.now():%Y-%m-%d}.json"
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        itens = []
        for d in dados.get("itens", []):
            d["quando"] = datetime.fromisoformat(d["quando"]) if d.get("quando") else None
            itens.append(Item(**d))
        return Digest(gerado_em=datetime.fromisoformat(dados["gerado_em"]), itens=itens, erros=dados.get("erros", []))
    except (OSError, ValueError, KeyError, TypeError):
        return None


class Vistos:
    """Lembra quais itens urgentes já foram avisados, para não repetir notificação."""

    def __init__(self, arquivo=None):
        self.arquivo = arquivo or DATA / "vistos.json"
        try:
            self.chaves = set(json.loads(self.arquivo.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            self.chaves = set()

    def novos(self, itens, prioridade_minima=URGENTE):
        novos = [i for i in itens if i.prioridade >= prioridade_minima and i.chave() not in self.chaves]
        if novos:
            self.chaves.update(i.chave() for i in novos)
            self.arquivo.write_text(json.dumps(sorted(self.chaves)[-2000:]), encoding="utf-8")
        return novos
