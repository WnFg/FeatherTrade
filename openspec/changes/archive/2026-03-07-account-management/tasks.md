## 1. Account Service Implementation

- [x] 1.1 Implement the `AccountService` in `src/trading_system/modules/account_service.py` with balance tracking.
- [x] 1.2 Implement the `has_funds(amount)` check in `AccountService`.
- [x] 1.3 Register `AccountService` as a handler for `EventType.FILL` in the `EventEngine` to update cash balance after trades.
- [x] 1.4 Add portfolio valuation logic based on held positions and current market prices.

## 2. Execution Engine Update

- [x] 2.1 Update the `AbstractExecutor` and `BacktestSimulator` in `src/trading_system/modules/execution_engine.py` to accept an `AccountService` dependency.
- [x] 2.2 Modify `submit_order()` in `BacktestSimulator` to perform a synchronous check via the `AccountService` for funds (BUY orders) and positions (SELL orders).
- [x] 2.3 Refactor `BacktestSimulator` to remove all internal position tracking logic, relying solely on `AccountService` for validation and state.
- [x] 2.4 Ensure the simulator correctly triggers the `FillEvent` with the necessary data (including price and side) for the `AccountService` to process.

## 3. Integration & Testing

- [x] 3.1 Update the `BacktestRunner` in `src/trading_system/core/backtest_runner.py` to instantiate and link the `AccountService`.
- [x] 3.2 Add unit tests for `AccountService` focusing on balance updates and fund checks.
- [x] 3.3 Create a backtesting scenario with insufficient initial capital to verify order rejection logic.
- [x] 3.4 Validate that the final account balance correctly reflects all commissions (if applicable) and trade results.
