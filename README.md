# Dynamic Hedge Bot

Bot em Python para hedge dinâmico entre posição LP Uniswap v3 (WETH/USDC na Arbitrum) e short perp na Hyperliquid.

## Setup

1. Crie um `.env` a partir de `.env.example` e preencha as chaves necessárias (`TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `WALLET_ADDRESS`, etc).
2. Instale dependências:

```bash
pip install -r requirements.txt
```

3. Execute o bot (modo espectador por padrão):

```bash
python -m bot.main
```

### Modo ativo

Defina `MODE=active` no `.env` e forneça `PRIVATE_KEY`/`HL_API_SECRET`. Por padrão apenas o hedge perp é executado; para permitir operações na LP ajuste `ENABLE_LP_EXECUTIONS=true`.

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
