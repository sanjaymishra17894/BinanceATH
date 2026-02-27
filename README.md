# Binance ATH Bot

A trading/monitoring automation bot designed for Binance market data and strategy execution. This README explains, in practical detail, what the bot is intended to do and exactly how to run it on a VPS step by step.

## What this bot does

At a high level, this bot is built to:

1. **Connect to Binance APIs** (market data and/or account endpoints).
2. **Track ATH-related price behavior** for configured trading pairs.
3. **Apply strategy logic** (for example: signal generation, alerting, paper/live order workflow).
4. **Trigger actions** such as logging, notifications, and optional order execution.
5. **Run continuously** as a background process on a VPS.

Depending on your implementation, the bot can be configured to:

- Watch one or many symbols (e.g., `BTCUSDT`, `ETHUSDT`).
- Use spot or futures endpoints.
- Send alerts via Telegram/Discord/email.
- Place live orders only when risk and signal conditions match.

> **Important:** Crypto trading is risky. Test with paper mode/sandbox and very small capital before any live deployment.

---

## What you need before running

Prepare these items first:

### 1) VPS server

- Ubuntu 22.04 LTS (recommended)
- Minimum: 1 vCPU, 1 GB RAM, 15+ GB disk
- Public IP + SSH access

### 2) Local machine

- Terminal access (Linux/macOS shell, or PowerShell + SSH on Windows)
- SSH key (recommended) or password login

### 3) Binance account + API keys

- Create API key/secret in Binance account settings.
- Restrict key permissions to only what is needed.
- If possible, whitelist your VPS IP.
- Never commit API keys into Git.

### 4) Software dependencies on VPS

- `git`
- `python3`
- `python3-venv`
- `python3-pip`
- `tmux` or `screen` (optional)
- `ufw` firewall (recommended)

---

## Step-by-step: run on VPS

## Step 1 — Connect to VPS

From your local terminal:

```bash
ssh <username>@<vps_ip>
```

Example:

```bash
ssh ubuntu@203.0.113.10
```

## Step 2 — Update system packages

```bash
sudo apt update && sudo apt upgrade -y
```

## Step 3 — Install required packages

```bash
sudo apt install -y git python3 python3-venv python3-pip tmux ufw
```

## Step 4 — Configure basic firewall (recommended)

Allow SSH and enable firewall:

```bash
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw status
```

## Step 5 — Clone your repository

```bash
git clone <your_repo_url> BinanceATH
cd BinanceATH
```

## Step 6 — Create Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should now see `(.venv)` in your shell prompt.

## Step 7 — Install Python dependencies

If you have `requirements.txt`:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If you use Poetry/Pipenv, install with your chosen tool instead.

## Step 8 — Create environment configuration

Create a `.env` file in the project root:

```bash
nano .env
```

Add values similar to the following (adjust keys to your app):

```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
BINANCE_TESTNET=true
TRADING_PAIR=BTCUSDT
TIMEFRAME=1m
RISK_PER_TRADE=0.01
MAX_DAILY_LOSS=0.03
TELEGRAM_BOT_TOKEN=optional_token
TELEGRAM_CHAT_ID=optional_chat_id
```

Save and exit.

## Step 9 — (Optional but recommended) dry run the bot

Run once in foreground to verify startup:

```bash
python main.py
```

If your entry file is different, replace `main.py` with your actual start file.

## Step 10 — Run bot in a persistent session with tmux

Start tmux:

```bash
tmux new -s binance-bot
```

Run bot:

```bash
cd ~/BinanceATH
source .venv/bin/activate
python main.py
```

Detach from tmux (bot keeps running):

- Press `Ctrl+B`, then `D`

Re-attach later:

```bash
tmux attach -t binance-bot
```

## Step 11 — Auto-start on reboot with systemd (recommended for production)

Create service file:

```bash
sudo nano /etc/systemd/system/binance-ath-bot.service
```

Paste (edit paths/user):

```ini
[Unit]
Description=Binance ATH Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/BinanceATH
Environment="PATH=/home/ubuntu/BinanceATH/.venv/bin"
ExecStart=/home/ubuntu/BinanceATH/.venv/bin/python /home/ubuntu/BinanceATH/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable + start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable binance-ath-bot
sudo systemctl start binance-ath-bot
```

Check status/logs:

```bash
sudo systemctl status binance-ath-bot
journalctl -u binance-ath-bot -f
```

---

## Operational checklist

Before enabling live trading, verify:

- API keys loaded correctly.
- Bot starts without exceptions.
- Logs are being written.
- Time sync on VPS is correct (`timedatectl status`).
- Risk limits are configured.
- Testnet or paper mode works first.

---

## Security best practices

- Use a dedicated Binance API key for this bot.
- Disable withdrawal permission on API key.
- Restrict API key by IP (your VPS IP).
- Keep `.env` out of Git (`.gitignore`).
- Rotate API keys periodically.
- Apply OS updates regularly.

---

## Common commands

Restart service:

```bash
sudo systemctl restart binance-ath-bot
```

Stop service:

```bash
sudo systemctl stop binance-ath-bot
```

Tail logs:

```bash
journalctl -u binance-ath-bot -n 100 --no-pager
```

Check running Python processes:

```bash
ps aux | grep python
```

---

## Notes

- Replace placeholders (`<username>`, `<vps_ip>`, `<your_repo_url>`) with real values.
- Replace `main.py` if your project uses another entrypoint.
- If your bot supports Docker, you can deploy with Docker + Compose as an alternative.
