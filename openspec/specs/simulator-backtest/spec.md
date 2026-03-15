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

### Requirement: 回测结果查询
`BacktestRunner.get_results()` SHALL 返回一个 `BacktestResult` 结构化对象，包含最终现金、持仓、净值曲线、成交记录及绩效指标；同时保留原有的控制台打印输出（可通过 `verbose=False` 关闭）。此外，当 `save_report=True` 时，SHALL 自动调用 `BacktestVisualizer.plot()` 生成可视化报告文件。

#### Scenario: 返回结构化结果对象
- **WHEN** 调用 `runner.get_results()`
- **THEN** 返回值为 `BacktestResult` 实例，而非 `None`

#### Scenario: 默认保留控制台输出
- **WHEN** 调用 `runner.get_results()`（不传参数）
- **THEN** 控制台仍打印最终现金和持仓信息

#### Scenario: 关闭控制台输出
- **WHEN** 调用 `runner.get_results(verbose=False)`
- **THEN** 控制台无任何打印输出，仅返回 `BacktestResult` 对象

#### Scenario: 触发可视化报告生成
- **WHEN** 调用 `runner.get_results(save_report=True, report_path='my_report.html')`
- **THEN** 在 `my_report.html` 路径生成可视化报告文件

