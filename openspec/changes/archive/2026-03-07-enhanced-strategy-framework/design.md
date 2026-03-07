## Context

The current `BaseStrategy` in `src/trading_system/strategies/base_strategy.py` is stateless and decoupled from external services. To support more complex real-world trading logic, we need a way to inject system state (account balance, factors) and maintain strategy-specific persistence without complicating the core event engine. Furthermore, the `ExecutionEngine` needs protection against signal "flooding" during asynchronous order processing.

## Goals / Non-Goals

**Goals:**
- Decouple strategies from service instantiation by using a `StrategyContext` container.
- Implement a `StatefulStrategy` base class that simplifies risk management (SL/TP) and liquidation flows.
- Ensure that each strategy can only have one active signal "in flight" at a time to prevent double-execution.
- Maintain backward compatibility where possible, but allow for a clean break in the strategy interface.

**Non-Goals:**
- Persistent (disk-based) KV storage for strategies in this iteration (memory-only for now).
- Complex cross-strategy margin management (managed by `AccountService` and individual risk rules).

## Decisions

### 1. `StrategyContext` as a Dependency Injection Container
**Decision**: Create a `StrategyContext` class in `src/trading_system/strategies/context.py`. It will wrap references to `AccountService`, `ExecutionEngine`, and `FactorService`.
**Rationale**: This keeps the `on_tick`/`on_bar` signatures clean and allows mocking services easily in unit tests.

### 2. Memory-Resident KV Store per Strategy
**Decision**: Each `StrategyContext` instance will hold a private `dict` for state storage.
**Rationale**: Simplifies logic for simple tracking (e.g., "last_action_time") without requiring a database migration for every new strategy field.

### 3. State-Machine Based `StatefulStrategy`
**Decision**: Introduce `StatefulStrategy` inheriting from `BaseStrategy`. It will manage internal states: `NORMAL` (detecting signals), `CLOSING` (SL/TP triggered, waiting for fills), and `CLOSED` (done).
**Rationale**: Consolidates repetitive liquidation logic (e.g., "if SL triggered, send sell and ignore new buy signals") into the base class.

### 4. `IN_FLIGHT` Tracking in `ExecutionEngine`
**Decision**: The `ExecutionEngine` will maintain a `set` or `dict` of `strategy_id`s that have pending orders. New signals from these IDs will be silently dropped until the pending order is resolved (FILLED or CANCELED).
**Rationale**: Prevent race conditions where a fast-ticking market causes a strategy to send multiple identical BUY orders before the first one is even confirmed.

## Risks / Trade-offs

- **[Risk] State Desync** → **Mitigation**: `StrategyContext` provides real-time access to the source-of-truth services (Account/Execution) rather than caching their state.
- **[Risk] Strategy Locking** → **Mitigation**: Ensure `ExecutionEngine` correctly clears `IN_FLIGHT` status on *all* terminal order states (FILLED, REJECTED, CANCELED).
- **[Risk] Breaking Change** → **Mitigation**: Update the `StrategyManager` to automatically wrap services into a `context` before calling strategy methods.
