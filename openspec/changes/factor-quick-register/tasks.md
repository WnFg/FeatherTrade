## 1. 新增核心模块 quick_register.py

- [x] 1.1 创建 `src/trading_system/factors/quick_register.py`，定义 `QuickRegisterConfig` dataclass（字段：`data_source`, `fields`, `prefix`, `description_template`, `category`）
- [x] 1.2 在同文件实现 `ColumnExtractLogic(BaseFactorLogic)`，`formula_config` 读取 `column` 键，处理 `ts_code`/`symbol` → `symbol`，`trade_date`/`timestamp` → `datetime`，返回 `[timestamp, symbol, value]`
- [x] 1.3 `ColumnExtractLogic.compute` 处理缺失列：目标列不存在时返回空 DataFrame 并记录错误日志
- [x] 1.4 `ColumnExtractLogic.compute` 处理 YYYYMMDD 字符串日期转换为 `datetime` 对象

## 2. 扩展 DiscoveryEngine 支持 QUICK_REGISTER_CONFIGS

- [x] 2.1 在 `DiscoveryEngine.discover_configs` 中增加对模块属性 `QUICK_REGISTER_CONFIGS` 的检测，收集到返回 dict 的 `'quick_register_configs'` 键
- [x] 2.2 在 `FactorRegistry.__init__` 中增加 `_quick_register_configs: List[QuickRegisterConfig] = []` 存储
- [x] 2.3 在 `FactorRegistry.discover_all` 中调用 `_register_quick_register_configs`，将发现的 configs 存入 `_quick_register_configs`
- [x] 2.4 在 `FactorRegistry` 新增 `get_quick_register_configs() -> List[QuickRegisterConfig]` 方法

## 3. FactorService 新增 quick_register 方法

- [x] 3.1 在 `FactorService` 新增 `quick_register(config: QuickRegisterConfig, sample_symbol: str = None, sample_date: datetime = None) -> List[str]` 方法签名
- [x] 3.2 实现字段解析逻辑：若 `config.fields` 已指定直接使用；否则通过采样调用数据源 `fetch_data` 并过滤标识符列和非数值列
- [x] 3.3 当 `fields=None` 且未提供 `sample_symbol`/`sample_date` 时抛出 `ValueError`
- [x] 3.4 实现因子定义注册循环：为每个字段构造 `FactorDefinition`（`formula_config={"column": field, "quick_register": True}`），调用 `registry.register_factor`（跳过已存在的）
- [x] 3.5 为每个字段实例化 `ColumnExtractLogic` 并注册到 `self._logic_instances[factor_name]`
- [x] 3.6 方法返回所有注册的因子名称列表

## 4. FactorService.__init__ 自动执行发现的 QuickRegisterConfigs

- [x] 4.1 在 `FactorService.__init__` 现有发现流程末尾，遍历 `registry.get_quick_register_configs()`
- [x] 4.2 对每个 config 调用 `self.quick_register(config)`，catch 所有异常并 log，不阻塞初始化

## 5. 单元测试

- [x] 5.1 创建 `tests/unit/test_quick_register.py`，测试 `ColumnExtractLogic.compute` 正常提取列值
- [x] 5.2 测试 `ColumnExtractLogic.compute` 缺失列时返回空 DataFrame
- [x] 5.3 测试 YYYYMMDD 日期字符串正确解析为 `datetime`
- [x] 5.4 测试 `QuickRegisterConfig` 字段默认值（`category` 默认 `"QuickRegister"`，`prefix` 默认空）

## 6. 集成测试

- [x] 6.1 创建 `tests/integration/test_quick_register_pipeline.py`，使用 Mock 数据源测试 `service.quick_register` 完整流程：注册因子定义、绑定逻辑、可查询
- [x] 6.2 测试幂等性：调用两次 `quick_register` 相同 config，不创建重复因子定义
- [x] 6.3 测试 `QUICK_REGISTER_CONFIGS` 自动发现：extension 文件中定义变量，`FactorService` 初始化后因子自动注册
- [x] 6.4 测试 `prefix` 参数：注册的因子名称包含前缀
- [x] 6.5 测试引用不存在数据源时 log error 但不抛异常
