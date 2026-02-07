"""Backtesting engine for strategies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .data import Bar
from .strategy import BaseStrategy, StrategyState


@dataclass
class Trade:
    timestamp: str
    action: str
    price: float
    shares: int
    cash: float
    position: int


@dataclass
class BacktestResult:
    equity_curve: List[float]
    trades: List[Trade]


class Backtester:
    """Run a strategy over historical data."""

    def __init__(self, strategy: BaseStrategy, initial_cash: float = 10000.0):
        self.strategy = strategy
        self.initial_cash = initial_cash

    def run(self, bars: List[Bar]) -> BacktestResult:
        state = StrategyState()
        cash = self.initial_cash
        position = 0
        equity_curve: List[float] = []
        trades: List[Trade] = []

        for bar in bars:
            signal = self.strategy.on_bar(state, bar)
            if signal == "buy" and cash > 0:
                shares = int(cash // bar.close)
                if shares > 0:
                    cash -= shares * bar.close
                    position += shares
                    state.position = position
                    trades.append(
                        Trade(
                            timestamp=bar.timestamp,
                            action="buy",
                            price=bar.close,
                            shares=shares,
                            cash=cash,
                            position=position,
                        )
                    )
            elif signal == "sell" and position > 0:
                cash += position * bar.close
                trades.append(
                    Trade(
                        timestamp=bar.timestamp,
                        action="sell",
                        price=bar.close,
                        shares=position,
                        cash=cash,
                        position=0,
                    )
                )
                position = 0
                state.position = 0

            equity = cash + position * bar.close
            equity_curve.append(equity)

        return BacktestResult(equity_curve=equity_curve, trades=trades)
