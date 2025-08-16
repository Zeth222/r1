# Dynamic Hedge Bot

Bot em Python para hedge dinâmico entre posição LP Uniswap v3 (WETH/USDC na Arbitrum) e short perp na Hyperliquid.

## Setup

1. Crie um `.env` a partir de `.env.example` e preencha as chaves necessárias (`TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `WALLET_ADDRESS`, `HL_WALLET_ADDRESS`, etc).
2. Instale o SDK da Hyperliquid e demais dependências:

```bash
pip install hyperliquid-python-sdk
# ou
pip install -r requirements.txt
```

3. Execute o bot (modo espectador por padrão):

```bash
python -m bot.main
```

`WEEKLY_REPORT_DOW` define o dia da semana do relatório semanal e aceita valores de 1 (segunda-feira) a 7 (domingo).

### Modo ativo

Defina `MODE=active` no `.env` e forneça `PRIVATE_KEY`/`HL_PRIVATE_KEY`. Por padrão apenas o hedge perp é executado; para permitir operações na LP ajuste `ENABLE_LP_EXECUTIONS=true`.

### Configuração Hyperliquid

O SDK segue o [`config.json` de exemplo](https://github.com/hyperliquid/py-sdk/blob/master/example/config.json), que define:

- `account_address`: endereço da carteira principal.
- `secret_key`: chave privada usada para assinar (pode ser de uma carteira API).

No `.env` estes campos correspondem a `HL_WALLET_ADDRESS` e `HL_PRIVATE_KEY`. A carteira API é opcional, mas recomendada:

- Gere uma API wallet na interface da Hyperliquid e anote a `secret_key`.
- `account_address` permanece o endereço da carteira principal.
- Guarde a chave da carteira principal separadamente; ela só é usada para criar a API wallet.

Para testar a conexão com a rede de teste:

```python
from hyperliquid.info import Info, constants

info = Info(constants.TESTNET_API_URL, skip_ws=True)
print(info.user_state("<account_address>"))
```

## Segurança

- Nunca commitar o arquivo `.env`.
- Revise as flags antes de operar em produção.

## Troubleshooting

- Subgraph indisponível: o bot notificará via Telegram e tentará novamente.
- Funding extremo: verifique alertas e considere desligar o hedge temporariamente.

## Estrutura

O pacote `bot` contém os módulos principais:

- `config.py` – leitura e validação de configuração.
- `data/` – acessos a APIs (Uniswap, Hyperliquid, preços).
- `strategy.py` – lógica de hedge e sizing.
- `executor.py` – camada de execução.
- `reports.py` – relatórios diários/semanais.

Testes simples estão em `tests/`.
