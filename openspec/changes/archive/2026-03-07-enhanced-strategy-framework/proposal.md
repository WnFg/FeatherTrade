## Why

The current strategy module is limited to simple signal generation and lacks direct access to system state (accounts, factors) and persistent local storage. Additionally, without a built-in state machine for risk management and a concurrency protection mechanism, strategies are prone to over-trading or missing complex exit conditions (like stop-losses) in a realistic environment.

## What Changes

- **Strategy Context**: Introduce a `context` parameter to all primary strategy methods. This object will encapsulate the execution engine interface, external states (account, factor registry), and provide a memory-level Key-Value (KV) store for strategy-specific persistence.
- **Enhanced Strategy Template**: Provide a base class/template that includes:
  - Built-in Risk Management: Position sizing limits, and automated Stop-Loss (SL) / Take-Profit (TP) logic.
  - State Machine: Logic to transition between `NORMAL`, `CLOSING` (liquidation in progress), and `CLOSED` (fully liquidated) states.
- **Signal Concurrency Protection**: Implement a state-tracking mechanism for strategy execution.
  - Strategies will have `IDLE` and `IN_FLIGHT` states.
  - **BREAKING**: The execution engine will ignore new signals from a strategy that is already in the `IN_FLIGHT` state to prevent unintended over-positioning.

## Capabilities

### New Capabilities
- `strategy-context`: Encapsulation of external services and memory-level KV storage for strategy use.

### Modified Capabilities
- `strategy-module`: Update the strategy interface to accept `context`, and introduce the state-machine-driven template with integrated risk rules.
- `execution-engine`: Add concurrency protection logic to track strategy execution states (`IDLE`/`IN_FLIGHT`) and filter redundant signals.

## Impact

- **`src/trading_system/strategies/base_strategy.py`**: Interface changes to include `context`.
- **`src/trading_system/core/strategy_manager.py`**: Logic to instantiate and inject the `context`.
- **`src/trading_system/modules/execution_engine.py`**: Implementation of the `IN_FLIGHT` signal filter.
- **Strategy Implementations**: All existing strategies will need to be updated to support the new `context` signature.
