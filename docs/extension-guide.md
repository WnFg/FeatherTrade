# Extension Guide

This guide describes how to extend the Trend Trading System with new strategies and adapters.

## Strategy Extension

To implement a new trading strategy, inherit from the `BaseStrategy` class in `src/trading_system/strategies/base_strategy.py`.

### Requirements
1. Implement `on_tick(self, tick: Tick)` or `on_bar(self, bar: Bar)`.
2. (Optional) Define a dictionary of `params` for strategy configuration.
3. Use `self.send_signal(symbol, side, quantity, price)` to generate trading signals.

### Example: Simple SMA Cross
```python
from src.trading_system.strategies.base_strategy import BaseStrategy

class MySMAStrategy(BaseStrategy):
    def on_bar(self, bar: Bar):
        # Calculate SMAs and logic
        if fast_sma > slow_sma:
            self.send_signal(bar.symbol, "BUY", 100)
```

## Signal Module Extension (Data Adapters)

To add a new data source (e.g., WebSocket feed, REST API), inherit from `AbstractSignalSource` in `src/trading_system/modules/signal_module.py`.

### Requirements
1. Implement `start()` to begin the data stream.
2. Implement `stop()` to terminate the stream.
3. Normalize incoming data into `Tick` or `Bar` objects and put them into the `EventEngine` as `MarketEvent` instances.

```python
class MyAPIDataFeed(AbstractSignalSource):
    def start(self):
        # Start API connection and loop
        while True:
            data = fetch_api()
            tick = normalize(data)
            self._event_engine.put(MarketEvent(tick))
```

## Execution Extension (Broker Adapters)

To integrate with a new broker or execution venue, inherit from `AbstractExecutor` in `src/trading_system/modules/execution_engine.py`.

### Requirements
1. Implement `submit_order(self, order: Order)` to send a trade request to the venue.
2. Implement `cancel_order(self, order_id: str)` to revoke a pending order.
3. Generate `FillEvent` instances when order status changes (filled, partially filled, canceled).

```python
class MyBrokerAdapter(AbstractExecutor):
    def submit_order(self, order: Order):
        # Call broker API to place trade
        response = broker_api.place_order(order)
        # On success, handle fill (could be asynchronous)
```
