# `pixeldigest/__main__.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/__main__.py)

É o ponto de entrada do programa. Quando alguém roda `python -m pixeldigest`, o Python procura o arquivo `__main__.py` dentro do pacote `pixeldigest` e executa ele. Aqui ficam: a leitura dos argumentos da linha de comando, o log, a trava contra duas cópias abertas e a escolha do modo (tela, demonstração, sem tela, login, teste, resumo ou captura de imagem).

### Linhas 1 a 9

```python
"""Ponto de entrada: python -m pixeldigest [opções]

    python -m pixeldigest                 abre a tela com as suas contas (config.yaml + .env)
    python -m pixeldigest --demo          tela com dados de exemplo (para GitHub e apresentação)
    python -m pixeldigest --headless      sem tela: só gatilhos + notificações (ex.: num servidor)
    python -m pixeldigest login           faz o login OAuth do Google e da Microsoft (uma vez)
    python -m pixeldigest testar          manda uma notificação de teste para Discord e celular
    python -m pixeldigest resumo          gera o resumo agora, salva o JSON e envia
"""
```

Docstring do módulo (texto entre três aspas no topo do arquivo). Não executa nada: serve de manual rápido e mostra os seis jeitos de rodar o programa. O `help()` do Python e editores como o VS Code mostram esse texto.

### Linha 10

```python
import argparse
```

Importa `argparse`, a biblioteca padrão do Python para ler argumentos da linha de comando (`--demo`, `--headless` etc.) e gerar a ajuda `-h` automaticamente.

### Linha 11

```python
import logging
```

Importa `logging`, a biblioteca padrão de registro de eventos. Usamos para gravar o que acontece num arquivo de log, o que ajuda a descobrir erros depois.

### Linha 12

```python
import os
```

Importa `os`, usado mais abaixo para mudar uma variável de ambiente (`SDL_VIDEODRIVER`) no modo de captura de imagem.

### Linha 13

```python
import sys
```

Importa `sys`, usado para saber o sistema operacional (`sys.platform`), escrever na saída padrão (`sys.stdout`) e encerrar o programa com código de erro (`sys.exit`).

### Linha 14

```python
import time
```

Importa `time`, usado para pausar alguns segundos (`time.sleep`) no comando `resumo`.

### Linha 15

```python
from datetime import datetime, timedelta
```

Importa as classes `datetime` (data e hora) e `timedelta` (diferença de tempo, ex.: 3 horas) do módulo padrão `datetime`.

### Linha 17

```python
from . import config
```

Importa o nosso módulo `config.py` do mesmo pacote. O ponto em `from . import` significa "deste pacote" (import relativo).

### Linha 20

```python
def preparar_log():
```

Define a função `preparar_log`, que configura o registro de eventos do programa.

### Linha 21

```python
    config.DATA.mkdir(exist_ok=True)
```

Cria a pasta `data/` se ela ainda não existir. `config.DATA` é um `Path` (caminho) definido em `config.py`. `exist_ok=True` evita erro se a pasta já existir.

### Linhas 22 a 25

```python
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(config.DATA / "pixeldigest.log", encoding="utf-8"),
                  logging.StreamHandler(sys.stdout)])
```

Configura o `logging` uma vez para o programa todo:
- `level=logging.INFO`: registra mensagens de nível INFO para cima (INFO, WARNING, ERROR), ignorando DEBUG.
- `format=...`: cada linha do log terá data e hora (`asctime`), nível (`levelname`), nome do módulo que escreveu (`name`) e a mensagem.
- `handlers=[...]`: para onde as mensagens vão. O `FileHandler` grava em `data/pixeldigest.log` (em UTF-8, para os acentos saírem certos) e o `StreamHandler(sys.stdout)` mostra também no terminal.

### Linha 28

```python
_trava = None
```

Variável global que vai guardar o socket da trava de instância única. Precisa ser global porque, se o socket fosse uma variável local, o Python poderia apagá-lo quando a função terminasse e a porta seria liberada.

### Linha 31

```python
def ja_esta_aberto(porta=47391):
```

Define `ja_esta_aberto`, que devolve `True` se já existe outra cópia do PixelDigest rodando. A porta 47391 é um número qualquer, pouco usado, escolhido para o programa.

### Linhas 32 a 35

```python
    """Impede duas cópias abertas (cada uma gasta RAM e faz as mesmas chamadas de API).

    A primeira cópia "ocupa" uma porta local; a segunda não consegue e desiste.
    """
```

Docstring explicando a ideia: só um programa por vez consegue "ocupar" uma porta TCP no computador. A primeira cópia ocupa; a segunda tenta, falha e sabe que já existe outra aberta. Isso evita gastar RAM em dobro e repetir as mesmas chamadas de API.

### Linha 36

```python
    import socket
```

Importa `socket` (comunicação de rede de baixo nível) só dentro da função, porque ele só é necessário aqui.

### Linha 37

```python
    global _trava
```

Avisa ao Python que a função vai alterar a variável global `_trava`, e não criar uma variável local com o mesmo nome.

### Linha 38

```python
    _trava = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
```

Cria um socket TCP (`SOCK_STREAM`) de IPv4 (`AF_INET`).

### Linhas 39 a 40

```python
    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):          # Windows: ninguém mais pode usar a porta
        _trava.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
```

No Windows existe a opção `SO_EXCLUSIVEADDRUSE`, que impede qualquer outro programa de usar a mesma porta ao mesmo tempo. `hasattr` confere se a opção existe (no Linux ela não existe, e a linha 40 é pulada). `setsockopt(..., 1)` liga a opção.

### Linhas 41 a 44

```python
    try:
        _trava.bind(("127.0.0.1", porta))
        _trava.listen(1)
        return False
```

Tenta "ocupar" a porta só no endereço local `127.0.0.1` (não abre nada para a internet). `bind` reserva a porta e `listen(1)` deixa ela em modo de escuta. Se deu certo, esta é a primeira cópia e a função devolve `False` (não estava aberto).

### Linhas 45 a 46

```python
    except OSError:
        return True
```

Se o `bind` falhar com `OSError` (porta já ocupada), outra cópia está rodando: devolve `True`.

### Linha 49

```python
def avisar_ja_aberto():
```

Define a função que avisa o usuário de que o programa já está aberto.

### Linha 50

```python
    texto = "O PixelDigest já está aberto. Procure a janela na barra de tarefas."
```

Texto do aviso.

### Linha 51

```python
    print(texto)
```

Mostra o aviso no terminal.

### Linhas 52 a 54

```python
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, texto, "PixelDigest", 0x40)
```

Se estiver no Windows (`win32`), também mostra uma caixa de mensagem nativa. `ctypes` permite chamar funções de DLLs do Windows; `MessageBoxW` é a função da `user32.dll` que abre a caixa. O `0x40` é o código do ícone de informação. `None` quer dizer que a caixa não pertence a nenhuma janela.

### Linha 57

```python
def cmd_login(cfg):
```

Define o comando `login`, que faz o login OAuth (Google e Microsoft) pelo terminal.

### Linha 58

```python
    from . import connectors
```

Importa o pacote `connectors` só quando o comando é usado (deixa a abertura do programa mais rápida).

### Linha 59

```python
    conectores, erros = connectors.montar(cfg)
```

`connectors.montar(cfg)` cria um objeto conector para cada serviço configurado e devolve também a lista de erros (ex.: chave faltando). A atribuição `a, b = ...` desempacota as duas coisas.

### Linhas 60 a 61

```python
    for e in erros:
        print("!", e)
```

Mostra cada erro no terminal, com um `!` na frente.

### Linha 62

```python
    precisam = [c for c in conectores if c.precisa_login()]
```

List comprehension: monta a lista só com os conectores que ainda precisam de login (`precisa_login()` devolve `True`).

### Linhas 63 a 64

```python
    if not precisam:
        print("Nenhum login pendente.")
```

Se a lista estiver vazia, avisa que não há nada a fazer.

### Linhas 65 a 68

```python
    for c in precisam:
        print(f"\n== Login: {c.nome} ==")
        c.login()
        print("ok!")
```

Para cada conector que precisa de login: mostra o nome, chama `login()` (que abre o navegador ou mostra o código da Microsoft) e escreve "ok!" quando termina.

### Linha 71

```python
def cmd_testar(cfg):
```

Define o comando `testar`, que manda uma notificação de teste.

### Linha 72

```python
    from .notify import Notificador
```

Importa a classe `Notificador` de `notify.py`.

### Linha 73

```python
    n = Notificador(cfg)
```

Cria o notificador com a configuração.

### Linhas 74 a 76

```python
    if not n.ativo():
        print("Configure DISCORD_WEBHOOK_URL e/ou NTFY_TOPIC no .env primeiro.")
        return
```

Se nem o Discord nem o celular estiverem configurados (`ativo()` devolve `False`), explica o que falta e sai da função com `return`.

### Linha 77

```python
    print(n.enviar("🧪 Teste do PixelDigest", "Se você está lendo isso, as notificações funcionam!", "#ffcc4d", tags=["tada"]))
```

Envia a notificação de teste (título, texto, cor em hexadecimal e uma tag que vira emoji no ntfy) e mostra no terminal o resultado de cada canal.

### Linha 80

```python
def cmd_resumo(cfg):
```

Define o comando `resumo`, que gera o resumo do dia na hora.

### Linha 81

```python
    from .core import Motor
```

Importa a classe `Motor` de `core.py`, que é quem busca os dados e dispara as ações.

### Linha 82

```python
    m = Motor(cfg)
```

Cria o motor.

### Linha 83

```python
    m.bom_dia()
```

Chama `bom_dia()`, a mesma ação das 07:00: busca tudo, monta o resumo, salva o JSON e envia as notificações.

### Linha 84

```python
    time.sleep(3)      # dá tempo das notificações saírem
```

Espera 3 segundos porque as notificações saem em threads (em paralelo); se o programa terminasse na hora, elas poderiam ser cortadas.

### Linha 85

```python
    print("Resumo salvo em", config.DATA)
```

Mostra onde o resumo foi salvo.

### Linha 88

```python
def headless(cfg):
```

Define o modo `headless` (sem tela), útil para rodar num servidor.

### Linhas 89 a 91

```python
    from .core import Motor
    m = Motor(cfg)
    m.start()
```

Importa e cria o `Motor` e chama `start()`, que liga a thread de segundo plano com os gatilhos.

### Linha 92

```python
    print("PixelDigest rodando sem tela. Ctrl+C para sair.")
```

Avisa no terminal que está rodando e como sair.

### Linhas 93 a 94

```python
    try:
        while True:
```

Laço infinito dentro de um `try`, para conseguir capturar o Ctrl+C.

### Linha 95

```python
            tipo, dados = m.eventos.get()
```

Espera (bloqueia) até o motor colocar um evento na fila `eventos`. Cada evento é uma tupla `(tipo, dados)`.

### Linhas 96 a 98

```python
            if tipo == "resumo":
                r = dados["resumo"]
                print(f"[{datetime.now():%H:%M}] resumo: {len(r.itens)} itens, {len(r.erros)} erros")
```

Se o evento for um resumo novo, mostra a hora (`%H:%M`), quantos itens e quantos erros ele teve. A f-string com `{datetime.now():%H:%M}` formata a hora direto dentro do texto.

### Linhas 99 a 100

```python
            elif tipo != "clima":
                print(f"[{datetime.now():%H:%M}] {tipo}: {dados.get('texto', '')}")
```

Para os outros eventos (menos o clima, que chega toda hora e poluiria o terminal), mostra o tipo e o texto. `dados.get('texto', '')` devolve vazio se o evento não tiver texto.

### Linhas 101 a 102

```python
    except KeyboardInterrupt:
        m.parar.set()
```

Ctrl+C gera `KeyboardInterrupt`. Aí ligamos o sinal `parar` (um `threading.Event`) para o motor encerrar a thread dele.

### Linha 105

```python
def screenshot(cfg, args):
```

Define o modo de captura de tela (`--shot`), usado para gerar as imagens do README sem abrir janela.

### Linha 106

```python
    """Gera uma imagem da tela sem abrir janela (usado para as imagens do README)."""
```

Docstring dizendo para que a função serve.

### Linha 107

```python
    os.environ["SDL_VIDEODRIVER"] = "dummy"
```

Diz ao SDL (a biblioteca por trás do pygame) para usar um vídeo "falso" (`dummy`). Assim o pygame desenha na memória sem abrir janela nenhuma. Precisa vir antes do `import pygame`.

### Linhas 108 a 112

```python
    import pygame
    from .core import Motor
    from .meetings import rotulo
    from .ui import effects
    from .ui.app import App
```

Importa o que a captura precisa: o pygame, o `Motor`, a função `rotulo` (formata um horário de reunião), o módulo de animações `effects` e a classe `App` (a tela).

### Linha 113

```python
    pygame.init()
```

Inicializa os módulos do pygame (vídeo, fontes etc.).

### Linha 114

```python
    tamanho = tuple(map(int, (args.tamanho or "1280x720").lower().split("x")))
```

Lê o tamanho pedido em `--tamanho` (padrão "1280x720"), passa para minúsculas, separa no "x" e converte cada parte em inteiro. `tuple(map(int, ...))` vira `(1280, 720)`.

### Linha 115

```python
    tela = pygame.display.set_mode(tamanho)
```

Cria a "janela" (no driver falso) com esse tamanho.

### Linha 116

```python
    cfg["tela"]["orientacao"] = "automatica"          # a forma da imagem decide o layout
```

Força a orientação automática: se a imagem for mais alta que larga, o layout fica vertical.

### Linha 117

```python
    motor = Motor(cfg)
```

Cria o motor (não chama `start`, porque aqui não precisa da thread).

### Linhas 118 a 119

```python
    if not args.clima:
        motor.atualizar_clima()
```

Se não foi pedido um clima de mentira (`--clima`), busca o clima real.

### Linha 120

```python
    motor.atualizar_resumo(avisar_urgentes=False)
```

Busca os dados e monta o resumo, sem disparar avisos de urgência (é só uma foto).

### Linha 121

```python
    app = App(cfg, motor, tela)
```

Cria a tela do app, desenhando na superfície criada na linha 115.

### Linhas 122 a 123

```python
    import time as _t
    _t.sleep(1.5)                    # deixa o resumo dos e-mails (em segundo plano) terminar
```

Espera 1,5 segundo para o resumo dos e-mails, que roda em outra thread, terminar.

### Linha 124

```python
    app.receber()
```

`receber()` lê os eventos que o motor colocou na fila e atualiza a tela.

### Linhas 125 a 126

```python
    app.preset = args.clima
    app.cena.definir_clima(preset=args.clima)
```

Guarda o clima escolhido e manda o cenário usar esse clima.

### Linhas 127 a 128

```python
    if args.clima:
        app.cena.vis = dict(app.cena.alvo)              # clima já "assentado" na imagem
```

Se um clima foi escolhido, copia os valores-alvo direto para os valores visíveis. Normalmente o cenário muda aos poucos (transição suave); na foto queremos o clima já "assentado".

### Linha 129

```python
    app.pagina = args.pagina or "inicio"
```

Escolhe a aba mostrada (`--pagina`), ou "inicio" se não foi passada.

### Linhas 130 a 133

```python
    if args.hora:
        h, m = map(int, args.hora.split(":"))
        alvo = datetime.now().astimezone().replace(hour=h, minute=m)
        app.desloc_horas = (alvo - datetime.now().astimezone()).total_seconds() / 3600
```

Se foi passada uma hora (`--hora 20:30`), calcula quantas horas faltam ou sobram até ela e guarda em `desloc_horas`. O cenário então desenha o céu daquela hora.

### Linha 134

```python
    app.agora = lambda: datetime.now().astimezone() + timedelta(hours=app.desloc_horas)
```

Troca a função `agora` do app por uma `lambda` (função anônima de uma linha) que soma esse deslocamento à hora real.

### Linha 135

```python
    quadros = 120
```

Quantidade padrão de quadros a desenhar antes de tirar a foto (120 quadros = 4 s a 30 quadros por segundo), para as animações chegarem num ponto bonito.

### Linhas 136 a 138

```python
    if args.efeito == "bom_dia":
        app.efeitos.append(effects.BomDia(cfg["usuario"]["nome"], len(motor.resumo.itens)))
        quadros = 75
```

Se o efeito pedido for "bom_dia", adiciona a animação de bom dia com o nome do usuário e o número de itens, e tira a foto no quadro 75.

### Linhas 139 a 142

```python
    elif args.efeito == "fim":
        app.cena.acender_janelas()
        app.efeitos.append(effects.FimDia())
        quadros = 80
```

Efeito "fim": acende as janelas dos prédios e adiciona a animação de fim do expediente.

### Linhas 143 a 146

```python
    elif args.efeito == "agendado":
        h = motor.agendador.conector.horarios_livres("", 30, [])[0]
        app.efeitos.append(effects.Agendado("Ana", rotulo(h), "Reunião"))
        quadros = 45
```

Efeito "agendado": pega o primeiro horário livre do conector de agenda (da demonstração) e mostra a animação de reunião agendada com a Ana.

### Linhas 147 a 149

```python
    elif args.efeito == "alarme":
        app.efeitos.append(effects.Alarme("Alarme", "Hora de acordar!"))
        quadros = 20
```

Efeito "alarme": mostra a animação do alarme do celular.

### Linhas 150 a 154

```python
    elif args.efeito == "proposta":
        motor.tratar_pedido({"chat_id": "x", "user_id": "y", "nome": "Beatriz Lima",
                             "texto": "Oi! Podemos marcar uma reunião essa semana pra alinhar o projeto?"})
        app.receber()
        app.toasts.clear()
```

Efeito "proposta": simula um pedido de reunião chegando no Teams. O motor trata o pedido (procura horários livres), a tela recebe o resultado e os avisos pequenos (toasts) são apagados para não cobrir a imagem.

### Linhas 155 a 160

```python
    if args.aba is not None:
        if args.config:                      # imagem das Configurações com um config de exemplo
            config.ARQ_CONFIG = config.Path(args.config)
        app.abrir_config(primeira_vez=not config.existe())
        app.config_tela.aba = args.aba
        quadros = 3
```

Se foi pedida uma aba das Configurações (`--aba`): opcionalmente usa outro config.yaml de exemplo (`--config`), abre a tela de Configurações, escolhe a aba e desenha só 3 quadros.

### Linhas 161 a 162

```python
    for _ in range(quadros):
        app.quadro(1 / 30)
```

Desenha os quadros. `1 / 30` é o tempo de cada quadro em segundos (30 por segundo).

### Linhas 163 a 164

```python
    pygame.image.save(tela, args.shot)
    print("imagem salva em", args.shot)
```

Salva a superfície como imagem PNG no caminho de `--shot` e avisa.

### Linha 167

```python
def main():
```

Define `main`, a função principal.

### Linha 168

```python
    p = argparse.ArgumentParser(prog="pixeldigest", description="Resumo diário animado em pixel art")
```

Cria o leitor de argumentos com nome e descrição (aparecem no `-h`).

### Linha 169

```python
    p.add_argument("comando", nargs="?", choices=["login", "testar", "resumo"], help="ação avulsa")
```

Argumento posicional opcional (`nargs="?"`): pode ser `login`, `testar` ou `resumo`. `choices` recusa qualquer outra palavra.

### Linhas 170 a 171

```python
    p.add_argument("--demo", action="store_true", help="usa dados de exemplo (sem contas reais)")
    p.add_argument("--headless", action="store_true", help="roda sem tela")
```

Opções liga/desliga: `store_true` faz `args.demo` valer `True` quando `--demo` aparece.

### Linhas 172 a 179

```python
    p.add_argument("--config", help="caminho do config.yaml")
    p.add_argument("--shot", help="salva uma imagem da tela e sai")
    p.add_argument("--clima", default=None, help="sol, nublado, chuva ou tempestade (com --shot)")
    p.add_argument("--hora", default=None, help="HH:MM mostrado no cenário (com --shot)")
    p.add_argument("--efeito", default=None, help="bom_dia, fim, agendado, alarme ou proposta (com --shot)")
    p.add_argument("--aba", type=int, default=None, help="número da aba das Configurações (com --shot)")
    p.add_argument("--tamanho", default=None, help="LxA da imagem, ex.: 720x1280 (com --shot)")
    p.add_argument("--pagina", default=None, help="inicio, resumo, emails ou agenda (com --shot)")
```

Opções com valor: caminho do config, arquivo da captura e os ajustes da captura (clima, hora, efeito, aba, tamanho e página). `type=int` converte o número da aba para inteiro.

### Linha 180

```python
    args = p.parse_args()
```

Lê de verdade os argumentos digitados (`sys.argv`) e devolve o objeto `args`.

### Linha 182

```python
    preparar_log()
```

Liga o log.

### Linhas 183 a 187

```python
    try:
        cfg = config.carregar(args.config, demo=args.demo)
    except config.ConfigError as exc:
        print("Erro na configuração:", exc)
        sys.exit(1)
```

Carrega a configuração. Se ela tiver algum problema (`ConfigError`, ex.: horário inválido), mostra a mensagem e encerra com código 1 (código diferente de 0 indica erro para o sistema).

### Linhas 189 a 196

```python
    if args.comando == "login":
        return cmd_login(cfg)
    if args.comando == "testar":
        return cmd_testar(cfg)
    if args.comando == "resumo":
        return cmd_resumo(cfg)
    if args.shot:
        return screenshot(cfg, args)
```

Executa os comandos avulsos, se algum foi pedido. O `return` sai do `main` depois de cada um.

### Linhas 197 a 198

```python
    if ja_esta_aberto():
        return avisar_ja_aberto()
```

Se já existe outra cópia aberta, avisa e sai (não abre uma segunda janela).

### Linhas 199 a 200

```python
    if args.headless:
        return headless(cfg)
```

Modo sem tela.

### Linhas 202 a 204

```python
    import pygame
    from .core import Motor
    from .ui.app import App
```

Importa o pygame, o motor e a tela só agora, porque os modos acima não precisam deles.

### Linha 205

```python
    pygame.init()
```

Inicializa o pygame.

### Linhas 206 a 207

```python
    motor = Motor(cfg)
    motor.start()
```

Cria o motor e liga a thread de segundo plano.

### Linha 208

```python
    app = App(cfg, motor, demo_forcado=args.demo)          # a janela segue Configurações > Tela
```

Cria a tela. `demo_forcado` indica que o `--demo` veio da linha de comando. O tamanho da janela segue o que está em Configurações > Tela.

### Linhas 209 a 210

```python
    if not config.existe() and not args.demo:
        app.abrir_config(primeira_vez=True)      # primeira vez: abre direto nas Configurações
```

Na primeira vez (sem config.yaml) e fora da demonstração, a tela já abre nas Configurações.

### Linha 211

```python
    app.rodar()
```

`rodar()` é o laço principal da tela: só termina quando a janela é fechada.

### Linha 212

```python
    pygame.quit()
```

Encerra o pygame e libera a janela.

### Linhas 215 a 216

```python
if __name__ == "__main__":
    main()
```

Este `if` só é verdadeiro quando o arquivo é executado diretamente (não importado por outro). Aí chama o `main()`.
