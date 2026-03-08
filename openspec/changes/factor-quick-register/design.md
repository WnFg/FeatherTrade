## Context

因子系统当前通过 `BaseFactorLogic` 子类 + `FactorConfig` + `DiscoveryEngine` 实现因子注册。每个因子需要独立的逻辑类，导致从同一 DataFrame 数据源提取多个列值时产生大量样板代码。

`QuickRegisterConfig` 快捷注册机制作为附加层引入，不改变现有扩展机制，通过内置的 `ColumnExtractLogic` 实现列提取，在 `FactorService` 层完成自动注册。

## Goals / Non-Goals

**Goals:**
- 引入 `QuickRegisterConfig` 数据类，让用户通过声明式配置批量注册 DataFrame 列为因子
- 实现 `ColumnExtractLogic`：内置的 `BaseFactorLogic` 子类，按列名提取单列值
- 在 `FactorService` 新增 `quick_register` 方法，处理列发现、定义注册、逻辑绑定
- 在 `DiscoveryEngine` 支持发现 `QUICK_REGISTER_CONFIGS` 变量，`FactorService.__init__` 自动执行

**Non-Goals:**
- 不修改 `BaseDataSource` / `BaseFactorLogic` 接口
- 不修改 `FactorDatabase` schema（不新增表）
- 不支持非数值列的因子注册
- 不提供 YAML 格式的 `QUICK_REGISTER_CONFIGS`（仅 Python，与现有 `FactorConfig` YAML 支持保持一致的后续扩展）

## Decisions

### 1. 新文件 `quick_register.py` 而非扩展现有文件

`QuickRegisterConfig` 和 `ColumnExtractLogic` 放入独立文件 `src/trading_system/factors/quick_register.py`。

**理由**：`config.py` 已有 `FactorConfig`/`DataSourceConfig`/`ScheduleConfig`，避免混入不同抽象层次的类；`base.py` 只放抽象基类；新文件职责清晰。

**替代方案**：放入 `builtin/factors.py` — 拒绝，因为 `ColumnExtractLogic` 是内部机制而非用户可见的内置因子。

### 2. 列发现通过采样而非 schema introspection

自动检测数值列时，对数据源调用 `fetch_data` 获取小样本（单个 symbol、1天范围），从返回的 DataFrame 推断列类型。

**理由**：`BaseDataSource` 接口无 schema 方法，采样最简单、最通用。

**替代方案**：为 `BaseDataSource` 添加 `get_schema()` 抽象方法 — 拒绝，breaking change，且过度设计。

采样需要 symbol 和时间范围。`FactorService.quick_register` 接受可选的 `sample_symbol: str` 和 `sample_date: datetime` 参数用于列发现；若未提供且 `fields` 也未指定，则抛出 `ValueError`。

### 3. 逻辑绑定存入 `FactorService._logic_instances`（内存），不持久化

`ColumnExtractLogic` 实例注册到 `FactorService._logic_instances[factor_name]`，与现有手动 `register_logic` 路径完全相同。

**理由**：`FactorDefinition.formula_config` 中已存储 `{"column": "close"}`，重启后 `quick_register` 被 `__init__` 再次调用，逻辑实例会重建。无需新增持久化机制。

### 4. 幂等性通过 `formula_config` 中的 `"quick_register": true` 标记

`FactorDefinition.formula_config` 写入 `{"column": "close", "quick_register": true}`，`_register_factor_configs` 中现有的 `existing` 检查已跳过重复插入。`quick_register` 额外跳过已存在定义的逻辑绑定重建（直接覆盖也无害）。

### 5. `DiscoveryEngine` 扩展：新增 `QUICK_REGISTER_CONFIGS` 发现

在 `DiscoveryEngine.discover_configs` 中增加对 `QUICK_REGISTER_CONFIGS` 的检测，与 `FACTOR_CONFIGS` 同等处理，返回 dict 增加 `'quick_register_configs'` 键。

`FactorRegistry` 存储发现的 `QuickRegisterConfig` 列表，暴露 `get_quick_register_configs()` 方法。

`FactorService.__init__` 在现有发现流程后，遍历 `quick_register_configs` 调用 `self.quick_register(config)`。由于此时数据源已就绪，调用顺序无问题。

## Risks / Trade-offs

- **采样调用副作用** → 列发现时会实际调用数据源（可能触发网络请求）。缓解：仅在 `fields=None` 时采样，用户明确指定 `fields` 可完全规避。
- **初始化时自动 quick_register 失败** → 若数据源不可用（如网络离线），`__init__` 期间调用会抛出异常。缓解：在自动发现路径中 catch 异常并 log，不阻塞 `FactorService` 初始化。
- **列名冲突** → 若不同数据源的同名列被注册为同名因子（如两个 `DataSourceConfig` 都有 `close` 列），后注册的 `ColumnExtractLogic` 会覆盖前者。缓解：`prefix` 字段可规避冲突；文档说明用户应使用 prefix 区分来源。
