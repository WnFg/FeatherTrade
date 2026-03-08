## Why

目前，因子系统要求用户为每个因子编写独立的 `BaseFactorLogic` 子类来定义计算逻辑。当用户已有一个返回多列数据的 DataFrame 数据源（如 TuShare 日线行情接口返回 open、high、low、close、vol 等字段），他们必须为每个字段分别编写因子逻辑类、注册因子定义、并将它们关联到调度任务。这个过程重复且繁琐。

快捷注册机制允许用户直接从 DataFrame 数据源的列中批量提取因子，无需编写任何 `BaseFactorLogic` 代码，大幅降低数据驱动型因子的注册成本。

## What Changes

引入 `QuickRegisterConfig` 配置类和对应的注册流程，支持用户基于现有 `DataSourceConfig` 快速批量注册因子。

系统自动分析数据源返回的 DataFrame 列，排除标识符列（ts_code、trade_date、symbol、timestamp 等），将剩余数值列作为独立因子注册并存储。

用户可选配置项：
- `fields`：指定要提取的列名子集（默认提取所有数值列）
- `prefix`：因子名称公共前缀（如 `daily_` → `daily_close`）
- `description`：因子描述模板
- `category`：因子分类

## Capabilities

### New Capabilities

- **因子快捷注册**：通过 `QuickRegisterConfig` 将 DataFrame 数据源的数值列批量注册为因子，自动创建 `FactorDefinition` 并生成内置的列提取逻辑

### Modified Capabilities

- **FactorService**：新增 `quick_register` 方法，接受数据源名称与 `QuickRegisterConfig`，执行自动列发现、因子定义注册、以及 `ColumnExtractLogic` 内置逻辑绑定
- **FactorRegistry / DiscoveryEngine**：支持从 `QuickRegisterConfig` 动态注册因子定义和对应的内置逻辑实例

## Impact

- 新增文件：`src/trading_system/factors/quick_register.py`（`QuickRegisterConfig`、`ColumnExtractLogic`）
- 修改文件：`src/trading_system/factors/service.py`（新增 `quick_register` 方法）
- 修改文件：`src/trading_system/factors/registry.py`（支持运行时动态注册逻辑实例）
- 新增测试：`tests/unit/test_quick_register.py`、`tests/integration/test_quick_register_pipeline.py`
- 无破坏性变更：所有现有扩展机制保持不变，快捷注册是附加能力
