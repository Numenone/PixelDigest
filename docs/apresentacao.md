# Roteiro da apresentação (5 minutos)

## Antes de começar

* Abra o programa com as contas reais **ou** com `python -m pixeldigest --demo` (não mostra dados das empresas).
* Deixe o celular com o app ntfy aberto e o Discord visível.
* Tenha uma aba com o repositório no GitHub.
* Teste antes: `python -m pixeldigest testar`.

## 1. O problema (1 min)

"Trabalho em duas empresas: uma usa Slack, ClickUp e Gmail, a outra usa Outlook e Teams. Todo dia eu abria cinco ferramentas para saber o que era urgente, perdia menções e gastava mensagens combinando horário de reunião. Automatizei isso: um resumo único, avisos no celular e no Discord, e um agendador que acha o horário livre das duas pessoas sozinho."

## 2. A arquitetura (1 min)

Mostre o diagrama do README e fale o caminho:

1. **Gatilhos:** horário (07:00, 18:00), consultas periódicas, alarme do celular pelo ntfy e comando digitado.
2. **Coleta:** cada API devolve JSON (Slack, ClickUp, Gmail, Microsoft Graph, Open-Meteo). Cada conector converte para o mesmo formato `Item`.
3. **Processamento:** prioriza (menção, atrasada, DM), reconhece pedido de reunião e consulta o `findMeetingTimes`.
4. **Saída:** tela animada, Discord e celular ao mesmo tempo, JSON do dia salvo.

## 3. Demonstração ao vivo (2 min)

0. **F10**: mostre rapidinho a tela de Configurações (abas, busca de endereço, chaves mascaradas, QR code do celular).
1. **F6** algumas vezes: o clima muda de sol para tempestade, as nuvens fecham e a tela escurece.
2. **F1**: animação do bom dia, e o resumo chega no celular e no Discord.
3. **F3**: chega um pedido de reunião "do Teams". Aparecem 3 horários livres. Aperte **1**: animação do "AGENDADO!" e a confirmação chega no celular.
4. Digite `reunião com Ana amanhã 45min sobre orçamento` e aperte Enter. Mostre que ele entendeu pessoa, dia, duração e assunto.
5. Se der tempo: dispare o alarme pelo celular (ou rode `curl -d "teste" https://ntfy.sh/SEU_TOPICO_ALARME`) e mostre o despertador aparecendo na tela.

## 4. Perguntas prováveis (1 min)

**Onde ficam as senhas?**
A tela de Configurações grava as chaves no `.env`, que está no `.gitignore`. O `config.yaml` só guarda o nome da variável (`config.salvar()`). Google e Microsoft usam OAuth: o token fica em `tokens/` e é renovado sozinho.

**E se uma API cair?**
`net.py` tenta de novo até 3 vezes com espera crescente em timeout, 429 e 5xx. Erro 401/403 vira mensagem clara de "confira o token". No resumo, cada fonte é independente: se o Slack cair, o resto aparece, junto com o aviso "1 fonte com problema". Notificação que falha vai para `data/pendentes.json` e é reenviada a cada 5 minutos.

**Como ele sabe que é um pedido de reunião?**
`eh_pedido()` em `meetings.py`: precisa ter uma palavra de reunião (lista no YAML) **e** uma intenção (pergunta ou verbo como "podemos", "marcar"). "A reunião foi ótima" não dispara.

**Como acha o horário livre dos dois?**
Monta as janelas de expediente dos próximos dias úteis e chama o `POST /me/findMeetingTimes` do Microsoft Graph com o e-mail da outra pessoa. O Outlook responde com os horários em que os dois estão livres. Depois `espalhar()` escolhe horários em dias diferentes.

**Por que a tela não trava esperando a internet?**
As chamadas rodam no `Motor` (uma thread). A tela só lê uma fila de eventos e manda comandos por outra fila.

**Como a chuva vira escuridão?**
`intensidade()` em `weather.py` transforma o código do tempo e os milímetros de chuva num número de 0 a 1. A cena usa esse número para a quantidade de gotas, o tamanho e a altura das nuvens e a camada escura por cima.

**Próximos passos?**
Resumo escrito por IA, agendador também no Google Agenda e painel web com o histórico.

## Ajustes ao vivo que o professor pode pedir

| Pedido | Onde mexer |
|---|---|
| Mudar o horário do bom dia | `config.yaml` → `horarios.inicio_dia` |
| Mudar a duração padrão da reunião | `config.yaml` → `reunioes.duracao_padrao` |
| Nova palavra de pedido de reunião | `config.yaml` → `reunioes.palavras` |
| Mudar a cidade do clima | `config.yaml` → `cidade` |
| Cor de uma empresa | `config.yaml` → `cor` |
| Mudar quantas tentativas na rede | `net.py` → `retries=3` |
| Deixar a chuva mais escura | `ui/scene.py` → `escuro` (o 0.62) |
