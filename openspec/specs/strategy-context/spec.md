## ADDED Requirements

### Requirement: Strategy Context Injection
The system SHALL provide a `StrategyContext` object to every strategy during initialization and when processing market events. This object MUST serve as a unified interface to external services.

#### Scenario: Strategy accesses account data
- **WHEN** a strategy calls `context.account.get_balance()`
- **THEN** it SHALL receive the current account balance from the central `AccountService`

### Requirement: Local Memory Key-Value Store
The `StrategyContext` SHALL provide a memory-resident key-value (KV) store for strategies to store and retrieve state during a single execution session.

#### Scenario: Strategy stores state
- **WHEN** a strategy calls `context.state.set("last_trade_price", 150.0)`
- **THEN** subsequent calls to `context.state.get("last_trade_price")` SHALL return 150.0

### Requirement: External Service Access
The `StrategyContext` SHALL provide access to the `FactorRegistry` and the `ExecutionEngine` to allow strategies to query factors and check order statuses.

#### Scenario: Strategy queries a factor
- **WHEN** a strategy calls `context.factors.get_value("sma_20", "AAPL")`
- **THEN** it SHALL receive the latest value of the 'sma_20' factor for 'AAPL' from the `FactorService`
