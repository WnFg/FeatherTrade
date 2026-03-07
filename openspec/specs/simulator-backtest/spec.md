# simulator-backtest Specification

## Purpose
TBD - created by archiving change trend-trading-system-framework. Update Purpose after archive.
## Requirements
### Requirement: Historical Data Replay
The simulator-backtest module SHALL be able to replay historical price data (bars/ticks) and feed it into the strategy and execution engine as if it were real-time data.

#### Scenario: Backtesting Strategy with Historical Bars
- **WHEN** the simulator loads a CSV file containing 1-minute price bars for a symbol
- **THEN** it SHALL provide these bars one-by-one to the strategy according to their timestamps

### Requirement: Fill Simulation
The simulator SHALL simulate the execution of orders based on the replayed price data, including slippage and transaction costs.

#### Scenario: Simulating a Limit Order Fill
- **WHEN** a BUY limit order is submitted at $100 and the next historical tick price is $99.50
- **THEN** the simulator SHALL fill the order at $100 (or better) and update the engine status to FILLED

