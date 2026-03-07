## 1. Foundation and Indicators

- [x] 1.1 Create `src/trading_system/strategies/atr_trend_strategy.py` inheriting from `StatefulStrategy`
- [x] 1.2 Implement sliding window bar tracking for indicator calculations
- [x] 1.3 Implement `_calculate_atr` helper (Average True Range over N periods)
- [x] 1.4 Implement `_calculate_breakout_high` helper (Max high over N periods)

## 2. Trading and Sizing Logic

- [x] 2.1 Implement ATR-based unit sizing logic in a `_calculate_unit_size` helper (1% risk distance)
- [x] 2.2 Implement 5% total equity position cap within `_calculate_unit_size`
- [x] 2.3 Implement `on_bar_logic` to detect price breakouts and generate BUY signals
- [x] 2.4 Override `check_risk` to implement the volatility-based (non-percent) Stop Loss

## 3. Integration and Verification

- [x] 3.1 Register `ATRTrendStrategy` in a test script or `StrategyManager` context
- [x] 3.2 Create unit tests for indicator calculations (ATR, High)
- [x] 3.3 Create a unit test for the "1 UNIT" calculation logic and the 5% cap
- [x] 3.4 Create an integration test (using sample data) for the complete "Entry -> Set ATR SL -> Risk-Exit" lifecycle
