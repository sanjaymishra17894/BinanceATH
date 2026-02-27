# Binance ATH Telegram Bot

This bot monitors a custom list of USDT-M Futures trading pairs on Binance and sends a Telegram message whenever a symbol breaks its all-time high (ATH).

## What it does

- You provide the coin list (for example top 10 symbols).
- The bot fetches each symbol's ATH from Binance USDT-M Futures daily candles.
- It polls the latest futures price continuously.
- If the current price is higher than the known ATH, it sends a Telegram alert to your channel.

Message format:

```text
COIN: BTCUSDT
NEW All Time High: 70000.12
ATH Break: 69999.99
```

## Setup

1. Create a Telegram bot with BotFather.
2. Add the bot to your Telegram channel and make it admin.
3. Get your channel chat ID.
4. Copy `.env.example` to `.env` and fill in your values.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with your bot token and chat id
python bot.py
```

The bot automatically loads variables from `.env` if present. Explicit environment variables still take priority.

## Notes

- Only `USDT` pairs (USDT-M Futures symbols) are supported.
- The bot sends one alert each time a new ATH is reached and then updates the stored ATH.
- Keep the process running with `screen`, `tmux`, Docker, or systemd for production.
