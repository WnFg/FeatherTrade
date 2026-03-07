## 1. Core Implementation

- [x] 1.1 Implement `StrategyContext` in `src/trading_system/strategies/context.py` with KV store and service wrappers
- [x] 1.2 Update `BaseStrategy` interface in `src/trading_system/strategies/base_strategy.py` to accept `context` in `on_tick` and `on_bar`
- [x] 1.3 Implement `StatefulStrategy` base class with `NORMAL`, `CLOSING`, and `CLOSED` state transitions
- [x] 1.4 Add integrated Risk Management (Stop-Loss/Take-Profit) logic to `StatefulStrategy`

## 2. Integration and Infrastructure

- [x] 2.1 Update `StrategyManager` to instantiate and inject `StrategyContext` into strategies during market event processing
- [x] 2.2 Implement `IN_FLIGHT` tracking in `ExecutionEngine` to filter concurrent signals from the same strategy
- [x] 2.3 Ensure `ExecutionEngine` clears `IN_FLIGHT` status on FILLED, REJECTED, and CANCELED order events

## 3. Migration and Refactoring

- [x] 3.1 Refactor `MovingAverageCrossover` strategy in `src/trading_system/strategies/moving_average_crossover.py` to use the new `context` signature
- [x] 3.2 Update any existing unit tests for strategies to provide a mock `context`

## 4. Verification

- [x] 4.1 Add unit tests for `StrategyContext` verifying service access and KV store persistence
- [x] 4.2 Add unit tests for `StatefulStrategy` verifying state transitions and automatic liquidation signals
- [x] 4.3 Add integration tests verifying that `ExecutionEngine` ignores signals from a strategy while it has an order `IN_FLIGHT`
