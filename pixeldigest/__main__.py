"""Ponto de entrada: python -m pixeldigest [opções]

    python -m pixeldigest                 abre a tela com as suas contas (config.yaml + .env)
    python -m pixeldigest --demo          tela com dados de exemplo (para GitHub e apresentação)
    python -m pixeldigest --headless      sem tela: só gatilhos + notificações (ex.: num servidor)
    python -m pixeldigest login           faz o login OAuth do Google e da Microsoft (uma vez)
    python -m pixeldigest testar          manda uma notificação de teste para Discord e celular
    python -m pixeldigest resumo          gera o resumo agora, salva o JSON e envia
"""
import argparse
import logging
import os
import sys
import time
from datetime import datetime, timedelta

from . import config


def preparar_log():
    config.DATA.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(config.DATA / "pixeldigest.log", encoding="utf-8"),
                  logging.StreamHandler(sys.stdout)])


_trava = None


def ja_esta_aberto(porta=47391):
    """Impede duas cópias abertas (cada uma gasta RAM e faz as mesmas chamadas de API).

    A primeira cópia "ocupa" uma porta local; a segunda não consegue e desiste.
    """
    import socket
    global _trava
    _trava = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):          # Windows: ninguém mais pode usar a porta
        _trava.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    try:
        _trava.bind(("127.0.0.1", porta))
        _trava.listen(1)
        return False
    except OSError:
        return True


def avisar_ja_aberto():
    texto = "O PixelDigest já está aberto. Procure a janela na barra de tarefas."
    print(texto)
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, texto, "PixelDigest", 0x40)


def cmd_login(cfg):
    from . import connectors
    conectores, erros = connectors.montar(cfg)
    for e in erros:
        print("!", e)
    precisam = [c for c in conectores if c.precisa_login()]
    if not precisam:
        print("Nenhum login pendente.")
    for c in precisam:
        print(f"\n== Login: {c.nome} ==")
        c.login()
        print("ok!")


def cmd_testar(cfg):
    from .notify import Notificador
    n = Notificador(cfg)
    if not n.ativo():
        print("Configure DISCORD_WEBHOOK_URL e/ou NTFY_TOPIC no .env primeiro.")
        return
    print(n.enviar("🧪 Teste do PixelDigest", "Se você está lendo isso, as notificações funcionam!", "#ffcc4d", tags=["tada"]))


def cmd_resumo(cfg):
    from .core import Motor
    m = Motor(cfg)
    m.bom_dia()
    time.sleep(3)      # dá tempo das notificações saírem
    print("Resumo salvo em", config.DATA)


def headless(cfg):
    from .core import Motor
    m = Motor(cfg)
    m.start()
    print("PixelDigest rodando sem tela. Ctrl+C para sair.")
    try:
        while True:
            tipo, dados = m.eventos.get()
            if tipo == "resumo":
                r = dados["resumo"]
                print(f"[{datetime.now():%H:%M}] resumo: {len(r.itens)} itens, {len(r.erros)} erros")
            elif tipo != "clima":
                print(f"[{datetime.now():%H:%M}] {tipo}: {dados.get('texto', '')}")
    except KeyboardInterrupt:
        m.parar.set()


def screenshot(cfg, args):
    """Gera uma imagem da tela sem abrir janela (usado para as imagens do README)."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import pygame
    from .core import Motor
    from .meetings import rotulo
    from .ui import effects
    from .ui.app import App
    pygame.init()
    tamanho = tuple(map(int, (args.tamanho or "1280x720").lower().split("x")))
    tela = pygame.display.set_mode(tamanho)
    cfg["tela"]["orientacao"] = "automatica"          # a forma da imagem decide o layout
    motor = Motor(cfg)
    if not args.clima:
        motor.atualizar_clima()
    motor.atualizar_resumo(avisar_urgentes=False)
    app = App(cfg, motor, tela)
    import time as _t
    _t.sleep(1.5)                    # deixa o resumo dos e-mails (em segundo plano) terminar
    app.receber()
    app.preset = args.clima
    app.cena.definir_clima(preset=args.clima)
    if args.clima:
        app.cena.vis = dict(app.cena.alvo)              # clima já "assentado" na imagem
    app.pagina = args.pagina or "inicio"
    if args.hora:
        h, m = map(int, args.hora.split(":"))
        alvo = datetime.now().astimezone().replace(hour=h, minute=m)
        app.desloc_horas = (alvo - datetime.now().astimezone()).total_seconds() / 3600
    app.agora = lambda: datetime.now().astimezone() + timedelta(hours=app.desloc_horas)
    quadros = 120
    if args.efeito == "bom_dia":
        app.efeitos.append(effects.BomDia(cfg["usuario"]["nome"], len(motor.resumo.itens)))
        quadros = 75
    elif args.efeito == "fim":
        app.cena.acender_janelas()
        app.efeitos.append(effects.FimDia())
        quadros = 80
    elif args.efeito == "agendado":
        h = motor.agendador.conector.horarios_livres("", 30, [])[0]
        app.efeitos.append(effects.Agendado("Ana", rotulo(h), "Reunião"))
        quadros = 45
    elif args.efeito == "alarme":
        app.efeitos.append(effects.Alarme("Alarme", "Hora de acordar!"))
        quadros = 20
    elif args.efeito == "proposta":
        motor.tratar_pedido({"chat_id": "x", "user_id": "y", "nome": "Beatriz Lima",
                             "texto": "Oi! Podemos marcar uma reunião essa semana pra alinhar o projeto?"})
        app.receber()
        app.toasts.clear()
    if args.aba is not None:
        if args.config:                      # imagem das Configurações com um config de exemplo
            config.ARQ_CONFIG = config.Path(args.config)
        app.abrir_config(primeira_vez=not config.existe())
        app.config_tela.aba = args.aba
        quadros = 3
    for _ in range(quadros):
        app.quadro(1 / 30)
    pygame.image.save(tela, args.shot)
    print("imagem salva em", args.shot)


def main():
    p = argparse.ArgumentParser(prog="pixeldigest", description="Resumo diário animado em pixel art")
    p.add_argument("comando", nargs="?", choices=["login", "testar", "resumo"], help="ação avulsa")
    p.add_argument("--demo", action="store_true", help="usa dados de exemplo (sem contas reais)")
    p.add_argument("--headless", action="store_true", help="roda sem tela")
    p.add_argument("--config", help="caminho do config.yaml")
    p.add_argument("--shot", help="salva uma imagem da tela e sai")
    p.add_argument("--clima", default=None, help="sol, nublado, chuva ou tempestade (com --shot)")
    p.add_argument("--hora", default=None, help="HH:MM mostrado no cenário (com --shot)")
    p.add_argument("--efeito", default=None, help="bom_dia, fim, agendado, alarme ou proposta (com --shot)")
    p.add_argument("--aba", type=int, default=None, help="número da aba das Configurações (com --shot)")
    p.add_argument("--tamanho", default=None, help="LxA da imagem, ex.: 720x1280 (com --shot)")
    p.add_argument("--pagina", default=None, help="inicio, resumo, emails ou agenda (com --shot)")
    args = p.parse_args()

    preparar_log()
    try:
        cfg = config.carregar(args.config, demo=args.demo)
    except config.ConfigError as exc:
        print("Erro na configuração:", exc)
        sys.exit(1)

    if args.comando == "login":
        return cmd_login(cfg)
    if args.comando == "testar":
        return cmd_testar(cfg)
    if args.comando == "resumo":
        return cmd_resumo(cfg)
    if args.shot:
        return screenshot(cfg, args)
    if ja_esta_aberto():
        return avisar_ja_aberto()
    if args.headless:
        return headless(cfg)

    import pygame
    from .core import Motor
    from .ui.app import App
    pygame.init()
    motor = Motor(cfg)
    motor.start()
    app = App(cfg, motor, demo_forcado=args.demo)          # a janela segue Configurações > Tela
    if not config.existe() and not args.demo:
        app.abrir_config(primeira_vez=True)      # primeira vez: abre direto nas Configurações
    app.rodar()
    pygame.quit()


if __name__ == "__main__":
    main()
