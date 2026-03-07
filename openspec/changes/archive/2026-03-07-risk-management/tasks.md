## 1. Risk Management Framework Setup

- [x] 1.1 Create `src/trading_system/risk/` directory and initialize it as a python package.
- [x] 1.2 Define the `RiskSignalEvent` in `src/trading_system/core/event_types.py`.
- [x] 1.3 Create the `BaseRiskStrategy` abstract base class in `src/trading_system/risk/base_risk.py` with an evaluation method.
- [x] 1.4 Implement the `RiskManager` class in `src/trading_system/risk/risk_manager.py` that listens to market and fill events to evaluate active positions against loaded risk strategies.

## 2. Pluggable Risk Strategies Implementation

- [x] 2.1 Implement a `FixedStopLossStrategy` inheriting from `BaseRiskStrategy`.
- [x] 2.2 Implement a `FixedTakeProfitStrategy` inheriting from `BaseRiskStrategy`.

## 3. Execution Engine Integration

- [x] 3.1 Update the `StrategyManager` or a new coordinator to subscribe to `RiskSignalEvent`.
- [x] 3.2 Implement logic in `StrategyManager` to convert a `RiskSignalEvent` into an immediate market order.
- [x] 3.3 Ensure the execution engine processes this order to close the position.

## 4. Integration & Validation

- [x] 4.1 Update `BacktestRunner` to instantiate the `RiskManager` and register sample risk strategies (e.g., stop-loss) for the run.
- [x] 4.2 Create a specific backtest scenario where price drops significantly, validating that the stop-loss strategy correctly triggers and closes the position.
- [x] 4.3 Add unit tests for `RiskManager` and `FixedStopLossStrategy`.