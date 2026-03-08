## 1. 配置数据结构定义

- [x] 1.1 创建 `src/trading_system/factors/config.py`，定义 `FactorConfig` dataclass（name, category, display_name, formula_config, version）
- [x] 1.2 在 `config.py` 中定义 `DataSourceConfig` dataclass（name, source_class, params, time_range, transformation）
- [x] 1.3 在 `config.py` 中定义 `ScheduleConfig` dataclass（name, factor, data_source, trigger）
- [x] 1.4 为三个 dataclass 添加 `to_dict()` 和 `from_dict()` 方法，支持 YAML 序列化

## 2. 时间范围解析器

- [x] 2.1 创建 `src/trading_system/factors/time_resolver.py`，实现 `TimeRangeResolver` 类
- [x] 2.2 实现 `resolve(expr: str) -> datetime` 方法，支持 `today`、`today-Nd`、`today-Nw` 格式
- [x] 2.3 实现 ISO 8601 字符串解析作为 fallback
- [x] 2.4 添加单元测试 `tests/unit/test_time_resolver.py`，覆盖各种时间表达式

## 3. BaseDataSource 接口扩展

- [x] 3.1 在 `src/trading_system/factors/base.py` 的 `BaseDataSource` 中添加 `configure(params: dict)` 方法（默认空实现）
- [x] 3.2 更新 `DataSourceFactory.create_instance()` 在实例化后调用 `configure(params)`
- [x] 3.3 更新 `builtin/data_sources.py` 中的 `TuShareDataSource`，实现 `configure()` 方法接收 `api`、`fields`、`symbols` 参数
- [x] 3.4 确保 `FileDataSource` 和 `APIDataSource` 向后兼容（不实现 `configure()` 也能正常工作）

## 4. DiscoveryEngine 配置扫描增强

- [x] 4.1 扩展 `DiscoveryEngine.discover_components()` 支持扫描模块级变量 `FACTOR_CONFIGS`、`DATA_SOURCE_CONFIGS`、`SCHEDULE_CONFIGS`
- [x] 4.2 实现 `DiscoveryEngine.discover_yaml_configs(directory: str)` 方法，扫描 `.yaml` 文件并解析为 config 对象
- [x] 4.3 在 `FactorRegistry.__init__` 中调用配置扫描，收集所有 config 对象
- [x] 4.4 实现 `FactorRegistry._register_factor_configs()` 方法，将 `FactorConfig` upsert 到 `factor_definitions` 表（幂等）
- [x] 4.5 实现 `FactorRegistry._register_data_source_configs()` 方法，将 `DataSourceConfig` 保存到内存 `_ds_config_map: Dict[str, DataSourceConfig]`
- [x] 4.6 实现 `FactorRegistry._register_schedule_configs()` 方法，将 `ScheduleConfig` 保存到内存 `_schedule_config_map: Dict[str, ScheduleConfig]`

## 5. FactorService 配置驱动增强

- [x] 5.1 修改 `FactorService._get_source()` 方法，优先从 `_ds_config_map` 查找 `DataSourceConfig`，再 fallback 到 DB 和动态注册
- [x] 5.2 实现 `FactorService._instantiate_from_config(config: DataSourceConfig) -> BaseDataSource` 方法
- [x] 5.3 在 `compute_and_store()` 中支持 `source_name_or_id` 参数既可以是 DB ID 也可以是 config name
- [x] 5.4 确保 `ParameterTransformer` 能从 `DataSourceConfig.transformation` 读取转换规则

## 6. TaskScheduler 动态参数解析

- [x] 6.1 修改 `TaskScheduler._execute_task_wrapper()`，从 `ScheduleConfig` 读取关联的 `DataSourceConfig`
- [x] 6.2 从 `DataSourceConfig.params.symbols` 提取 symbol 列表，替换 TODO 占位
- [x] 6.3 从 `DataSourceConfig.time_range` 提取时间范围表达式，使用 `TimeRangeResolver` 解析为具体 datetime
- [x] 6.4 对每个 symbol 调用 `FactorService.compute_and_store()`，传入解析后的时间范围
- [x] 6.5 更新 `TaskScheduler.add_task()` 支持从 `ScheduleConfig` 创建 APScheduler job

## 7. TuShare 数据源完善

- [x] 7.1 在 `builtin/data_sources.py` 中完善 `TuShareDataSource.configure()` 实现，支持 `api` 参数（`daily` / `daily_basic`）
- [x] 7.2 实现 `TuShareDataSource.fetch_data()` 根据 `api` 参数调用不同的 TuShare 接口
- [x] 7.3 添加 `TUSHARE_TOKEN` 环境变量检查，未设置时抛出清晰错误
- [x] 7.4 实现 TuShare 日期格式转换（`YYYYMMDD` → `datetime`）
- [x] 7.5 添加单元测试 `tests/unit/test_tushare_data_source.py`，mock TuShare API 调用

## 8. 示例扩展文件

- [x] 8.1 创建 `src/trading_system/factors/extensions/example_value_factors.py`
- [x] 8.2 在示例文件中定义 `FACTOR_CONFIGS`，包含 `pe_ratio` 和 `pb_ratio` 因子
- [x] 8.3 在示例文件中定义 `DATA_SOURCE_CONFIGS`，配置 TuShare `daily_basic` 数据源，symbols 包含 `000001.SZ`、`600000.SH`，时间范围 `today-3d ~ today`
- [x] 8.4 在示例文件中定义 `SCHEDULE_CONFIGS`，配置每日 18:00 定时任务（cron: `0 18 * * 1-5`）
- [x] 8.5 添加示例 YAML 文件 `extensions/example_value_factors.yaml` 作为等价配置

## 9. 集成测试

- [x] 9.1 创建 `tests/integration/test_config_driven_pipeline.py`
- [x] 9.2 测试场景:从 extension 文件加载 config → 注册因子 → 实例化数据源 → 执行调度任务 → 验证 `factor_values` 表写入
- [x] 9.3 测试场景：相对时间范围解析（`today-3d`）在不同日期执行时正确求值
- [x] 9.4 测试场景：多 symbol 列表展开，每个 symbol 独立调用 `compute_and_store`
- [x] 9.5 测试场景：YAML 配置文件与 Python 配置文件等价性

## 10. 现有测试适配

- [x] 10.1 更新 `tests/unit/test_factor_system.py`，适配 `BaseDataSource.configure()` 新接口
- [x] 10.2 更新 `tests/integration/test_factor_extensions.py`，验证 config 扫描机制
- [x] 10.3 更新 `tests/integration/test_factor_scheduling.py`，验证 `ScheduleConfig` 驱动的任务执行

## 11. 文档与示例

- [x] 11.1 更新 `docs/factor_model.md`，添加配置驱动注册章节
- [x] 11.2 创建 `docs/factor_config_guide.md`，详细说明 `FactorConfig`、`DataSourceConfig`、`ScheduleConfig` 用法
- [x] 11.3 在 `docs/factor_config_guide.md` 中添加完整的 TuShare PE/PB 定时抓取示例
- [x] 11.4 更新 `CLAUDE.md`，补充 factor 模块的配置驱动扩展机制说明

## 12. 调度器与服务配合（补充任务）

- [x] 12.1 修复 `TaskScheduler.add_task_from_config()` 的 trigger 配置提取逻辑，正确处理 interval 和 one-off 类型
- [x] 12.2 改进 `TaskScheduler._execute_config_task_wrapper()` 添加详细执行日志（成功/失败计数、错误消息、执行时长）
- [x] 12.3 修复 `TaskScheduler._execute_task_wrapper()` (DB 驱动) 的时间范围解析和多 symbol 支持
- [x] 12.4 添加 `FactorDatabase.get_factor_definition_by_id()` 方法
- [x] 12.5 添加 `FactorDatabase.get_factor_definition_dict()` 辅助方法
- [x] 12.6 添加 `FactorDatabase.close()` 方法（用于测试清理）
- [x] 12.7 修复 `FactorService.__init__()` 初始化顺序，支持 db 参数接收字符串路径或 FactorDatabase 实例
- [x] 12.8 改进 `FactorService._instantiate_from_config()` 优先从 registry 查找类，支持扩展中的简单类名
- [x] 12.9 改进 `DataSourceFactory.create_instance()` 错误处理，明确要求 class_path 包含模块路径
- [x] 12.10 创建 `test_factor_pipeline.py` 集成测试脚本，验证完整流程
- [x] 12.11 更新 `example_value_factors.py` 补充 `PERatioFactor` 和 `PBRatioFactor` 计算逻辑类
- [x] 12.12 更新文档明确说明因子计算逻辑必须用代码定义，配置只能表达元数据
