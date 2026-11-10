"""Classe base dos conectores.

Um conector sabe falar com UM serviço de UMA empresa e devolve uma lista de Item.
Para adicionar um serviço novo: crie uma classe filha, implemente coletar() e
registre o tipo em connectors/__init__.py.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


class Conector:
    tipo = "base"

    def __init__(self, empresa, opcoes, cfg):
        self.empresa = empresa            # nome da empresa (ex.: "Minha Empresa")
        self.opcoes = opcoes              # bloco do conector no config.yaml
        self.cfg = cfg                    # configuração inteira
        self.fuso = ZoneInfo(cfg["usuario"]["fuso"])
        self.client = None                # os testes trocam por um httpx.Client falso

    def opcao(self, nome, obrigatorio=True):
        """Lê uma opção do conector.

        Segredos vêm do .env (o config guarda só o nome da variável em '<nome>_env');
        o resto vem direto do config.yaml.
        """
        from ..config import ConfigError, env
        if f"{nome}_env" in self.opcoes:
            return env(self.opcoes[f"{nome}_env"], obrigatorio)
        valor = str(self.opcoes.get(nome) or "").strip()
        if obrigatorio and not valor:
            raise ConfigError(f"falta '{nome}' do {self.tipo} (preencha em Configurações > Chaves de API)")
        return valor

    @property
    def nome(self):
        return f"{self.empresa} / {self.tipo}"

    def agora(self):
        return datetime.now(self.fuso)

    def inicio_do_dia(self):
        return self.agora().replace(hour=0, minute=0, second=0, microsecond=0)

    def fim_de_amanha(self):
        return self.inicio_do_dia() + timedelta(days=2)

    def coletar(self):
        """Devolve list[Item]. Pode levantar net.ApiError ou ConfigError."""
        raise NotImplementedError

    def precisa_login(self):
        """Conectores com OAuth (Google, Microsoft) respondem True quando falta o login."""
        return False

    def login(self):
        """Login interativo (roda pelo comando: python -m pixeldigest login)."""
