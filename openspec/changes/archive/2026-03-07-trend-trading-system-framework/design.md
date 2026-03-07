## Context

The requirement is for a new, modular trend trading system framework. Currently, no such framework exists in the repository. The system needs to support strategy development, real-time execution, signal processing, and historical backtesting.

## Goals / Non-Goals

**Goals:**
- **Modular Design**: Ensure components like strategies, executors, and signal sources are decoupled and interchangeable.
- **Event-Driven Architecture**: Use an event loop to handle market data updates, signal generation, and order execution.
- **Pluggable Adapters**: Support multiple data sources (REST, WebSocket, CSV) and execution venues (Brokers, Simulators).
- **Backtesting Integrity**: Implement a discrete-event simulator to ensure backtest accuracy and prevent look-ahead bias.

**Non-Goals:**
- **Low-Latency/HFT**: This design does not prioritize microsecond-level latency.
- **Advanced Portfolio Optimization**: Focus is on single or multi-asset trend-following logic, not complex portfolio-level risk parity or optimization.
- **GUI**: The initial framework will be CLI and API-driven.

## Decisions

### 1. Event-Driven Core
The system will center around an `EventEngine` that manages an event queue.
- **Rationale**: This allows for a clean separation of concerns. Strategies produce `SignalEvents`, the `ExecutionEngine` handles `OrderEvents`, and the `SignalModule` produces `MarketEvents`.
- **Alternatives**: A simple procedural loop. *Decision rationale*: Procedural loops become complex when handling multiple asynchronous data sources and simultaneous strategy executions.

### 2. Unified Interface for Live/Simulation
The `ExecutionEngine` will interact with an `AbstractExecutor` interface. Both the `LiveBrokerAdapter` and the `BacktestSimulator` will implement this interface.
- **Rationale**: Allows the same strategy code to run in both backtesting and live environments without modification.
- **Alternatives**: Separate logic for backtesting. *Decision rationale*: Increases maintenance burden and risks "backtest-live divergence".

### 3. Strategy State Management
Strategies will be implemented as classes inheriting from a `BaseStrategy` ABC.
- **Rationale**: Enforces a consistent contract (init, on_tick, on_bar, on_signal).
- **Alternatives**: Functional approach or script-based strategies. *Decision rationale*: OOP allows for easier state management and inheritance of common indicators/utils.

### 4. Normalized Data Format
All incoming market data will be converted into a standard `MarketData` object (e.g., `Tick` or `Bar`).
- **Rationale**: Decouples strategies from specific vendor data formats.
- **Alternatives**: Passing raw dictionaries/JSON. *Decision rationale*: Reduces type errors and improves developer experience through better IDE support.

## Risks / Trade-offs

- **[Risk] Data Synchronization** → Multiple asset data arriving at different rates during live trading. **Mitigation**: Use a central event loop that processes events in the order they arrive, and ensure all data points are timestamped at the source.
- **[Risk] Backtest Look-ahead Bias** → Accidentally using information from "future" bars during simulation. **Mitigation**: The simulator will strictly manage the "current time" and only reveal data points that are chronologically valid.
- **[Risk] Complexity of Event Loop** → Debugging an event-driven system can be harder than procedural code. **Mitigation**: Implement robust logging and an optional "synchronous mode" for simpler debugging of strategy logic.

## Open Questions

- Should we use an existing event-loop framework (like Python's `asyncio`) or implement a custom lightweight one?
- What specific data vendors (e.g., Interactive Brokers, Binance, Yahoo Finance) should we prioritize for initial adapters?
