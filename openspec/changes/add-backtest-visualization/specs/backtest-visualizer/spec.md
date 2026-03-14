## ADDED Requirements

### Requirement: 生成价格走势图并标注买卖点
`BacktestVisualizer` SHALL 根据 `BacktestResult.bars` 绘制价格折线图，并将 `BacktestResult.trades` 中的 BUY 成交以向上箭头标注、SELL 成交以向下箭头标注，标注点位于成交价格处。

#### Scenario: BUY 点显示向上标注
- **WHEN** `BacktestResult.trades` 中存在 side 为 BUY 的成交记录
- **THEN** 可视化报告的价格图上，对应时间戳处显示向上箭头或绿色标记，悬停/注释显示成交价格

#### Scenario: SELL 点显示向下标注
- **WHEN** `BacktestResult.trades` 中存在 side 为 SELL 的成交记录
- **THEN** 可视化报告的价格图上，对应时间戳处显示向下箭头或红色标记，悬停/注释显示成交价格

#### Scenario: 无成交时价格图正常渲染
- **WHEN** `BacktestResult.trades` 为空列表
- **THEN** 价格走势图正常绘制，无买卖标注

---

### Requirement: 生成资金净值曲线与回撤曲线
`BacktestVisualizer` SHALL 根据 `BacktestResult.equity_curve` 绘制净值折线图，根据 `BacktestResult.drawdown_curve` 绘制回撤面积图，两图共享时间轴。

#### Scenario: 净值曲线反映逐 Bar 变化
- **WHEN** 调用 `plot()` 生成报告
- **THEN** 净值子图中每根 Bar 对应一个数据点，Y 轴单位为金额（元）

#### Scenario: 回撤曲线显示最大回撤区间
- **WHEN** 调用 `plot()` 生成报告
- **THEN** 回撤子图中最大回撤区间以面积图高亮显示，Y 轴为回撤百分比（负值）

---

### Requirement: 生成持仓量时序图
`BacktestVisualizer` SHALL 根据 `BacktestResult.position_curve` 绘制持仓量随时间变化的阶梯图（step chart）。

#### Scenario: 持仓量在成交后阶跃变化
- **WHEN** 存在 BUY 成交后持仓量增加
- **THEN** 持仓量子图在对应时间戳处显示阶跃上升

---

### Requirement: 输出交互式 HTML 报告
`BacktestVisualizer` SHALL 支持使用 Plotly 将四个子图（价格+标注、净值、回撤、持仓量）合并输出为单个自包含 HTML 文件，用户可在浏览器中缩放、平移和悬停查看数据。

#### Scenario: HTML 文件生成成功
- **WHEN** 调用 `plot(result, output_path='report.html', backend='plotly')`
- **THEN** 在 `output_path` 路径生成有效的 HTML 文件，文件大小大于 0

#### Scenario: Plotly 未安装时自动回退
- **WHEN** 调用 `plot()` 时 Plotly 未安装，`backend` 为 `'plotly'`
- **THEN** 系统打印警告信息并自动切换到 Matplotlib 后端生成 PNG 文件

---

### Requirement: 输出静态 PNG 报告
`BacktestVisualizer` SHALL 支持使用 Matplotlib 将四个子图输出为单张 PNG 图片文件。

#### Scenario: PNG 文件生成成功
- **WHEN** 调用 `plot(result, output_path='report.png', backend='matplotlib')`
- **THEN** 在 `output_path` 路径生成有效的 PNG 文件，文件大小大于 0
