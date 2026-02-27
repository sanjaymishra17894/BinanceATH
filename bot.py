import logging
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests

BINANCE_BASE_URL = "https://api.binance.com"
TELEGRAM_BASE_URL = "https://api.telegram.org"


@dataclass
class BotConfig:
    telegram_bot_token: str
    telegram_chat_id: str
    symbols: List[str]
    poll_seconds: int = 60

    @classmethod
    def from_env(cls) -> "BotConfig":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        raw_symbols = os.getenv("TOP_COINS", "").strip()
        poll_seconds = int(os.getenv("POLL_SECONDS", "60"))

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
        )


class BinanceAthWatcher:
    def __init__(self, config: BotConfig):
        self.config = config
        self.session = requests.Session()
        self.current_ath_by_symbol: Dict[str, float] = {}

    def initialize_ath_values(self) -> None:
        for symbol in self.config.symbols:
            ath = self.fetch_all_time_high(symbol)
            self.current_ath_by_symbol[symbol] = ath
            logging.info("Loaded ATH for %s: %s", symbol, ath)

    def fetch_all_time_high(self, symbol: str) -> float:
        endpoint = f"{BINANCE_BASE_URL}/api/v3/klines"
        start_time: Optional[int] = None
        ath = 0.0

        while True:
            params = {
                "symbol": symbol,
                "interval": "1d",
                "limit": 1000,
            }
            if start_time is not None:
                params["startTime"] = start_time

            data = self._get_json(endpoint, params=params)
            if not data:
                break

            for candle in data:
                high = float(candle[2])
                if high > ath:
                    ath = high

            last_open_time = int(data[-1][0])
            next_start_time = last_open_time + 24 * 60 * 60 * 1000
            if len(data) < 1000:
                break
            start_time = next_start_time

            time.sleep(0.1)

        if ath == 0.0:
            raise RuntimeError(f"Unable to fetch ATH for {symbol}")

        return ath

    def fetch_current_price(self, symbol: str) -> float:
        endpoint = f"{BINANCE_BASE_URL}/api/v3/ticker/price"
        payload = self._get_json(endpoint, params={"symbol": symbol})
        return float(payload["price"])

    def send_telegram_message(self, symbol: str, old_ath: float, new_price: float) -> None:
        endpoint = (
            f"{TELEGRAM_BASE_URL}/bot{self.config.telegram_bot_token}/sendMessage"
        )
        message = (
            f"COIN: {symbol}\n"
            f"NEW All Time High: {new_price}\n"
            f"ATH Break: {old_ath}"
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
        logging.info("Sent ATH alert for %s", symbol)

    def monitor_loop(self) -> None:
        while True:
            for symbol in self.config.symbols:
                try:
                    current_price = self.fetch_current_price(symbol)
                    current_ath = self.current_ath_by_symbol[symbol]

                    if current_price > current_ath:
                        self.send_telegram_message(symbol, current_ath, current_price)
                        self.current_ath_by_symbol[symbol] = current_price
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

    config = BotConfig.from_env()
    watcher = BinanceAthWatcher(config)

    watcher.initialize_ath_values()
    logging.info("Started monitoring symbols: %s", ", ".join(config.symbols))
    watcher.monitor_loop()


if __name__ == "__main__":
    main()
