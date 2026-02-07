"""Paper trading components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, List

from .data import Bar

try:
    from kiteconnect import KiteConnect
except ImportError:  # pragma: no cover - optional dependency
    KiteConnect = None
from .strategy import BaseStrategy, StrategyState


@dataclass
class Order:
    timestamp: str
    action: str
    price: float
    shares: int


class PaperBroker:
    """A simple paper broker that tracks cash and positions."""

    def __init__(self, starting_cash: float = 10000.0):
        self.cash = starting_cash
        self.position = 0
        self.orders: List[Order] = []

    def execute(self, timestamp: str, action: str, price: float) -> None:
        if action == "buy":
            shares = int(self.cash // price)
            if shares > 0:
                self.cash -= shares * price
                self.position += shares
                self.orders.append(Order(timestamp, action, price, shares))
        elif action == "sell" and self.position > 0:
            shares = self.position
            self.cash += shares * price
            self.position = 0
            self.orders.append(Order(timestamp, action, price, shares))


class PaperTrader:
    """Run a strategy against a streaming data feed."""

    def __init__(self, strategy: BaseStrategy, broker: PaperBroker):
        self.strategy = strategy
        self.broker = broker
        self.state = StrategyState()

    def run(self, stream: Iterator[Bar]) -> None:
        for bar in stream:
            signal = self.strategy.on_bar(self.state, bar)
            if signal in {"buy", "sell"}:
                self.broker.execute(bar.timestamp, signal, bar.close)
                self.state.position = self.broker.position


class KiteBroker:
    """Execute live orders using Zerodha Kite Connect."""

    def __init__(
        self,
        api_key: str,
        access_token: str,
        exchange: str = "NSE",
        product: str = "CNC",
        order_type: str = "MARKET",
        variety: str = "regular",
    ):
        if KiteConnect is None:
            raise ImportError(
                "kiteconnect is not installed. Install it with `pip install kiteconnect`."
            )
        self.exchange = exchange
        self.product = product
        self.order_type = order_type
        self.variety = variety
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)

    def execute(self, symbol: str, action: str, quantity: int) -> str:
        transaction_type = "BUY" if action == "buy" else "SELL"
        return self.kite.place_order(
            variety=self.variety,
            exchange=self.exchange,
            tradingsymbol=symbol,
            transaction_type=transaction_type,
            quantity=quantity,
            order_type=self.order_type,
            product=self.product,
        )
