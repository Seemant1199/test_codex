# Automatic Trading Algorithm Starter

This repo provides a lightweight Python starter kit for an automatic trading algorithm with:

- **Backtesting** over historical CSV data.
- **Paper trading** using a streaming CSV feed that mimics live data.
- **Live paper trading** using real-time prices from Zerodha Kite (Indian market data).
- **Optional global demo feed** using real-time prices from Stooq (public market data).

> ⚠️ This code is for educational purposes only and is **not** financial advice.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Backtesting on actual Indian market data

To backtest with real NSE/BSE data, export historical prices from your broker or a data vendor
into a CSV with `timestamp` and `close` columns, then point the feed at that file.

```bash
python - <<'PY'
from algo_trader.backtest import Backtester
from algo_trader.data import CSVDataFeed
from algo_trader.strategy import MovingAverageCrossStrategy

feed = CSVDataFeed("data/your_nse_data.csv")
strategy = MovingAverageCrossStrategy(short_window=3, long_window=7)
backtester = Backtester(strategy)
result = backtester.run(list(feed))

print("Final equity:", result.equity_curve[-1])
print("Trades:")
for trade in result.trades:
    print(trade)
PY
```

## Paper Trading (Simulated)

```bash
python - <<'PY'
from algo_trader.broker import PaperBroker, PaperTrader
from algo_trader.data import CSVStreamingFeed
from algo_trader.strategy import MovingAverageCrossStrategy

feed = CSVStreamingFeed("data/sample_prices.csv", delay_s=0.2)
strategy = MovingAverageCrossStrategy(short_window=3, long_window=7)
trader = PaperTrader(strategy, PaperBroker())
trader.run(feed.stream())

print("Orders:")
for order in trader.broker.orders:
    print(order)
print("Cash:", trader.broker.cash)
print("Position:", trader.broker.position)
PY
```

## Live Paper Trading (Real Market Data)

```bash
python - <<'PY'
from itertools import islice

from algo_trader.broker import PaperBroker, PaperTrader
from algo_trader.data import KiteLiveFeed
from algo_trader.strategy import MovingAverageCrossStrategy

# Example NSE symbols: RELIANCE, TCS, INFY
feed = KiteLiveFeed(
    symbol="RELIANCE",
    api_key="YOUR_API_KEY",
    access_token="YOUR_ACCESS_TOKEN",
    exchange="NSE",
    interval_s=5,
)
strategy = MovingAverageCrossStrategy(short_window=3, long_window=7)
trader = PaperTrader(strategy, PaperBroker())

for bar in islice(feed.stream(), 10):
    trader.run([bar])
    print(bar, trader.broker.cash, trader.broker.position)
PY
```

## Live Trading (Real Money via Broker API)

To place real orders, use the `KiteBroker` wrapper with your Zerodha Kite Connect credentials.
You will need to generate an **access token** via the Kite Connect login flow and supply it here.

```bash
python - <<'PY'
from algo_trader.broker import KiteBroker

broker = KiteBroker(
    api_key="YOUR_API_KEY",
    access_token="YOUR_ACCESS_TOKEN",
    exchange="NSE",
)

# Example: market buy 1 share of RELIANCE
order_id = broker.execute(symbol="RELIANCE", action="buy", quantity=1)
print("Order placed:", order_id)
PY
```

> ⚠️ Real-money trading requires a funded brokerage account, API approval, and compliant usage.

## Optional Global Demo Feed (Stooq)

If you want a free, public demo feed (not India-specific), you can still use Stooq:

```bash
python - <<'PY'
from itertools import islice

from algo_trader.broker import PaperBroker, PaperTrader
from algo_trader.data import StooqLiveFeed
from algo_trader.strategy import MovingAverageCrossStrategy

feed = StooqLiveFeed("aapl.us", interval_s=15)
strategy = MovingAverageCrossStrategy(short_window=3, long_window=7)
trader = PaperTrader(strategy, PaperBroker())

for bar in islice(feed.stream(), 5):
    trader.run([bar])
    print(bar, trader.broker.cash, trader.broker.position)
PY
```

## Extending

- Add new strategy classes in `algo_trader/strategy.py`.
- Replace `CSVDataFeed` with another market data API feed.
- Replace `PaperBroker` with another broker API once you are ready.
