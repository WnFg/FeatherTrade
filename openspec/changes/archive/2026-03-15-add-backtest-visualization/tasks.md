## 1. 依赖与项目结构

- [x] 1.1 在 `requirements.txt` 中添加 `plotly>=5.0` 和 `matplotlib>=3.5` 依赖
- [x] 1.2 创建 `backtest/` 目录，添加 `__init__.py`，将现有 `core/backtest_runner.py` 移入或建立引用
- [x] 1.3 新建空文件 `backtest/result.py`、`backtest/recorder.py`、`backtest/visualizer.py`

## 2. 数据模型

- [x] 2.1 在 `backtest/result.py` 中定义 `TradeRecord` dataclass（timestamp, symbol, side, quantity, price, pnl）
- [x] 2.2 在 `backtest/result.py` 中定义 `BacktestResult` dataclass（symbol, initial_capital, final_cash, final_equity, trades, equity_curve, drawdown_curve, position_curve, bars, metrics）
- [x] 2.3 在 `backtest/result.py` 中实现 `compute_drawdown_curve(equity_curve) -> pd.Series` 辅助函数
- [x] 2.4 在 `backtest/result.py` 中实现 `compute_metrics(equity_curve, trades, initial_capital) -> Dict[str, float]`，计算 total_return、max_drawdown、sharpe_ratio、win_rate

## 3. BacktestRecorder 实现

- [x] 3.1 在 `backtest/recorder.py` 中实现 `BacktestRecorder.__init__(self, event_engine, account_service, symbol, initial_capital)`，初始化内部列表（bars, equity_points, position_points, trades）
- [x] 3.2 实现 `_on_market(event)` 方法：提取 Bar，计算瞬时净值和持仓量，追加到对应列表；校验 `bar.close > 0`，否则跳过并打印警告
- [x] 3.3 实现 `_on_fill(event)` 方法：从 `FillEvent.data` 提取字段，计算 pnl（SELL 时用平均成本），构造 `TradeRecord` 并追加到 `trades`
- [x] 3.4 实现 `build_result() -> BacktestResult` 方法：将列表转为 `pd.Series`，调用 `compute_drawdown_curve` 和 `compute_metrics`，返回完整 `BacktestResult`
- [x] 3.5 在 `__init__` 中调用 `event_engine.register(EVENT_MARKET, self._on_market)` 和 `event_engine.register(EVENT_FILL, self._on_fill)`

## 4. BacktestRunner 集成

- [x] 4.1 在 `BacktestRunner.__init__` 中实例化 `BacktestRecorder` 并保存为 `self.recorder`
- [x] 4.2 修改 `BacktestRunner.get_results(self, verbose=True, save_report=False, report_path='backtest_report.html') -> BacktestResult`：调用 `self.recorder.build_result()` 获取结果对象
- [x] 4.3 保留原有 print 逻辑（现金、持仓），由 `verbose` 参数控制开关
- [x] 4.4 当 `save_report=True` 时，调用 `BacktestVisualizer().plot(result, report_path)` 生成报告
- [x] 4.5 更新 `run_backtest.py` 入口：在调用 `get_results()` 时传入 `save_report=True`，并打印报告路径提示

## 5. BacktestVisualizer 实现

- [x] 5.1 在 `backtest/visualizer.py` 中实现 `BacktestVisualizer.plot(result: BacktestResult, output_path: str, backend: str = 'plotly')` 入口方法，根据 backend 分发到 `_plot_plotly` 或 `_plot_matplotlib`
- [x] 5.2 实现 `_compute_buy_sell_markers(result)` 辅助方法：从 `result.trades` 分别提取 BUY / SELL 的时间戳和价格列表
- [x] 5.3 实现 `_plot_plotly(result, output_path)`：用 `make_subplots(rows=4)` 创建四子图（价格折线+买卖标注、净值折线、回撤面积、持仓量阶梯），写出 HTML 文件
- [x] 5.4 实现 `_plot_matplotlib(result, output_path)`：用 `plt.subplots(4, 1, sharex=True)` 创建相同布局，写出 PNG 文件
- [x] 5.5 在 `_plot_plotly` 入口处捕获 `ImportError`，自动回退到 `_plot_matplotlib` 并打印警告；若 Matplotlib 也缺失则仅输出 CSV（trades + equity_curve）

## 6. 单元测试

- [x] 6.1 新建 `tests/test_recorder.py`：用 mock `EventEngine` 和 `AccountService` 测试 `_on_fill` 正确记录 `TradeRecord`
- [x] 6.2 测试 `_on_market` 使净值序列长度等于触发次数，且无持仓时净值等于现金
- [x] 6.3 测试 `build_result()` 在零成交情况下正常返回，metrics 字典包含四个预期键
- [x] 6.4 新建 `tests/test_visualizer.py`：用最小 `BacktestResult` fixture 测试 Plotly 路径生成 HTML 文件（文件存在且 size > 0）
- [x] 6.5 测试 Matplotlib 路径生成 PNG 文件（文件存在且 size > 0）

## 7. 文档与验收

- [x] 7.1 在 `README.md` 或项目文档中补充可视化功能使用说明（如何触发、输出路径、依赖安装）
- [x] 7.2 用 `sample_data.csv` 端到端运行 `run_backtest.py`，确认生成 HTML 报告，浏览器中可见价格图、买卖点标注、净值曲线、回撤曲线和持仓量图
