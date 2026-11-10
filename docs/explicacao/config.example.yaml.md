# `config.example.yaml`

[Voltar ao índice](README.md) · [Ver o arquivo](../../config.example.yaml)

Exemplo de `config.yaml`. O arquivo real é gerado pela tela de Configurações; este exemplo mostra o formato para quem quiser entender ou montar à mão. Não contém nenhum segredo.

### Linhas 1 a 3

```yaml
# Exemplo do config.yaml. Você NÃO precisa editar este arquivo:
# abra o PixelDigest e use a tela de Configurações (botão Configurar ou F10).
# Ela grava o config.yaml (sem segredos) e as chaves no .env.
```

Comentários (no YAML começam com `#`): não é preciso editar, a tela grava sozinha, e as chaves vão para o `.env`.

### Linha 5

```yaml
demo: false
```

Modo demonstração desligado.

### Linhas 6 a 8

```yaml
usuario:
  nome: Felipe
  fuso: America/Sao_Paulo
```

Usuário: nome e fuso horário no padrão IANA. A indentação de dois espaços indica que `nome` e `fuso` pertencem a `usuario`.

### Linhas 9 a 12

```yaml
clima:
  local: Avenida Paulista, São Paulo
  lat: -23.5614
  lon: -46.6559
```

Local do clima: endereço mostrado e coordenadas (preenchidas pela busca de endereço).

### Linhas 13 a 16

```yaml
horarios:
  inicio_dia: '07:00'
  fim_dia: '18:00'
  expediente: ['09:00', '18:00']
```

Horários: bom dia, fim do expediente e o expediente (uma lista de dois horários). As aspas garantem que "07:00" seja lido como texto, não como número.

### Linhas 17 a 20

```yaml
notificacoes:
  discord: true
  celular: true
  ouvir_alarme: true
```

Notificações ligadas: Discord, celular e alarme.

### Linhas 21 a 25

```yaml
reunioes:
  duracao_padrao: 30
  dias_para_frente: 3
  responder_no_teams: false
  palavras: [reunião, reuniao, call, meet, meeting, conversar, alinhar, papo]
```

Regras de reunião: duração padrão, dias à frente, resposta automática no Teams desligada e as palavras que indicam pedido (uma lista em uma linha, entre colchetes).

### Linha 26

```yaml
empresas:
```

Lista de empresas. Cada item começa com `-`.

### Linhas 27 a 28

```yaml
- nome: Minha Empresa
  cor: '#3fa7ff'
```

Primeira empresa: nome e cor.

### Linha 29

```yaml
  conectores:
```

Lista de serviços da empresa.

### Linhas 30 a 34

```yaml
  - tipo: slack
    token_env: PD_MINHA_EMPRESA_SLACK_TOKEN    # o token fica no .env
    meu_id: U0123456789
    canais: [C0123ABCD]
    incluir_dms: false
```

Slack: só o NOME da variável do token (`token_env`), nunca o token. O comentário lembra que o valor fica no `.env`. Depois, o id do usuário, os canais e as DMs.

### Linhas 35 a 37

```yaml
  - tipo: clickup
    token_env: PD_MINHA_EMPRESA_CLICKUP_TOKEN
    equipe_id: '1234567'
```

ClickUp: nome da variável do token e o id do workspace.

### Linhas 38 a 41

```yaml
  - tipo: gmail
    credenciais: tokens/google-cliente-minha_empresa.json
    conta: minha_empresa
    agenda: true
```

Gmail: arquivo de credenciais (na pasta `tokens/`, fora do GitHub), nome da conta e agenda ligada.

### Linhas 42 a 43

```yaml
- nome: Outra Empresa
  cor: '#7ad67a'
```

Segunda empresa, com outra cor.

### Linhas 44 a 51

```yaml
  conectores:
  - tipo: microsoft
    client_id: 00000000-0000-0000-0000-000000000000
    tenant: organizations
    email: true
    agenda: true
    teams: true
    agendador: true
```

Microsoft (Outlook e Teams): client id do app no Azure (aqui um valor zerado de exemplo), tenant e as partes usadas, incluindo o agendador.
