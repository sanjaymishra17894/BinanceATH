# Binance ATH Telegram Bot

This bot monitors a custom list of USDT-M Futures trading pairs on Binance and sends a Telegram message whenever a symbol breaks its rolling 24-hour high (configurable via `WINDOW_HOURS`).

## What it does

- You provide the coin list (for example top 10 symbols).
- The bot fetches the highest *high* price for each symbol over the last `WINDOW_HOURS` (default 24 h) using Binance USDT-M Futures 1h klines.
- It polls the latest futures price continuously.
- If the current price exceeds the rolling window high, it sends a Telegram alert to your channel.
- The window high is refreshed from the Binance API on every poll cycle (one lightweight API call per symbol per cycle using the 1h interval).

Message format:

```text
🚀 NEW 24h HIGH BREAK (USDT-M Futures)

Symbol:      VVVUSDT
Last Price:  0.123456
Window:      24h
Window High: 0.120000
New High:    0.123456
Break %:     +2.88%

━━━━━━━━━━━━━━━━━━━━
📌 Trade Ideas (Example)
Interval: 1h candles
Time (UTC): 2026-02-27 10:25:12

1) 📈 LONG (momentum continuation)
   Entry (Now):              0.123456
   Pump % (from 24h high):   +2.88%
   TP (same +% move):        0.127012

2) 📉 SHORT (retest / mean reversion)
   Entry (Now):              0.123456
   TP (24h high level):      0.120000

Notes:
- LONG TP = Entry * (1 + Pump%/100)
- SHORT TP = 24h window high
━━━━━━━━━━━━━━━━━━━━
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

## Configuration

| Variable            | Default | Description |
|---------------------|---------|-------------|
| `TELEGRAM_BOT_TOKEN`| —       | Telegram bot token from BotFather (required) |
| `TELEGRAM_CHAT_ID`  | —       | Target channel/chat ID (required) |
| `TOP_COINS`         | —       | Comma-separated USDT-M Futures symbols, e.g. `BTCUSDT,ETHUSDT` (required) |
| `POLL_SECONDS`      | `60`    | Seconds between price polls |
| `WINDOW_HOURS`      | `24`    | Rolling window in hours used to compute the high baseline |

## Notes

- Only `USDT` pairs (USDT-M Futures symbols) are supported.
- The bot sends one alert each time the current price breaks the rolling window high and then raises the stored baseline to the current price to prevent immediate re-alerts.
- Keep the process running with `screen`, `tmux`, Docker, or systemd for production.
