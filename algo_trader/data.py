"""Market data feeds for backtesting and paper trading."""

from __future__ import annotations

import csv
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import requests

try:
    from kiteconnect import KiteConnect
except ImportError:  # pragma: no cover - optional dependency
    KiteConnect = None


@dataclass(frozen=True)
class Bar:
    timestamp: str
    close: float


class CSVDataFeed:
    """Load historical bars from a CSV file for backtesting."""

    def __init__(self, csv_path: str | Path):
        self.csv_path = Path(csv_path)

    def __iter__(self) -> Iterator[Bar]:
        with self.csv_path.open("r", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                yield Bar(timestamp=row["timestamp"], close=float(row["close"]))


class CSVStreamingFeed:
    """Stream bars from a CSV file to mimic a live price feed."""

    def __init__(self, csv_path: str | Path, delay_s: float = 1.0):
        self.csv_path = Path(csv_path)
        self.delay_s = delay_s

    def stream(self) -> Iterator[Bar]:
        with self.csv_path.open("r", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                yield Bar(timestamp=row["timestamp"], close=float(row["close"]))
                if self.delay_s > 0:
                    time.sleep(self.delay_s)


class StooqLiveFeed:
    """Fetch near-real-time prices from Stooq's public CSV endpoint."""

    def __init__(self, symbol: str, interval_s: float = 15.0, timeout_s: float = 10.0):
        self.symbol = symbol.lower()
        self.interval_s = interval_s
        self.timeout_s = timeout_s

    def stream(self) -> Iterator[Bar]:
        url = f"https://stooq.com/q/l/?s={self.symbol}&f=sd2t2ohlcv&h&e=csv"
        while True:
            response = requests.get(url, timeout=self.timeout_s)
            response.raise_for_status()
            lines = response.text.strip().splitlines()
            if len(lines) >= 2:
                row = next(csv.DictReader(lines))
                timestamp = f"{row['Date']} {row['Time']}"
                yield Bar(timestamp=timestamp, close=float(row["Close"]))
            if self.interval_s > 0:
                time.sleep(self.interval_s)


class KiteLiveFeed:
    """Stream live prices from Zerodha Kite Connect for Indian markets."""

    def __init__(
        self,
        symbol: str,
        api_key: str,
        access_token: str,
        exchange: str = "NSE",
        interval_s: float = 5.0,
    ):
        if KiteConnect is None:
            raise ImportError(
                "kiteconnect is not installed. Install it with `pip install kiteconnect`."
            )
        self.symbol = symbol
        self.exchange = exchange
        self.interval_s = interval_s
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)

    def stream(self) -> Iterator[Bar]:
        full_symbol = f"{self.exchange}:{self.symbol}"
        while True:
            quote = self.kite.quote(full_symbol)
            data = quote.get(full_symbol, {})
            close = data.get("last_price")
            if close is not None:
                timestamp = data.get("timestamp") or data.get("last_trade_time")
                yield Bar(timestamp=str(timestamp), close=float(close))
            if self.interval_s > 0:
                time.sleep(self.interval_s)
