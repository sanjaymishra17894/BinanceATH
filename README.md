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

| Variable               | Default | Description |
|------------------------|---------|-------------|
| `TELEGRAM_BOT_TOKEN`   | —       | Telegram bot token from BotFather (required) |
| `TELEGRAM_CHAT_ID`     | —       | Target channel/chat ID (required) |
| `TOP_COINS`            | —       | Comma-separated USDT-M Futures symbols, e.g. `BTCUSDT,ETHUSDT` (required) |
| `POLL_SECONDS`         | `60`    | Seconds between price polls |
| `WINDOW_HOURS`         | `24`    | Rolling window in hours used to compute the high baseline |
| `SEND_STARTUP_SUMMARY` | `1`     | Set to `0` to disable the startup Telegram summary message |

## Notes

- Only `USDT` pairs (USDT-M Futures symbols) are supported.
- The bot sends one alert each time the current price breaks the rolling window high and then raises the stored baseline to the current price to prevent immediate re-alerts.
- Keep the process running with `screen`, `tmux`, Docker, or systemd for production.


# BinanceATH Bot (VPS Setup) — Copy/Paste Guide (Non‑Tech)

Ye bot Binance **USDT‑M Futures** me coins monitor karta hai.
Bot Telegram par message bhejta hai jab koi coin **last 24 hours ka high (24h window high)** break karta hai.

---

## 1) VPS me login
Apne laptop/PC se VPS me login karo:

```bash
ssh USER@YOUR_VPS_IP
```

Example:
```bash
ssh root@1.2.3.4
```

---

## 2) Basic packages install karo
Ubuntu/Debian VPS ke liye:

```bash
sudo apt update -y
sudo apt install -y git python3 python3-venv python3-pip
```

---

## 3) Project download (clone)
```bash
cd ~
git clone https://github.com/sanjaymishra17894/BinanceATH.git
cd BinanceATH
```

---

## 4) Python virtual environment banao
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> Note: Har baar run karne se pehle `source .venv/bin/activate` karna hota hai.

---

## 5) Telegram Bot + Chat ID nikaalo (important)
### A) Telegram bot token lo
1. Telegram me `@BotFather` open karo
2. `/newbot` type karo
3. Jo token milega, usko copy kar lo (example: `123456:ABC-DEF...`)

### B) Chat ID lo (jahan message aayega)
Sabse easy way:
1. Apne bot ko Telegram me open karo aur 1 message send karo: `hi`
2. Browser me ye open karo (TOKEN apna paste karo):

```bash
curl -s "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates"
```

3. Output me `chat` ke andar `"id":` milega. Wahi aapka `TELEGRAM_CHAT_ID` hai.

---

## 6) .env file banao (copy/paste)
Project folder ke andar:

```bash
cd ~/BinanceATH
cp .env.example .env
nano .env
```

Ab `.env` me ye values set karo (example):

- `TELEGRAM_BOT_TOKEN=...`  (BotFather token)
- `TELEGRAM_CHAT_ID=...`    (chat id number)
- `TOP_COINS=...`           (comma separated symbols)
- `WINDOW_HOURS=24`
- `WINDOW_INTERVAL=15m`
- `SEND_STARTUP_SUMMARY=1`

### Example `.env` (copy/paste example)
```bash
TELEGRAM_BOT_TOKEN=PASTE_YOUR_TOKEN_HERE
TELEGRAM_CHAT_ID=PASTE_YOUR_CHAT_ID_HERE

# Coins to monitor (comma separated)
TOP_COINS=SAHARAUSDT,MYXUSDT,VVVUSDT,MIRAUSDT,FOLKSUSDT,TAKEUSDT,BUSDT,STBLUSDT,NEWTUSDT

# 24h rolling window config
WINDOW_HOURS=24
WINDOW_INTERVAL=15m

# Start hote hi Telegram pe summary message
SEND_STARTUP_SUMMARY=1
```

Save: `CTRL+O`, Enter, Exit: `CTRL+X`

---

## 7) Bot run karo (test)
```bash
cd ~/BinanceATH
source .venv/bin/activate
set -a; source .env; set +a
python bot.py
```

✅ Agar sab sahi hai to:
- Terminal me logs aayenge (Loaded 24h window high...)
- Telegram par **startup summary** message aayega (coins + 24h highs)

---

## 8) VPS pe bot ko background me 24/7 chalana (screen)
### Screen install:
```bash
sudo apt install -y screen
```

### New screen session:
```bash
screen -S binanceath
```

### Bot start:
```bash
cd ~/BinanceATH
source .venv/bin/activate
set -a; source .env; set +a
python bot.py
```

### Screen detach (bot chalta rahega):
Press:
- `CTRL + A` then `D`

### Wapas screen me jaana:
```bash
screen -r binanceath
```

---

## 9) Update (git pull) ka safe method
Kabhi update karna ho:

```bash
cd ~/BinanceATH
git stash push -m "local changes before update" || true
git pull
source .venv/bin/activate
pip install -r requirements.txt
```

Phir bot restart karo (screen me):

1) `screen -r binanceath`
2) `CTRL + C` (old bot stop)
3) Run commands again:

```bash
cd ~/BinanceATH
source .venv/bin/activate
set -a; source .env; set +a
python bot.py
```

---

## Common Problems (quick fixes)

### Telegram pe message nahi aa raha
- `.env` me `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` galat hoga
- Bot ko chat me start nahi kiya hoga (bot ko message bhejo `hi`)
- VPS me internet issue

### `git pull` error: local changes would be overwritten
Use this:
```bash
git stash push -m "local changes before pull"
git pull
```

---

Done ✅
