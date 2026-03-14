## Why

当前回测系统（`BacktestRunner`）仅通过 `print()` 输出最终持仓和现金，缺乏可视化能力。用户无法直观地看到策略在历史行情上的表现、买卖时机及资金曲线变化，极大地限制了策略评估效率。

## What Changes

- **新增** 回测数据采集器（`BacktestRecorder`）：在回测过程中以事件订阅方式无侵入地收集成交记录、逐 Bar 净值、信号等数据，并在回测结束后提供结构化结果对象。
- **新增** 可视化报告生成器（`BacktestVisualizer`）：基于采集到的数据，生成含价格走势图、买卖点标注、资金曲线、回撤曲线、持仓量变化等图表的交互式 HTML 报告或静态图片。
- **修改** `BacktestRunner.get_results()`：返回结构化的 `BacktestResult` 对象，并支持可选的可视化输出。
- **修改** `run_backtest.py` 入口脚本：支持 `--visualize` 参数以触发可视化报告生成。

## Capabilities

### New Capabilities
- `backtest-recorder`: 在回测运行期间通过事件总线订阅 `FillEvent` 和 `MarketEvent`，无侵入地采集逐笔成交、逐 Bar 价格及净值数据，并在回测结束后汇总为结构化的 `BacktestResult`（含成交记录列表、净值序列、回撤序列、绩效摘要等）。
- `backtest-visualizer`: 接收 `BacktestResult`，生成包含以下图表的可视化报告：价格 K 线 / 折线图叠加买卖点标注、资金净值曲线、回撤曲线、持仓量时序图；支持输出为交互式 HTML（基于 Plotly）或静态 PNG（基于 Matplotlib）。

### Modified Capabilities
- `simulator-backtest`: `BacktestRunner` 新增返回 `BacktestResult` 的接口，并在 `run()` 中自动注册 `BacktestRecorder`。

## Impact

- **代码**：新增 `core/backtest_recorder.py`、`core/backtest_visualizer.py`；修改 `core/backtest_runner.py`、`run_backtest.py`。
- **依赖**：引入 `plotly`（交互式图表）和/或 `matplotlib`（静态图表），需更新 `requirements.txt`。
- **接口**：`get_results()` 返回值从 `None` 变为 `BacktestResult` dataclass，属于 **BREAKING** 变更（当前无外部调用方，影响仅限 `run_backtest.py`）。
- **数据**：不修改现有事件模型；仅新增事件订阅者，对现有事件流无影响。
