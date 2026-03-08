## Context

已有 `tushare_daily_task.py` 和 `tushare_basic_task.py` 两个扩展文件，分别针对 `000001.SZ` 硬编码了 SYMBOLS。用户需要针对自定义股票代码（X 和 Y）创建同类任务文件，文件结构与现有文件保持一致，仅修改 `SYMBOLS` 和 `DataSourceConfig.name`（避免与现有配置冲突）。

## Goals / Non-Goals

**Goals:**
- 创建 `tushare_daily_task_X.py`：针对用户指定的 ts_code（代号 X），快捷注册日线行情因子并拉取近一年数据
- 创建 `tushare_basic_task_Y.py`：针对用户指定的 ts_code（代号 Y），快捷注册每日指标因子并拉取近一年数据
- 文件顶部 `SYMBOLS` 变量清晰标注，用户只需修改该变量即可复用

**Non-Goals:**
- 不修改框架核心代码
- 不处理多 symbol 批量并发（顺序执行即可）
- 不创建调度任务（用户手动执行 `__main__`）

## Decisions

**决策 1：DataSourceConfig.name 加 symbol 后缀**
- 选择：`tushare_daily_X` / `tushare_basic_Y`（而非通用的 `tushare_daily` / `tushare_basic`）
- 原因：避免与现有 `tushare_daily_task.py` 中已注册的 `tushare_daily` 数据源配置冲突；每个 symbol 的数据源独立，便于按需管理

**决策 2：复用现有 `quick_register` + `compute_and_store` 流程**
- 不引入新 API，与现有任务文件保持完全一致的执行模式
- 降低用户理解成本，复制文件即可上手

**决策 3：文件命名使用 `_X` / `_Y` 后缀**
- `tushare_daily_task_X.py` 和 `tushare_basic_task_Y.py`
- X / Y 为占位符，用户替换 `SYMBOLS` 后无需重命名文件

## Risks / Trade-offs

- [风险] 用户忘记修改 `SYMBOLS` 导致数据写入错误的 symbol → 缓解：文件顶部添加醒目注释说明必填项
- [风险] `tushare_daily_X` 数据源名与未来其他任务冲突 → 缓解：建议用户按实际 symbol 重命名，如 `tushare_daily_600519SH`
- [取舍] 不自动适配多 symbol：保持简单，用户有多个 symbol 时复制文件即可
