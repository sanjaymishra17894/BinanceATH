# Binance ATH Telegram Bot

This bot monitors a custom list of USDT-M Futures trading pairs on Binance and sends a Telegram message whenever a symbol breaks its all-time high (ATH).

## What it does

- You provide the coin list (for example top 10 symbols).
- The bot fetches each symbol's ATH from Binance USDT-M Futures daily candles.
- It polls the latest futures price continuously.
- If the current price is higher than the known ATH, it sends a Telegram alert to your channel.

Message format:

```text
🚀 NEW ATH (USDT-M Futures)

Symbol: VVVUSDT
Last Price: 0.123456
Old ATH:    0.120000
New ATH:    0.123456
Break %:    +2.88%

━━━━━━━━━━━━━━━━━━━━
📌 Trade Ideas (Example)
Interval: 1d candles
Time (UTC): 2026-02-27 10:25:12

1) 📈 LONG (momentum continuation)
   Entry (Now):        0.123456
   Pump % (from ATH):  +2.88%
   TP (same +% move):  0.127012

2) 📉 SHORT (retest / mean reversion)
   Entry (Now):        0.123456
   TP (Old ATH level): 0.120000

Notes:
- LONG TP = Entry * (1 + Pump%/100)
- SHORT TP = Old ATH
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

## Notes

- Only `USDT` pairs (USDT-M Futures symbols) are supported.
- The bot sends one alert each time a new ATH is reached and then updates the stored ATH.
- Keep the process running with `screen`, `tmux`, Docker, or systemd for production.
