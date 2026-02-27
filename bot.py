import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import requests

BINANCE_BASE_URL = "https://fapi.binance.com"
TELEGRAM_BASE_URL = "https://api.telegram.org"


def load_env_file(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass
class BotConfig:
    telegram_bot_token: str
    telegram_chat_id: str
    symbols: List[str]
    poll_seconds: int = 60
    window_hours: int = 24

    @classmethod
    def from_env(cls) -> "BotConfig":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        raw_symbols = os.getenv("TOP_COINS", "").strip()
        poll_seconds = int(os.getenv("POLL_SECONDS", "60"))
        window_hours = int(os.getenv("WINDOW_HOURS", "24"))

        if not token:
            raise ValueError("Missing TELEGRAM_BOT_TOKEN env variable")
        if not chat_id:
            raise ValueError("Missing TELEGRAM_CHAT_ID env variable")
        if not raw_symbols:
            raise ValueError("Missing TOP_COINS env variable (comma-separated symbols)")

        symbols = [s.strip().upper() for s in raw_symbols.split(",") if s.strip()]
        if not symbols:
            raise ValueError("TOP_COINS produced empty symbol list")
        for symbol in symbols:
            if not symbol.endswith("USDT"):
                raise ValueError(f"Only USDT pairs are supported, got: {symbol}")

        return cls(
            telegram_bot_token=token,
            telegram_chat_id=chat_id,
            symbols=symbols,
            poll_seconds=poll_seconds,
            window_hours=window_hours,
        )


class BinanceAthWatcher:
    def __init__(self, config: BotConfig):
        self.config = config
        self.session = requests.Session()
        self.current_window_high_by_symbol: Dict[str, float] = {}

    def initialize_window_high_values(self) -> None:
        for symbol in self.config.symbols:
            high = self.fetch_window_high(symbol)
            self.current_window_high_by_symbol[symbol] = high
            logging.info(
                "Loaded %dh window high for %s: %s",
                self.config.window_hours, symbol, high,
            )

    def fetch_window_high(self, symbol: str) -> float:
        """Return the highest 'high' price over the last WINDOW_HOURS using 1h klines.

        A single Binance USDT-M Futures API call is made per symbol using
        startTime = now - WINDOW_HOURS and the '1h' interval.  This keeps the
        candle count to at most WINDOW_HOURS candles, making it lightweight
        enough to refresh on every poll cycle.
        """
        endpoint = f"{BINANCE_BASE_URL}/fapi/v1/klines"
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        start_ms = now_ms - self.config.window_hours * 3600 * 1000

        params = {
            "symbol": symbol,
            "interval": "1h",
            "startTime": start_ms,
            "limit": self.config.window_hours + 1,  # +1 to also capture the current open candle
        }

        data = self._get_json(endpoint, params=params)
        if not data:
            raise RuntimeError(f"Unable to fetch window high for {symbol}")

        return max(float(candle[2]) for candle in data)

    def fetch_current_price(self, symbol: str) -> float:
        endpoint = f"{BINANCE_BASE_URL}/fapi/v1/ticker/price"
        payload = self._get_json(endpoint, params={"symbol": symbol})
        return float(payload["price"])

    def send_telegram_message(self, symbol: str, window_high: float, new_price: float) -> None:
        endpoint = (
            f"{TELEGRAM_BASE_URL}/bot{self.config.telegram_bot_token}/sendMessage"
        )
        break_pct = (new_price - window_high) / window_high * 100
        long_tp = new_price * (1 + break_pct / 100)
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        sep = "━" * 20
        message = (
            f"🚀 NEW {self.config.window_hours}h HIGH BREAK (USDT-M Futures)\n"
            f"\n"
            f"Symbol:      {symbol}\n"
            f"Last Price:  {new_price:.6f}\n"
            f"Window:      {self.config.window_hours}h\n"
            f"Window High: {window_high:.6f}\n"
            f"New High:    {new_price:.6f}\n"
            f"Break %:     {break_pct:+.2f}%\n"
            f"\n"
            f"{sep}\n"
            f"📌 Trade Ideas (Example)\n"
            f"Interval: 1h candles\n"
            f"Time (UTC): {now_utc}\n"
            f"\n"
            f"1) 📈 LONG (momentum continuation)\n"
            f"   Entry (Now):              {new_price:.6f}\n"
            f"   Pump % (from {self.config.window_hours}h high):   {break_pct:+.2f}%\n"
            f"   TP (same +% move):        {long_tp:.6f}\n"
            f"\n"
            f"2) 📉 SHORT (retest / mean reversion)\n"
            f"   Entry (Now):              {new_price:.6f}\n"
            f"   TP ({self.config.window_hours}h high level):     {window_high:.6f}\n"
            f"\n"
            f"Notes:\n"
            f"- LONG TP = Entry * (1 + Pump%/100)\n"
            f"- SHORT TP = {self.config.window_hours}h window high\n"
            f"{sep}"
        )

        response = self.session.post(
            endpoint,
            json={
                "chat_id": self.config.telegram_chat_id,
                "text": message,
            },
            timeout=15,
        )
        response.raise_for_status()
        logging.info(
            "Sent %dh high-break alert for %s", self.config.window_hours, symbol
        )

    def monitor_loop(self) -> None:
        # Refresh strategy: the rolling window high is recomputed from Binance
        # klines on every poll cycle.  With a 1h interval this is a single API
        # call per symbol per cycle (at most WINDOW_HOURS candles), which is
        # acceptable even at POLL_SECONDS=60 with O(10) symbols.
        # To prevent spam when a break is detected, the stored baseline is raised
        # to the current price after each alert; the next poll then uses the
        # higher of the fresh API value and the stored baseline.
        while True:
            for symbol in self.config.symbols:
                try:
                    fresh_high = self.fetch_window_high(symbol)
                    # Keep the stored baseline if it is higher (post-alert guard).
                    baseline = max(
                        fresh_high,
                        self.current_window_high_by_symbol.get(symbol, 0.0),
                    )
                    self.current_window_high_by_symbol[symbol] = baseline

                    current_price = self.fetch_current_price(symbol)
                    if current_price > baseline:
                        self.send_telegram_message(symbol, baseline, current_price)
                        # Raise baseline to suppress re-alerts until price pulls
                        # back below the window high.
                        self.current_window_high_by_symbol[symbol] = current_price
                except Exception as exc:
                    logging.exception("Failed monitoring for %s: %s", symbol, exc)

            time.sleep(self.config.poll_seconds)

    def _get_json(self, url: str, params: Dict[str, object]):
        response = self.session.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    load_env_file()
    config = BotConfig.from_env()
    watcher = BinanceAthWatcher(config)

    watcher.initialize_window_high_values()
    logging.info("Started monitoring symbols: %s", ", ".join(config.symbols))
    watcher.monitor_loop()


if __name__ == "__main__":
    main()
