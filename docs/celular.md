# Celular (Android): notificações e alarme

O PixelDigest usa o **ntfy**, um serviço gratuito de notificações. Ele funciona por "tópicos": quem publica num tópico faz o aviso chegar em todo mundo que assinou.

Usamos dois tópicos:

| Tópico | Direção | Para quê |
|---|---|---|
| `NTFY_TOPIC` | PC → celular | resumo, urgentes, reuniões |
| `NTFY_TOPIC_ALARME` | celular → PC | avisar que o alarme tocou |

Os tópicos do ntfy.sh são públicos para quem souber o nome. Por isso, escolha nomes difíceis de adivinhar (ex.: `pixeldigest-felipe-8f3k2q`). Se quiser mais segurança, use um servidor ntfy próprio com `NTFY_TOKEN`.

## 1. Receber as notificações

1. Instale o app **ntfy** (Play Store ou F-Droid).
2. Toque em **+** e assine o tópico que você colocou em `NTFY_TOPIC`.
3. No PC, rode `python -m pixeldigest testar`. A notificação chega no celular e no Discord.

## 2. Mandar o alarme do celular para o PC

1. Instale o **MacroDroid** (Play Store).
2. Crie uma macro nova.
3. **Gatilho:** Notificação > Notificação recebida.
   * Aplicativo: o seu Relógio (Google Relógio ou Relógio da Samsung).
   * Texto contém: `Alarme`. Se o seu relógio usar outro texto na notificação, ajuste aqui.
   * Se a sua versão do MacroDroid tiver um gatilho próprio de alarme do relógio, pode usar ele no lugar.
4. **Ação:** Conectividade > Requisição HTTP.
   * Método: POST
   * URL: `https://ntfy.sh/SEU_NTFY_TOPIC_ALARME`
   * Corpo: `Hora de acordar!`
   * Cabeçalho opcional: `Title: Alarme`
5. Salve e libere o acesso às notificações quando o MacroDroid pedir.

Teste sem esperar o alarme: rode no PC (ou em qualquer terminal) o comando abaixo. A animação do despertador aparece na tela.

```bash
curl -d "Teste do alarme" https://ntfy.sh/SEU_NTFY_TOPIC_ALARME
```

O PC não precisa de porta aberta no roteador: ele mesmo se conecta ao ntfy e fica ouvindo (streaming JSON). Se a internet cair, ele reconecta sozinho.
