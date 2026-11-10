# `pixeldigest/core.py`

[Voltar ao índice](README.md) · [Ver o arquivo](../../pixeldigest/core.py)

O Motor é o coração da automação. Ele roda numa thread separada da tela e liga cada gatilho à sua ação: horários, novidades nas fontes, alarme do celular e comandos digitados. Conversa com a tela por duas filas.

### Linhas 1 a 16

```python
"""O motor: roda em segundo plano, liga os gatilhos às ações.

    gatilho (horário, novidade numa fonte, alarme, comando na tela)
        -> processamento (coletar, ordenar, resumir e-mails, achar horário livre)
            -> saída (evento para a tela + Discord + celular + arquivo JSON)

Para não repetir requisições à toa:
- ao abrir, mostra na hora o último resumo salvo e faz UMA busca completa;
- depois, cada fonte tem o seu ritmo (INTERVALOS) e só baixa de novo quando tem
  novidade (o Gmail confere com uma chamada barata; o Slack só pega mensagens novas);
- trocar de tela, abrir as Configurações ou voltar para o resumo não busca nada;
- o botão Atualizar força uma busca completa.

A tela (ui/app.py) e o modo sem tela (--headless) recebem os mesmos eventos pela
fila `eventos`, como tuplas (tipo, dados).
"""
```

Docstring com o fluxo gatilho, processamento e saída, e as regras para não repetir requisições: uma busca completa ao abrir, depois cada fonte no seu ritmo e só quando há novidade. Trocar de aba não busca nada; o botão Atualizar força a busca completa.

### Linha 17

```python
import json
```

Importa `json` (arquivo dos itens apagados).

### Linha 18

```python
import logging
```

Importa `logging`.

### Linha 19

```python
import os
```

Importa `os` para ler a chave do Claude da variável de ambiente.

### Linha 20

```python
import queue
```

Importa `queue`. Uma `queue.Queue` é uma fila segura para várias threads: uma coloca (`put`) e outra tira (`get`), sem precisar de trava manual.

### Linha 21

```python
import threading
```

Importa `threading` para a thread do motor e as threads de envio.

### Linha 22

```python
import time
```

Importa `time` para controlar quando cada fonte será conferida (`time.time()` devolve os segundos desde 1970).

### Linha 23

```python
from datetime import datetime
```

Importa `datetime`.

### Linha 25

```python
from . import connectors, digest, net, resumo_email
```

Importa nossos módulos: conectores, resumo, rede e resumo de e-mails.

### Linha 26

```python
from .config import DATA, ConfigError
```

Importa a pasta `data/` e o erro de configuração.

### Linha 27

```python
from .connectors import weather
```

Importa o conector de clima.

### Linha 28

```python
from .connectors.demo import pedido_demo
```

Importa um pedido de reunião de exemplo, usado na demonstração.

### Linha 29

```python
from .meetings import Agendador, eh_pedido, rotulo
```

Importa do agendador: a classe `Agendador`, a função que reconhece pedido de reunião e a que formata um horário.

### Linha 30

```python
from .notify import Notificador
```

Importa o notificador (Discord e ntfy).

### Linha 31

```python
from .phone import OuvinteAlarme
```

Importa o ouvinte do alarme do celular.

### Linha 32

```python
from .scheduler import Agenda, Diario, Intervalo
```

Importa as classes do agendador de tarefas.

### Linha 34

```python
log = logging.getLogger(__name__)
```

Logger do módulo.

### Linhas 36 a 37

```python
# De quanto em quanto tempo (segundos) cada tipo de fonte é conferido
INTERVALOS = {"gmail": 120, "slack": 600, "clickup": 900, "zoom": 1800, "microsoft": 900}
```

De quanto em quanto tempo cada tipo de fonte é conferido, em segundos: Gmail a cada 2 min (a conferência é barata), Slack 10 min, ClickUp 15 min, Zoom 30 min, Microsoft 15 min.

### Linhas 40 a 41

```python
class Fonte:
    """Um conector + o que ele trouxe da última vez + quando conferir de novo."""
```

Classe `Fonte`: junta um conector com o resultado da última busca e o horário da próxima conferência.

### Linhas 43 a 44

```python
    def __init__(self, conector):
        self.conector = conector
```

Guarda o conector.

### Linha 45

```python
        self.intervalo = INTERVALOS.get(conector.tipo, 900)
```

Pega o intervalo do tipo; se o tipo não estiver no dicionário, usa 15 min.

### Linha 46

```python
        self.proxima = time.time() + self.intervalo
```

Próxima conferência: agora mais o intervalo.

### Linha 47

```python
        self.itens = None          # None = ainda não buscou
```

`None` quer dizer que ainda não buscou nada (diferente de lista vazia, que quer dizer que buscou e não veio nada).

### Linha 48

```python
        self.erro = None
```

Último erro da fonte, se houver.

### Linha 51

```python
class Motor(threading.Thread):
```

O `Motor` herda de `threading.Thread`: ele é uma thread, e o código do método `run` roda em paralelo à tela.

### Linhas 52 a 53

```python
    def __init__(self, cfg):
        super().__init__(daemon=True, name="motor")
```

Construtor. `daemon=True` faz a thread morrer junto com o programa (não segura o processo aberto). O nome "motor" aparece em logs e ferramentas de depuração.

### Linha 54

```python
        self.cfg = cfg
```

Guarda a configuração.

### Linha 55

```python
        self.eventos = queue.Queue()      # motor -> tela
```

Fila de eventos do motor para a tela (resumo novo, clima, alarme, erro...).

### Linha 56

```python
        self.comandos = queue.Queue()     # tela -> motor
```

Fila de comandos da tela para o motor (atualizar, marcar reunião, limpar...).

### Linha 57

```python
        self.parar = threading.Event()
```

Sinal de parada. `Event` é uma bandeira compartilhada entre threads: começa desligada e `set()` liga.

### Linha 58

```python
        self.nome = cfg["usuario"]["nome"]
```

Nome do usuário, usado nas mensagens.

### Linha 59

```python
        self.conectores, self.erros_config = connectors.montar(cfg)
```

Monta os conectores das empresas ativas e guarda também os erros de configuração (ex.: chave faltando).

### Linha 60

```python
        self.fontes = [Fonte(c) for c in self.conectores]
```

Cria uma `Fonte` para cada conector.

### Linha 61

```python
        self.cores = {e["nome"]: e.get("cor", "#5ab0ff") for e in cfg["empresas"]}
```

Dicionário empresa para cor, usado na tela e nas notificações. É uma dict comprehension.

### Linha 62

```python
        self.notificador = Notificador(cfg)
```

Cria o notificador.

### Linha 63

```python
        self.vistos = digest.Vistos()
```

Cria o controle de itens já avisados.

### Linha 64

```python
        self.limpos = self._ler_limpos()      # itens que o usuário tirou do resumo
```

Carrega os itens que o usuário apagou do resumo.

### Linhas 65 a 67

```python
        self.clima = None
        self.resumo = None
        self.resumos_email = {}               # conta -> resumo dos e-mails (IA)
```

Estado atual: clima, resumo e o dicionário de resumos de e-mail por conta. Começam vazios.

### Linha 68

```python
        self.agendador = self._montar_agendador()
```

Cria o agendador de reuniões, se houver uma empresa com Microsoft e agendador ligado.

### Linha 69

```python
        self.ultima_checagem_teams = datetime.now().astimezone()
```

Momento da última conferência do Teams (para buscar só mensagens novas).

### Linha 70

```python
        self.alarme = OuvinteAlarme(self._alarme_tocou)
```

Cria o ouvinte do alarme e passa a função que deve ser chamada quando o alarme tocar (callback).

### Linha 72

```python
        self.agenda = Agenda()
```

Cria a agenda de tarefas por tempo.

### Linha 73

```python
        h = cfg["horarios"]
```

Atalho para os horários.

### Linha 74

```python
        self.agenda.adicionar(Diario("bom_dia", h["inicio_dia"], self.bom_dia))
```

Tarefa diária no horário de início do dia: chama `bom_dia`. Repare que a função é passada sem parênteses (`self.bom_dia`): passamos a função em si, para ser chamada depois.

### Linha 75

```python
        self.agenda.adicionar(Diario("fim_do_dia", h["fim_dia"], self.fim_do_dia))
```

Tarefa diária no fim do dia: chama `fim_do_dia`.

### Linha 76

```python
        self.agenda.adicionar(Intervalo("clima", 30 * 60, self.atualizar_clima))
```

A cada 30 min atualiza o clima.

### Linha 77

```python
        self.agenda.adicionar(Intervalo("fontes", 30, self.conferir_fontes))
```

A cada 30 s confere quais fontes chegaram na hora de ser conferidas.

### Linha 78

```python
        self.agenda.adicionar(Intervalo("pendentes", 5 * 60, self.notificador.reenviar_pendentes))
```

A cada 5 min tenta reenviar notificações que falharam.

### Linhas 79 a 80

```python
        if self.agendador and not cfg["demo"]:
            self.agenda.adicionar(Intervalo("teams", 60, self.checar_teams))
```

Se existe agendador e não é demonstração, confere o Teams a cada minuto atrás de pedidos de reunião.

### Linha 82

```python
    # ---------- montagem ----------
```

Comentário que separa a parte de montagem.

### Linhas 83 a 87

```python
    def _montar_agendador(self):
        for c in self.conectores:
            if c.tipo == "microsoft" and getattr(c, "usar", {}).get("agendador"):
                return Agendador(self.cfg, c)
        return None
```

Procura um conector Microsoft com o agendador ligado e cria o `Agendador` com ele. `getattr(c, "usar", {})` lê o atributo `usar` ou devolve `{}` se o conector não tiver. Se não achar, devolve `None`.

### Linhas 89 a 94

```python
    @staticmethod
    def _ler_limpos():
        try:
            return set(json.loads((DATA / "limpos.json").read_text(encoding="utf-8")))
        except (OSError, ValueError):
            return set()
```

`@staticmethod` indica um método que não usa `self`. Lê o arquivo `data/limpos.json` com as chaves dos itens apagados; se não existir ou estiver corrompido, começa com um conjunto vazio.

### Linhas 96 a 97

```python
    def _salvar_limpos(self):
        (DATA / "limpos.json").write_text(json.dumps(sorted(self.limpos)[-3000:]), encoding="utf-8")
```

Grava as chaves apagadas no arquivo, ordenadas, guardando só as últimas 3000.

### Linha 99

```python
    def limpar(self, chaves=None):
```

Tira itens do resumo: todos (sem argumento) ou só as chaves passadas.

### Linha 100

```python
        """Tira itens do resumo (todos, ou só as chaves passadas). Novidades continuam chegando."""
```

Docstring: novidades continuam chegando depois de limpar.

### Linhas 101 a 102

```python
        if not self.resumo:
            return
```

Se ainda não há resumo, não faz nada.

### Linha 103

```python
        chaves = set(chaves) if chaves else {i.chave() for i in self.resumo.itens}
```

Se vieram chaves, usa elas; senão, pega as chaves de todos os itens do resumo atual.

### Linha 104

```python
        self.limpos |= chaves
```

`|=` faz a união dos conjuntos: acrescenta as chaves novas às já apagadas.

### Linha 105

```python
        self._salvar_limpos()
```

Salva no arquivo, para continuar valendo se o programa reabrir.

### Linha 106

```python
        self.resumo.itens = [i for i in self.resumo.itens if i.chave() not in self.limpos]
```

Remove os itens apagados do resumo atual.

### Linha 107

```python
        self.emitir("resumo", resumo=self.resumo, cores=self.cores)
```

Avisa a tela para redesenhar o resumo.

### Linhas 109 a 110

```python
    def emitir(self, tipo, **dados):
        self.eventos.put((tipo, dados))
```

`emitir` coloca um evento na fila para a tela. `**dados` junta os argumentos nomeados num dicionário, ex.: `emitir("erro", texto="x")` vira `("erro", {"texto": "x"})`.

### Linha 112

```python
    def avisar(self, titulo, texto, cor="#5ab0ff", **kw):
```

Envia uma notificação para o Discord e o celular.

### Linha 113

```python
        """Notifica no Discord e no celular sem travar o motor."""
```

Docstring: sem travar o motor.

### Linhas 114 a 116

```python
        if self.notificador.ativo():
            threading.Thread(target=self.notificador.enviar, args=(titulo, texto, cor),
                             kwargs=kw, daemon=True).start()
```

Se algum canal estiver configurado, cria uma thread só para o envio (a rede pode demorar). `target` é a função, `args` os argumentos posicionais e `kwargs` os nomeados. `start()` começa a thread.

### Linha 118

```python
    # ---------- fontes ----------
```

Comentário da parte das fontes.

### Linha 119

```python
    def atualizar_fonte(self, fonte, forcar=False):
```

Busca uma fonte. Devolve `True` se algo mudou.

### Linha 120

```python
        """Busca uma fonte. Sem 'forcar', pergunta antes se há novidade. Devolve True se mudou algo."""
```

Docstring.

### Linha 121

```python
        c = fonte.conector
```

Atalho para o conector.

### Linhas 122 a 124

```python
        try:
            if not forcar and fonte.itens is not None and hasattr(c, "tem_novidade") and not c.tem_novidade():
                return False
```

Sem `forcar`, se a fonte já buscou antes e o conector sabe responder se há novidade (`hasattr` confere se o método existe), pergunta primeiro. Se não houver novidade, não busca e devolve `False`. É isso que economiza requisições.

### Linha 125

```python
            fonte.itens, fonte.erro = c.coletar(), None
```

Busca os itens e limpa o erro.

### Linhas 126 a 129

```python
        except (net.ApiError, ConfigError) as exc:
            fonte.erro = f"{c.nome}: {exc}"
            log.warning("fonte com erro: %s", fonte.erro)
            return True
```

Erro esperado: guarda a mensagem, registra no log e devolve `True` (o erro é uma mudança que deve aparecer na tela).

### Linhas 130 a 133

```python
        except Exception as exc:           # nunca deixa uma fonte derrubar o resto
            log.exception("erro inesperado em %s", c.nome)
            fonte.erro = f"{c.nome}: erro inesperado ({exc})"
            return True
```

Erro inesperado: mesmo tratamento, com o rastro completo no log.

### Linhas 134 a 135

```python
        if c.tipo == "gmail" and c.opcoes.get("resumo_ia", True):
            self.resumir_emails(c)
```

Se a fonte é Gmail e o resumo com IA não foi desligado, dispara o resumo dos e-mails.

### Linha 136

```python
        return True
```

Devolve `True` porque a fonte foi atualizada.

### Linha 138

```python
    def montar_resumo(self, avisar_urgentes=True):
```

Monta o resumo com o que as fontes já têm, sem buscar nada.

### Linha 139

```python
        """Junta o que cada fonte já tem (sem buscar nada) e manda para a tela."""
```

Docstring.

### Linha 140

```python
        itens = [i for f in self.fontes for i in (f.itens or []) if i.chave() not in self.limpos]
```

Junta os itens de todas as fontes (comprehension com dois `for`) tirando os que o usuário apagou. `f.itens or []` cobre a fonte que ainda não buscou.

### Linha 141

```python
        erros = self.erros_config + [f.erro for f in self.fontes if f.erro]
```

Junta os erros de configuração com os erros de cada fonte.

### Linha 142

```python
        self.resumo = digest.Digest(gerado_em=datetime.now(), itens=digest.ordenar(itens), clima=self.clima, erros=erros)
```

Cria o `Digest` com os itens ordenados.

### Linha 143

```python
        digest.salvar(self.resumo)
```

Salva o JSON do dia.

### Linha 144

```python
        self.emitir("resumo", resumo=self.resumo, cores=self.cores)
```

Manda o resumo para a tela.

### Linhas 145 a 146

```python
        if avisar_urgentes:
            novos = self.vistos.novos(self.resumo.itens)
```

Se for para avisar urgentes, pega só os urgentes que ainda não foram avisados.

### Linha 147

```python
            if novos:   # um aviso só com todos os urgentes novos (evita limite do Discord)
```

Se houver novos, manda um aviso só com todos eles. O comentário explica: um aviso por item estouraria o limite de mensagens do Discord.

### Linhas 148 a 149

```python
                agora = datetime.now().astimezone()
                texto = "\n".join(digest.linha(i, agora) for i in novos[:8])
```

Monta o texto com até 8 linhas.

### Linha 150

```python
                self.avisar(f"‼️ {len(novos)} novidade(s) urgente(s)", texto, "#ff5050", tags=["warning"], prioridade=4)
```

Envia com cor vermelha, tag de alerta e prioridade 4 (alta no ntfy, faz o celular tocar).

### Linhas 151 a 152

```python
                for item in novos[:3]:
                    self.emitir("toast", titulo=item.empresa, texto=item.titulo, cor=self.cores.get(item.empresa))
```

Mostra na tela um aviso pequeno (toast) para os três primeiros, com a cor da empresa.

### Linha 153

```python
        return self.resumo
```

Devolve o resumo.

### Linha 155

```python
    def atualizar_resumo(self, avisar_urgentes=True, forcar=True):
```

Busca completa em todas as fontes.

### Linha 156

```python
        """Busca completa em todas as fontes (ao abrir, no botão Atualizar e no bom dia)."""
```

Docstring: usada ao abrir, no botão Atualizar e no bom dia.

### Linhas 157 a 159

```python
        for f in self.fontes:
            self.atualizar_fonte(f, forcar)
            f.proxima = time.time() + f.intervalo
```

Atualiza cada fonte (forçando, por padrão) e reagenda a próxima conferência dela.

### Linha 160

```python
        return self.montar_resumo(avisar_urgentes)
```

Monta o resumo e devolve.

### Linha 162

```python
    def conferir_fontes(self):
```

Chamada a cada 30 segundos pela agenda.

### Linha 163

```python
        """A cada 30 s: confere só as fontes cujo tempo chegou e só remonta se algo mudou."""
```

Docstring.

### Linha 164

```python
        agora, mudou = time.time(), False
```

Pega a hora atual e começa com "nada mudou".

### Linhas 165 a 168

```python
        for f in self.fontes:
            if agora >= f.proxima:
                f.proxima = agora + f.intervalo
                mudou |= self.atualizar_fonte(f)
```

Para cada fonte cuja hora chegou: reagenda e atualiza. `mudou |= ...` faz "ou" lógico acumulado: basta uma fonte mudar para `mudou` ficar `True`.

### Linhas 169 a 170

```python
        if mudou:
            self.montar_resumo()
```

Só remonta o resumo se algo mudou.

### Linha 172

```python
    def resumir_emails(self, conector):
```

Resume os e-mails de uma conta com IA.

### Linha 173

```python
        """Resumo com IA dos e-mails de uma conta, em segundo plano (a chamada demora alguns segundos)."""
```

Docstring: roda em segundo plano porque a chamada ao Claude leva alguns segundos.

### Linha 174

```python
        conta = conector.email or conector.empresa
```

Identifica a conta pelo e-mail (ou pelo nome da empresa, se o e-mail ainda não for conhecido).

### Linha 175

```python
        mensagens = list(conector.mensagens)
```

Copia a lista de mensagens, para a thread trabalhar numa cópia que não muda no meio.

### Linha 177

```python
        def trabalho():
```

Função interna (definida dentro de outra) que a thread vai executar. Ela enxerga as variáveis de fora (`conta`, `mensagens`), o que se chama closure.

### Linhas 178 a 179

```python
            r = resumo_email.resumir(conta, mensagens, os.getenv("ANTHROPIC_API_KEY", "").strip(),
                                     self.cfg["ia"]["modelo"])
```

Chama o resumo com a conta, as mensagens, a chave do Claude lida do ambiente e o modelo configurado.

### Linha 180

```python
            r["empresa"] = conector.empresa
```

Marca de qual empresa é o resumo.

### Linha 181

```python
            self.resumos_email[conta] = r
```

Guarda o resumo dessa conta.

### Linha 182

```python
            self.emitir("emails", resumos=dict(self.resumos_email))
```

Manda para a tela uma cópia de todos os resumos (`dict(...)` copia, para a tela não ler o dicionário enquanto ele muda).

### Linha 183

```python
        threading.Thread(target=trabalho, daemon=True).start()
```

Começa a thread.

### Linha 185

```python
    # ---------- tarefas ----------
```

Comentário da parte das tarefas.

### Linhas 186 a 189

```python
    def atualizar_clima(self):
        try:
            self.clima = weather.buscar(self.cfg["clima"], self.cfg["usuario"]["fuso"])
            self.emitir("clima", clima=self.clima)
```

Busca o clima e manda para a tela.

### Linhas 190 a 191

```python
        except net.ApiError as exc:
            self.emitir("erro", texto=str(exc))
```

Se falhar, manda o erro para a tela em vez de quebrar.

### Linha 193

```python
    def bom_dia(self):
```

Ação das 07:00.

### Linha 194

```python
        self.atualizar_clima()
```

Atualiza o clima.

### Linha 195

```python
        r = self.atualizar_resumo(avisar_urgentes=False)
```

Faz a busca completa sem avisar urgentes (o resumo inteiro já será enviado).

### Linha 196

```python
        self.vistos.novos(r.itens)       # o que já está no resumo não precisa de aviso separado
```

Marca todos os itens como vistos, para não gerar avisos separados depois.

### Linha 197

```python
        titulo, texto, campos = digest.texto_resumo(r, self.nome)
```

Monta o texto do resumo.

### Linha 198

```python
        self.avisar(titulo, texto, "#ffcc4d", campos=campos, tags=["sunny"])
```

Envia em amarelo, com os campos por empresa e a tag de sol.

### Linha 199

```python
        self.emitir("bom_dia", resumo=r)
```

Avisa a tela para mostrar a animação de bom dia.

### Linha 201

```python
    def fim_do_dia(self):
```

Ação das 18:00.

### Linha 202

```python
        r = self.resumo or self.atualizar_resumo(avisar_urgentes=False)
```

Usa o resumo atual ou, se ainda não existir, busca.

### Linhas 203 a 204

```python
        titulo, texto = digest.texto_fim(r, self.nome)
        self.avisar(titulo, texto, "#6b5bd6", tags=["crescent_moon"])
```

Monta e envia o texto de fim do expediente em roxo, com a tag de lua.

### Linha 205

```python
        self.emitir("fim_do_dia")
```

Avisa a tela para mostrar a animação de fim do dia.

### Linha 207

```python
    def checar_teams(self):
```

Confere o Teams atrás de pedidos de reunião.

### Linha 208

```python
        desde, self.ultima_checagem_teams = self.ultima_checagem_teams, datetime.now().astimezone()
```

Guarda o momento da conferência anterior em `desde` e atualiza para agora, numa linha só.

### Linhas 209 a 210

```python
        try:
            mensagens = self.agendador.conector.mensagens_novas(desde)
```

Busca as mensagens recebidas desde a última conferência.

### Linhas 211 a 214

```python
        except net.ApiError as exc:
            self.ultima_checagem_teams = desde       # tenta o mesmo intervalo na próxima
            self.emitir("erro", texto=str(exc))
            return
```

Se falhar, volta o marcador para o valor anterior (assim as mensagens desse intervalo serão buscadas na próxima vez), manda o erro para a tela e sai.

### Linhas 215 a 217

```python
        for msg in mensagens:
            if eh_pedido(msg["texto"], self.cfg["reunioes"]["palavras"]):
                self.tratar_pedido(msg)
```

Para cada mensagem, se ela parece um pedido de reunião (contém uma das palavras configuradas), trata o pedido.

### Linha 219

```python
    def tratar_pedido(self, msg):
```

Trata um pedido de reunião.

### Linhas 220 a 221

```python
        try:
            pedido = self.agendador.de_mensagem(msg)
```

Pede ao agendador para descobrir o e-mail da pessoa e buscar os horários livres dos dois.

### Linhas 222 a 224

```python
        except (net.ApiError, ValueError) as exc:
            self.emitir("erro", texto=f"pedido de reunião de {msg['nome']}: {exc}")
            return
```

Se falhar, avisa na tela com o nome de quem pediu.

### Linha 225

```python
        opcoes = "\n".join(f"• {rotulo(h)}" for h in pedido.horarios)
```

Monta a lista de horários, um por linha, com um marcador na frente.

### Linhas 226 a 227

```python
        self.avisar(f"📅 {pedido.pessoa} pediu reunião", f"\"{pedido.texto[:150]}\"\n\nHorários livres para vocês dois:\n{opcoes}",
                    self.cores.get(pedido.empresa, "#7ad67a"), tags=["calendar"], prioridade=4)
```

Notifica no Discord e no celular: quem pediu, os primeiros 150 caracteres da mensagem e os horários livres.

### Linhas 228 a 230

```python
        self.emitir("proposta", proposta={"pessoa": pedido.pessoa, "email": pedido.email,
                                          "assunto": f"Reunião com {pedido.pessoa}", "horarios": pedido.horarios,
                                          "chat_id": pedido.chat_id, "origem": "teams", "texto": pedido.texto})
```

Manda a proposta para a tela, que mostra os horários como botões para confirmar.

### Linhas 232 a 233

```python
    def _alarme_tocou(self, titulo, mensagem):
        self.emitir("alarme", titulo=titulo, texto=mensagem)
```

Função chamada pelo ouvinte quando o alarme toca. Só repassa o evento para a tela.

### Linha 235

```python
    # ---------- comandos vindos da tela ----------
```

Comentário da parte dos comandos da tela.

### Linha 236

```python
    def _comando(self, tipo, dados):
```

Executa um comando que veio da tela.

### Linhas 237 a 240

```python
        if tipo == "reuniao":
            if not self.agendador:
                self.emitir("erro", texto="o agendador precisa de uma empresa com Outlook + Teams ativa")
                return
```

Comando "reuniao" (texto digitado). Se não houver agendador, explica o que falta.

### Linhas 241 a 245

```python
            try:
                proposta = self.agendador.de_comando(dados["texto"])
            except (net.ApiError, ValueError) as exc:
                self.emitir("erro", texto=str(exc))
                return
```

Interpreta o texto e busca horários livres. Se falhar, mostra o erro.

### Linhas 246 a 247

```python
            proposta["origem"] = "comando"
            self.emitir("proposta", proposta=proposta)
```

Marca que a proposta veio de um comando e manda para a tela.

### Linhas 248 a 249

```python
        elif tipo == "confirmar":
            p, h = dados["proposta"], dados["horario"]
```

Comando "confirmar": o usuário clicou num horário. Pega a proposta e o horário.

### Linhas 250 a 254

```python
            try:
                link = self.agendador.confirmar(p["email"], p["pessoa"], h, p["assunto"])
            except net.ApiError as exc:
                self.emitir("erro", texto=str(exc))
                return
```

Cria a reunião no Outlook (com link do Teams). Se falhar, mostra o erro.

### Linha 255

```python
            self.emitir("agendado", pessoa=p["pessoa"], horario=h, assunto=p["assunto"])
```

Avisa a tela para mostrar a animação de reunião agendada.

### Linhas 256 a 257

```python
            self.avisar("✅ Reunião agendada", f"{p['assunto']}\n{rotulo(h)} com {p['pessoa']}",
                        "#7ad67a", tags=["white_check_mark"], url=link)
```

Notifica no Discord e no celular, com o link da reunião.

### Linhas 258 a 259

```python
        elif tipo == "limpar":
            self.limpar(dados.get("chaves"))
```

Comando "limpar": tira itens do resumo.

### Linhas 260 a 262

```python
        elif tipo == "atualizar":
            self.atualizar_clima()
            self.atualizar_resumo()
```

Comando "atualizar": clima e busca completa.

### Linhas 263 a 264

```python
        elif tipo == "demo":
            self._demo(dados["acao"])
```

Comando "demo": atalhos da apresentação.

### Linha 266

```python
    def _demo(self, acao):
```

Atalhos da demonstração.

### Linha 267

```python
        """Atalhos da apresentação: disparam os mesmos caminhos do uso real."""
```

Docstring: os atalhos usam os mesmos caminhos do uso real (não são telas falsas).

### Linhas 268 a 275

```python
        if acao == "bom_dia":
            self.bom_dia()
        elif acao == "fim_do_dia":
            self.fim_do_dia()
        elif acao == "pedido" and self.agendador:
            self.tratar_pedido(pedido_demo(datetime.now()))
        elif acao == "alarme":
            self._alarme_tocou("Alarme", "Hora de acordar! (simulado)")
```

Cada ação chama a função correspondente: bom dia, fim do dia, um pedido de reunião de exemplo (só se houver agendador) e um alarme simulado.

### Linhas 277 a 280

```python
    def encerrar(self):
        """Para o motor e o ouvinte do alarme (usado ao salvar novas configurações)."""
        self.parar.set()
        self.alarme.parar.set()
```

Para o motor e o ouvinte do alarme, ligando os dois sinais de parada. Usado quando o usuário salva novas configurações e o motor é recriado.

### Linha 282

```python
    # ---------- laço principal ----------
```

Comentário do laço principal.

### Linha 283

```python
    def run(self):
```

`run` é o método que a thread executa quando chamamos `start()`.

### Linhas 284 a 285

```python
        if self.cfg["notificacoes"]["ouvir_alarme"] and self.alarme.configurado():
            self.alarme.start()
```

Se o alarme do celular está ligado e configurado, começa a escutar.

### Linha 286

```python
        anterior = digest.carregar_hoje()          # mostra na hora o último resumo de hoje
```

Lê o resumo salvo hoje.

### Linhas 287 a 290

```python
        if anterior:
            anterior.itens = [i for i in anterior.itens if i.chave() not in self.limpos]
            self.resumo = anterior
            self.emitir("resumo", resumo=anterior, cores=self.cores)
```

Se existir, tira os itens apagados e manda para a tela na hora (a tela não fica vazia enquanto a busca acontece).

### Linha 291

```python
        self.atualizar_clima()
```

Busca o clima.

### Linha 292

```python
        self.atualizar_resumo(avisar_urgentes=False)   # a única busca completa (ao abrir)
```

A única busca completa automática, feita ao abrir.

### Linha 293

```python
        while not self.parar.is_set():
```

Laço que roda até o sinal de parada ser ligado.

### Linha 294

```python
            self.agenda.tick(datetime.now().astimezone())
```

Roda as tarefas da agenda que estiverem na hora.

### Linhas 295 a 298

```python
            try:
                tipo, dados = self.comandos.get(timeout=0.5)
            except queue.Empty:
                continue
```

Espera um comando da tela por até meio segundo. Se não chegar nenhum (`queue.Empty`), volta ao começo do laço. Esse tempo curto faz o laço conferir a agenda duas vezes por segundo.

### Linhas 299 a 303

```python
            try:
                self._comando(tipo, dados)
            except Exception as exc:
                log.exception("comando %s falhou", tipo)
                self.emitir("erro", texto=f"erro inesperado: {exc}")
```

Executa o comando. Qualquer erro inesperado é registrado no log e mostrado na tela, e o motor continua rodando.
