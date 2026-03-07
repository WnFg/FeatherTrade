## Context

The current trading system framework includes an `EventEngine`, `StrategyManager`, and `BacktestSimulator` (acting as the execution engine). Order execution currently tracks quantity and average cost but does not account for cash constraints or total equity updates.

## Goals / Non-Goals

**Goals:**
- **Centralized State**: Implement an `AccountService` to serve as the single source of truth for user funds.
- **Synchronous Validation**: Provide a way for the `ExecutionEngine` to check solvency before accepting a `BUY` order.
- **Event-Driven Updates**: Use the `EventEngine` to propagate trade results (fills) to the `AccountService`.

**Non-Goals:**
- **Multi-Account Support**: This design assumes a single primary account for simplicity.
- **Persistence**: Initial implementation will be in-memory (persistent storage can be added later).
- **Complex Margin Logic**: Initial implementation will use a simple cash-basis model.

## Decisions

### 1. AccountService as the Single Source of Truth
The `AccountService` will hold the authoritative state for both cash balances and all asset positions. 
- **Rationale**: Eliminates synchronization issues and "state divergence" risks by centralizing all financial and portfolio data.
- **Alternatives**: Redundant tracking in the executor. *Decision rationale*: Redundancy increases complexity and the likelihood of bugs in backtesting and live trading.

### 2. Pre-Submission Resource Validation
The `ExecutionEngine` (or `StrategyManager`) will perform synchronous calls to `AccountService` to validate both cash (for BUYS) and existing positions (for SELLS) before an order is accepted.
- **Rationale**: Prevents the system from attempting invalid trades (e.g., shorting when not intended or buying without funds).
- **Alternatives**: Asynchronous validation. *Decision rationale*: Synchronous validation provides immediate feedback and simplifies the state machine.

### 3. Stateless Execution
The `ExecutionEngine` (e.g., `BacktestSimulator`) will be refactored to remove internal state for positions and balances. It will focus purely on order matching and fill generation.
- **Rationale**: Keeps the execution component lightweight and focused on its primary responsibility.
- **Alternatives**: Maintaining a local cache. *Decision rationale*: A local cache is unnecessary if the `AccountService` is optimized for fast synchronous lookups.

## Risks / Trade-offs

- **[Risk] Sync Latency** → Frequent synchronous calls to `AccountService` could impact throughput. **Mitigation**: Ensure `AccountService` lookups are O(1) using efficient in-memory data structures.
- **[Risk] Event Order Integrity** → If fill events are processed out of order, the account state could temporarily drift. **Mitigation**: Use sequential event processing or include versioning/timestamps in fill events.
