## Why

The system needs a more sophisticated trend-following strategy that utilizes Average True Range (ATR) for volatility-based risk management (stop-loss, take-profit, and position sizing). This demonstrates the power of the newly implemented `StatefulStrategy` framework and provides a robust template for real-world trading.

## What Changes

- **ATR Trend Strategy**: Implement a new strategy class `ATRTrendStrategy` inheriting from `StatefulStrategy`.
- **Volatility-Based Risk**: Use ATR to calculate dynamic stop-loss and take-profit levels.
- **Controlled Position Sizing**: Implement a constraint where the maximum position size is limited to 5% of total account capital.
- **Unit-Based Ingestion**: Logic to buy 1 'UNIT' (defined by ATR-based risk) when trend conditions are met.

## Capabilities

### New Capabilities
- `atr-trend-strategy`: Implementation of a trend-following logic using ATR for exit signals and position sizing.

### Modified Capabilities
- (None)

## Impact

- **`src/trading_system/strategies/atr_trend_strategy.py`**: New strategy implementation.
- **`src/trading_system/core/strategy_manager.py`**: Integration for the new strategy.
- **Strategy Selection**: The new strategy will be available for backtests and live trading.
