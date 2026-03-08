# Strategy Guide

## Overview

Strategies in FeatherTrade receive market events (`Bar` or `Tick`) and emit trading signals. The framework provides two base classes:

- **`BaseStrategy`** — minimal interface; implement `on_bar` and `on_tick`
- **`StatefulStrategy`** — extends `BaseStrategy` with a state machine, position tracking, ATR stop-loss support, and an `on_fill` callback

## StrategyContext

Every `on_bar` / `on_tick` call receives a `StrategyContext` object:

| Attribute | Type | Description |
|---|---|---|
| `context.account` | `AccountService` | Access cash, positions, `has_funds()` |
| `context.execution` | `AbstractExecutor` | The active executor (simulator or live) |
| `context.factors` | `FactorService` | Optional — query factor values |
| `context.get(key)` / `context.set(key, val)` | — | Per-strategy in-memory KV store |

## Implementing BaseStrategy

```python
from src.trading_system.strategies.base_strategy import BaseStrategy
from src.trading_system.data.market_data import Bar, Tick
from src.trading_system.strategies.context import StrategyContext

class MyStrategy(BaseStrategy):
    def on_bar(self, bar: Bar, context: StrategyContext):
        cash = context.account.cash
        if cash > bar.close * 100:
            self.send_signal(bar.symbol, "BUY", 100, bar.close)

    def on_tick(self, tick: Tick, context: StrategyContext):
        pass  # optional
```

`send_signal(symbol, side, quantity, price)` emits a `SignalEvent` into the engine. Use `price=0.0` for market orders.

## Implementing StatefulStrategy

`StatefulStrategy` adds:
- **State machine**: `NORMAL` → `CLOSING` → `CLOSED`
- **`check_risk(data, context) -> bool`**: called on every bar/tick while in position; return `True` to trigger liquidation
- **`on_fill(fill_data)`**: called when an order for this strategy is confirmed filled; use it to update position tracking
- **`record_entry(price, qty)`**: marks a pending BUY in-flight

```python
from src.trading_system.strategies.stateful_strategy import StatefulStrategy, StrategyContext, StrategyState
from src.trading_system.data.market_data import Bar, Tick
from typing import Any

class MyTrendStrategy(StatefulStrategy):
    def on_bar_logic(self, bar: Bar, context: StrategyContext):
        # Entry logic
        if self.position_qty == 0 and self._pending_buy_qty == 0:
            qty = self._calc_qty(bar.close, context)
            if qty > 0:
                self.send_signal(bar.symbol, "BUY", qty, bar.close)
                self.record_entry(bar.close, qty)

    def on_tick_logic(self, tick: Tick, context: StrategyContext):
        pass

    def check_risk(self, data: Any, context: StrategyContext) -> bool:
        if self.position_qty > 0:
            price = data.close if hasattr(data, "close") else data.price
            loss_pct = (self.entry_price - price) / self.entry_price
            return loss_pct >= 0.05  # 5% stop-loss
        return False

    def _calc_qty(self, price: float, context: StrategyContext) -> int:
        raw = int(context.account.cash * 0.95 / price)
        return max(0, raw - (raw % 100))  # A-share: multiples of 100
```

## Signal Concurrency Guard

The `BacktestSimulator` / `ExecutionEngine` tracks an `IN_FLIGHT` set per strategy. If a strategy already has an order pending, subsequent signals from that strategy are ignored until the order is filled or cancelled. This prevents double-buying from fast signal loops.

## State Machine

```
NORMAL
  ├── check_risk() == True  →  CLOSING  →  send liquidation signal  →  CLOSED
  └── on_bar_logic() / on_tick_logic() runs normally

CLOSING
  └── re-send liquidation signal each bar until filled

CLOSED
  └── all events ignored
```

## Built-in Strategies

| Class | File | Description |
|---|---|---|
| `MovingAverageCrossover` | `moving_average_crossover.py` | Fast/slow SMA crossover |
| `AtrTrendStrategy` | `atr_trend_strategy.py` | ATR-based trend + volatility stop |
| `DualMATrendStrategy` | `dual_ma_trend_strategy.py` | Dual MA + 60-day trend filter + ATR stop, A-share hand sizing |

## Wiring a Strategy into Backtest

See the [README](../README.md) or `run_factor_backtest.py` for a complete wiring example.
