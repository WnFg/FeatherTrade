## Context

当前回测系统（`BacktestRunner`）在运行期间通过事件总线（`EventEngine`）驱动所有模块，但没有任何组件订阅 `FillEvent` / `MarketEvent` 来持久化历史数据。`get_results()` 只打印最终状态，无法回溯成交记录或净值变化。用户只能通过日志猜测策略表现，难以进行系统性评估。

## Goals / Non-Goals

**Goals:**
- 在不修改现有事件流和策略代码的前提下，通过新增事件订阅者采集完整的回测数据
- 提供结构化的 `BacktestResult` 数据对象，包含成交记录、逐 Bar 净值序列、回撤序列、绩效摘要
- 生成可视化报告：价格走势叠加买卖点标注、资金净值曲线、回撤曲线、持仓量时序图
- 支持交互式 HTML 输出（Plotly）和静态 PNG 输出（Matplotlib）

**Non-Goals:**
- 实时（Live Trading）可视化 / 监控 Dashboard
- 多策略对比报告（当前仅支持单次回测结果）
- Web UI 或独立服务器
- 数据库持久化（仅文件输出）

## Decisions

### 决策 1：采用事件订阅而非侵入式修改

**选择**：新增 `BacktestRecorder` 类，通过 `event_engine.register()` 订阅 `FillEvent` 和 `MarketEvent`，在现有事件流中被动采集数据。

**理由**：现有代码无需修改，符合开闭原则。事件总线架构天然支持多订阅者，风险最低。

**备选方案**：直接在 `AccountService` 或 `BacktestSimulator` 中添加列表记录 → 耦合度高，破坏现有模块职责。

---

### 决策 2：净值计算时机

**选择**：在每个 `MarketEvent`（即每根 Bar）处理时，用当前 Bar 的收盘价 × 持仓量 + 现金 计算瞬时净值，追加到 `equity_curve` 列表。

**理由**：`MarketEvent` 携带完整的 `Bar` 对象（含 OHLCV），时序清晰。无需对 `AccountService` 内部状态进行快照。

**备选方案**：仅在 `FillEvent` 时记录净值 → 净值曲线只有成交点，无法反映持仓期间的浮盈浮亏变化。

---

### 决策 3：图表库选型

**选择**：主输出使用 **Plotly**（交互式 HTML），同时支持 **Matplotlib** 作为静态备选。

**理由**：Plotly 的 `make_subplots` 可将多图合并为单个 HTML 文件，用户可缩放/悬停查看细节，适合策略评估场景。Matplotlib 作为备选，适合 CI/CD 环境或无浏览器场景。

---

### 决策 4：`get_results()` 返回值变更

**选择**：`BacktestRunner.get_results()` 改为返回 `BacktestResult` dataclass，同时保留原有 `print` 输出（可通过 `verbose=False` 关闭）。

**理由**：保持向后兼容（不破坏只依赖 print 输出的用户），同时提供结构化数据供可视化使用。

---

### 决策 5：BacktestResult 数据结构

```python
@dataclass
class TradeRecord:
    timestamp: datetime
    symbol: str
    side: Side          # BUY / SELL
    quantity: int
    price: float
    pnl: float          # 仅 SELL 时有意义，BUY 时为 0.0

@dataclass
class BacktestResult:
    symbol: str
    initial_capital: float
    final_cash: float
    final_equity: float
    trades: List[TradeRecord]       # 所有成交记录
    equity_curve: pd.Series         # index=timestamp, value=equity
    drawdown_curve: pd.Series       # index=timestamp, value=drawdown_pct
    position_curve: pd.Series       # index=timestamp, value=quantity
    bars: List[Bar]                 # 所有历史 Bar，用于绘价格图
    metrics: Dict[str, float]       # sharpe, max_drawdown, total_return, win_rate
```

## Risks / Trade-offs

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| `MarketEvent` 中 `Bar` 数据不完整（缺收盘价）| 净值计算错误 | 在 `BacktestRecorder` 中校验 `bar.close > 0`，否则跳过并警告 |
| Plotly 未安装 | 报告生成失败 | 捕获 `ImportError`，自动回退到 Matplotlib；若两者均缺失则仅输出 CSV |
| 大数据量（10万+ Bar）内存占用 | OOM | `bars` 列表改为可选（`store_bars: bool = True`），默认开启，用户可关闭以节省内存 |
| `get_results()` 返回类型变更破坏调用方 | 兼容性风险 | 保留 `print` 输出；返回 `BacktestResult` 而非 `None`，调用方忽略返回值不受影响 |

## Implementation Plan

### Phase 1：数据采集层

1. 新建 `backtest/recorder.py`，实现 `BacktestRecorder`
   - `__init__(self, event_engine, account_service, symbol)`
   - 注册 `EVENT_MARKET` → `_on_market(event)`
   - 注册 `EVENT_FILL` → `_on_fill(event)`
   - `_on_market`：记录 Bar，计算并追加净值、持仓量
   - `_on_fill`：记录 `TradeRecord`
   - `build_result() -> BacktestResult`：计算回撤序列和 metrics，返回完整结果对象

2. 新建 `backtest/result.py`，定义 `TradeRecord` 和 `BacktestResult` dataclass

3. 修改 `BacktestRunner.__init__`：实例化 `BacktestRecorder` 并注入
4. 修改 `BacktestRunner.get_results()`：调用 `recorder.build_result()` 并返回

### Phase 2：可视化层

5. 新建 `backtest/visualizer.py`，实现 `BacktestVisualizer`
   - `plot(result: BacktestResult, output_path: str, backend: str = 'plotly')`
   - Plotly 路径：4 个子图（价格+标注、净值、回撤、持仓），输出单个 HTML
   - Matplotlib 路径：相同布局，输出 PNG
   - 辅助方法 `_compute_buy_sell_markers(result)` 从 `trades` 提取标注点

### Phase 3：集成与测试

6. 在 `BacktestRunner.get_results()` 中增加可选参数 `save_report: bool = False, report_path: str = 'backtest_report.html'`
7. 新增单元测试：
   - `test_recorder_captures_fills`
   - `test_recorder_equity_curve_length_equals_bar_count`
   - `test_build_result_metrics`
   - `test_visualizer_plotly_output_exists`
   - `test_visualizer_matplotlib_output_exists`

## File Layout

```
tradeSystem/
  backtest/
    __init__.py
    runner.py          # 已有，修改 get_results()
    recorder.py        # 新增
    result.py          # 新增
    visualizer.py      # 新增
  tests/
    test_recorder.py   # 新增
    test_visualizer.py # 新增
```
