"""Trading strategies and signals."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .data import Bar


@dataclass
class StrategyState:
    position: int = 0
    prices: List[float] = field(default_factory=list)


class BaseStrategy:
    """Base class for strategies."""

    def on_bar(self, state: StrategyState, bar: Bar) -> str:
        raise NotImplementedError


class MovingAverageCrossStrategy(BaseStrategy):
    """Simple moving average crossover strategy."""

    def __init__(self, short_window: int = 5, long_window: int = 20):
        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")
        self.short_window = short_window
        self.long_window = long_window

    def on_bar(self, state: StrategyState, bar: Bar) -> str:
        state.prices.append(bar.close)
        if len(state.prices) < self.long_window:
            return "hold"

        short_ma = sum(state.prices[-self.short_window :]) / self.short_window
        long_ma = sum(state.prices[-self.long_window :]) / self.long_window

        if short_ma > long_ma and state.position <= 0:
            return "buy"
        if short_ma < long_ma and state.position >= 0:
            return "sell"
        return "hold"
