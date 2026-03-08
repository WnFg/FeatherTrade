## Context

本变更仅新增两个用户扩展文件，利用已实现的 `QuickRegisterConfig` + `TuShareDataSource` 机制，无需修改任何现有代码。

`TuShareDataSource.fetch_data` 已将 `ts_code`→`symbol`、`trade_date`→`timestamp`（datetime）、`vol`→`volume` 完成列重命名。`ColumnExtractLogic` 通过 `symbol`/`timestamp` 列提取值，与此兼容。

时间范围使用 `TimeRangeResolver` 已支持的 `"today-365d"` / `"today"` 表达式。

## Goals / Non-Goals

**Goals:**
- 提供 `tushare_daily_task.py`：为股票 `X` 注册 A股日线行情的 9 个数值因子（prefix `daily_`）
- 提供 `tushare_basic_task.py`：为股票 `Y` 注册每日指标的 16 个数值因子（prefix `basic_`）
- 两个文件均放入 `extensions/` 目录，被 `DiscoveryEngine` 自动发现

**Non-Goals:**
- 不修改 `TuShareDataSource`、`QuickRegisterConfig`、`FactorService` 等任何现有代码
- 不处理调度任务（`ScheduleConfig`）——快捷注册仅在 `FactorService.__init__` 时执行一次
- 不处理多 symbol 批量执行（`quick_register` 当前绑定单 symbol 采样；本任务使用 `fields` 显式指定，无需采样）

## Decisions

### 1. 显式指定 `fields` 而非自动发现

两个扩展均明确列出 `fields`，不依赖采样自动发现。

**理由**：避免在 `FactorService.__init__` 时发起实际 TuShare 网络请求（采样需要 `sample_symbol` + `sample_date`，且会消耗 API 配额）。显式 `fields` 使注册完全离线、幂等。

### 2. 每个文件仅定义 `DATA_SOURCE_CONFIGS` + `QUICK_REGISTER_CONFIGS`，不定义 `BaseDataSource` 子类

`TuShareDataSource` 已在 `builtin/data_sources.py` 中，通过 `source_class="TuShareDataSource"` 引用即可。

### 3. 前缀区分来源

- 日线行情：`prefix="daily_"` → `daily_close`, `daily_vol`, …
- 每日指标：`prefix="basic_"` → `basic_pe`, `basic_pb`, …

避免两个数据源的 `close` 列冲突（`daily_close` vs `basic_close`）。

### 4. 时间范围

`time_range={"start": "today-365d", "end": "today"}`，由 `TimeRangeResolver` 在运行时解析，覆盖近一年数据。

## Risks / Trade-offs

- **TuShare token 未配置** → `TuShareDataSource.configure()` 抛出 `ValueError`。缓解：`FactorService.__init__` 的自动 `quick_register` 已 catch 异常并 log，不阻塞启动。
- **daily_basic 的 `close` 与 daily 的 `close` 同名** → 已通过 prefix 区分（`daily_close` vs `basic_close`），无冲突。
