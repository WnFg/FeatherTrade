## 1. Project Setup & Core Event Engine

- [x] 1.1 Create the initial directory structure for the framework (core, modules, strategies, data).
- [x] 1.2 Implement the `EventEngine` for managing an event-driven queue and callback registration.
- [x] 1.3 Define core `Event` types: `MarketEvent`, `SignalEvent`, `OrderEvent`, `FillEvent`.
- [x] 1.4 Implement normalized data classes for `Tick` and `Bar`.

## 2. External Signal Module Implementation

- [x] 2.1 Define the `AbstractSignalSource` base class with methods for starting and stopping the feed.
- [x] 2.2 Implement a `CSVDataFeed` adapter that reads historical data from a CSV file and produces `MarketEvent` objects.
- [x] 2.3 Implement basic data validation to ensure incoming market data meets the system's normalization standards.

## 3. Execution Engine & Simulator Implementation

- [x] 3.1 Define the `AbstractExecutor` base class for handling order placement and cancellation.
- [x] 3.2 Implement the `BacktestSimulator` implementing `AbstractExecutor`, capable of filling orders based on current simulated market prices.
- [x] 3.3 Add position tracking logic within the execution engine to maintain current holdings and average costs.

## 4. Strategy Module Implementation

- [x] 4.1 Define the `BaseStrategy` abstract base class with standardized lifecycle methods (`on_tick`, `on_bar`, `on_signal`).
- [x] 4.2 Implement the `StrategyManager` to coordinate between the `EventEngine`, `SignalSources`, and `Executors`.
- [x] 4.3 Create a simple `TrendFollowingStrategy` (e.g., Moving Average Crossover) as a reference implementation.

## 5. Backtesting Integration & Validation

- [x] 5.1 Implement a `BacktestRunner` utility to orchestrate a full backtest session given a strategy, historical data, and initial capital.
- [x] 5.2 Create unit tests for the `EventEngine` to ensure correct event propagation.
- [x] 5.3 Create integration tests for the `BacktestSimulator` to verify order fill logic and position management.
- [x] 5.4 Run a complete sample backtest session and verify the generated trade logs.
