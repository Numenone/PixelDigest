# Explicação do código, linha por linha

Cada arquivo do PixelDigest tem uma página aqui. Em cada página, o código aparece
em trechos (copiados direto do arquivo, com o número das linhas) e, logo abaixo de
cada trecho, o que ele faz e por que está ali. Nenhuma linha com código ficou de
fora: o script `tools/gerar_explicacao.py` confere isso toda vez que gera as páginas.

Ordem sugerida de leitura: comece pelo `__main__.py` (onde o programa começa),
depois `config.py`, `net.py`, `models.py` e `core.py` (o Motor). Em seguida os
conectores (cada API), e por último a interface (`ui/`) e os testes.

Os arquivos `pixeldigest/__init__.py` e `pixeldigest/ui/__init__.py` estão vazios:
eles só existem para o Python tratar a pasta como um pacote (e permitir os imports
com ponto, como `from . import config`).

| Arquivo | Linhas | O que faz |
|---|---:|---|
| [`pixeldigest/__main__.py`](pixeldigest.__main__.py.md) | 216 | É o ponto de entrada do programa. |
| [`pixeldigest/config.py`](pixeldigest.config.py.md) | 154 | Lê, completa com valores padrão, valida e salva a configuração. |
| [`pixeldigest/net.py`](pixeldigest.net.py.md) | 89 | Toda conversa com a internet passa por este arquivo. |
| [`pixeldigest/models.py`](pixeldigest.models.py.md) | 110 | Define os formatos de dados comuns do programa. |
| [`pixeldigest/scheduler.py`](pixeldigest.scheduler.py.md) | 69 | Agendador de tarefas por tempo: são os gatilhos de horário do projeto (07:00, 18:00 e as tarefas que repetem a cada N segundos). |
| [`pixeldigest/digest.py`](pixeldigest.digest.py.md) | 129 | Monta o resumo do dia: junta os itens de todas as fontes, ordena por importância, gera o texto das notificações e salva o arquivo JSON do dia. |
| [`pixeldigest/core.py`](pixeldigest.core.py.md) | 303 | O Motor é o coração da automação. |
| [`pixeldigest/meetings.py`](pixeldigest.meetings.py.md) | 202 | Agendador de reuniões. |
| [`pixeldigest/notify.py`](pixeldigest.notify.py.md) | 106 | Envia as notificações para o Discord e para o celular ao mesmo tempo. |
| [`pixeldigest/phone.py`](pixeldigest.phone.py.md) | 61 | Escuta o alarme do celular. |
| [`pixeldigest/resumo_email.py`](pixeldigest.resumo_email.py.md) | 126 | Resume com IA (Claude, da Anthropic) os 10 e-mails mais recentes de cada conta. |
| [`pixeldigest/assistente.py`](pixeldigest.assistente.py.md) | 204 | Funções chamadas pelos botões da tela de Configurações: buscar endereço, descobrir localização, testar Discord e ntfy, conectar Slack e ClickUp, testar a chave do Claude e cada serviço, e ligar o início junto com o Windows. |
| [`pixeldigest/connectors/__init__.py`](pixeldigest.connectors.__init__.py.md) | 40 | Registro dos tipos de serviço e função que cria os conectores a partir da configuração. |
| [`pixeldigest/connectors/base.py`](pixeldigest.connectors.base.py.md) | 57 | Classe base de todos os conectores. |
| [`pixeldigest/connectors/clickup.py`](pixeldigest.connectors.clickup.py.md) | 57 | Conector do ClickUp: busca as tarefas atribuídas a você que vencem até amanhã, incluindo as atrasadas. |
| [`pixeldigest/connectors/slack.py`](pixeldigest.connectors.slack.py.md) | 145 | Conector do Slack: busca as mensagens das últimas 24 horas nos canais escolhidos, nas DMs e nos grupos, marcando como urgente quando alguém menciona você. |
| [`pixeldigest/connectors/google.py`](pixeldigest.connectors.google.py.md) | 187 | Conector do Gmail e do Google Agenda, com OAuth 2.0. |
| [`pixeldigest/connectors/microsoft.py`](pixeldigest.connectors.microsoft.py.md) | 292 | Conector do Microsoft 365 pelo Microsoft Graph: e-mail e agenda do Outlook e chats do Teams. |
| [`pixeldigest/connectors/weather.py`](pixeldigest.connectors.weather.py.md) | 137 | Clima e tempo pelo Open-Meteo, uma API pública que não precisa de chave. |
| [`pixeldigest/connectors/zoom.py`](pixeldigest.connectors.zoom.py.md) | 60 | Conector do Zoom: lê as reuniões agendadas para hoje e amanhã. |
| [`pixeldigest/connectors/demo.py`](pixeldigest.connectors.demo.py.md) | 112 | Modo demonstração: dados inventados, sem nenhuma conta real. |
| [`pixeldigest/ui/tela.py`](pixeldigest.ui.tela.py.md) | 85 | Cuida da orientação (horizontal ou vertical) e da escala da tela. |
| [`pixeldigest/ui/icons.py`](pixeldigest.ui.icons.py.md) | 204 | Ícones em pixel art desenhados direto no código, sem nenhum arquivo de imagem. |
| [`pixeldigest/ui/font.py`](pixeldigest.ui.font.py.md) | 108 | Desenho de texto em pixel art, com acentos. |
| [`pixeldigest/ui/widgets.py`](pixeldigest.ui.widgets.py.md) | 294 | Componentes da interface (botões, campos de texto, interruptores, QR code) no estilo "immediate mode": em vez de criar um objeto para cada botão, a tela chama uma função a cada quadro, e a função desenha e já responde se foi clicada. |
| [`pixeldigest/ui/effects.py`](pixeldigest.ui.effects.py.md) | 326 | Animações que aparecem por cima da tela: bom dia, fim do expediente, reunião agendada, alarme, avisos rápidos (toasts) e confete. |
| [`pixeldigest/ui/scene.py`](pixeldigest.ui.scene.py.md) | 421 | O cenário animado em pixel art: céu, sol, lua, estrelas, nuvens, cidade, chuva, relâmpago, neblina e neve. |
| [`pixeldigest/ui/settings.py`](pixeldigest.ui.settings.py.md) | 715 | A tela de Configurações. |
| [`pixeldigest/ui/app.py`](pixeldigest.ui.app.py.md) | 853 | A janela principal: cenário animado ao fundo, as abas (Início, Resumo do dia, E-mails, Agenda) e a barra de navegação embaixo. |
| [`tests/test_pixeldigest.py`](tests.test_pixeldigest.py.md) | 474 | Testes automáticos com o pytest. |
| [`tools/gerar_gif.py`](tools.gerar_gif.py.md) | 51 | Script auxiliar que gera o GIF animado do README (`docs/img/demo.gif`): o clima passando de sol para tempestade e uma reunião sendo agendada. |
| [`tools/gerar_explicacao.py`](tools.gerar_explicacao.py.md) | 117 | Script que monta esta própria documentação: junta o código de cada arquivo com as notas escritas em `docs/explicacao/_notas/`, gera o índice e confere se nenhuma linha ficou sem explicação. |
| [`run.bat`](run.bat.md) | 20 | Atalho para Windows: na primeira vez prepara o Python e as bibliotecas; depois só abre o programa. |
| [`requirements.txt`](requirements.txt.md) | 10 | Lista das bibliotecas externas que o projeto usa. |
| [`config.example.yaml`](config.example.yaml.md) | 51 | Exemplo de `config.yaml`. |
| [`.env.example`](env.example.md) | 18 | Exemplo do `.env`, com todas as variáveis de ambiente que o projeto usa. |
| [`requirements-dev.txt`](requirements-dev.txt.md) | 2 | Bibliotecas usadas só no desenvolvimento (não precisam estar instaladas para usar o programa). |
| [`.gitignore`](gitignore.md) | 13 | Diz ao Git quais arquivos nunca devem ir para o repositório. |
