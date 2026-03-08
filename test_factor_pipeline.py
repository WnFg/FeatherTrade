#!/usr/bin/env python
"""
测试因子管理和调度系统的完整流程。

测试场景：
1. 用户在 extensions/ 目录定义因子计算逻辑和配置
2. FactorService 自动发现并注册
3. TaskScheduler 加载调度任务
4. 手动触发任务执行
5. 验证因子值存储到数据库
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

from src.trading_system.factors.service import FactorService
from src.trading_system.factors.scheduler import TaskScheduler

def test_config_driven_pipeline():
    """测试配置驱动的因子计算流程"""

    # 1. 创建临时数据库和扩展目录
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_factors.db")
    extensions_dir = os.path.join(temp_dir, "extensions")
    os.makedirs(extensions_dir)

    # 2. 创建测试扩展文件
    extension_code = '''
from datetime import datetime
import pandas as pd
from src.trading_system.factors.base import BaseDataSource, BaseFactorLogic
from src.trading_system.factors.config import FactorConfig, DataSourceConfig, ScheduleConfig

class MockDataSource(BaseDataSource):
    """模拟数据源，返回固定数据"""
    def configure(self, params):
        self.multiplier = params.get('multiplier', 1.0)

    def fetch_data(self, symbol, start_time, end_time):
        # 返回模拟数据
        dates = pd.date_range(start_time, end_time, freq='D')
        return pd.DataFrame({
            'timestamp': dates,
            'symbol': [symbol] * len(dates),
            'price': [100.0 * self.multiplier] * len(dates)
        })

class TestFactor(BaseFactorLogic):
    """测试因子，计算平均价格"""
    def compute(self, data, config):
        if data.empty or 'price' not in data.columns:
            return pd.DataFrame()

        result = pd.DataFrame({
            'timestamp': [data['timestamp'].iloc[-1]],
            'symbol': [data['symbol'].iloc[0]],
            'value': [data['price'].mean()]
        })
        return result

# 因子元数据配置
FACTOR_CONFIGS = [
    FactorConfig(
        name="testfactor",  # 必须与类名小写一致
        category="Test",
        display_name="测试因子",
        description="用于测试的简单因子"
    )
]

# 数据源配置
DATA_SOURCE_CONFIGS = [
    DataSourceConfig(
        name="mock_source",
        source_class="MockDataSource",
        params={
            "multiplier": 2.0,
            "symbols": ["TEST001", "TEST002"]
        },
        time_range={
            "start": "today-3d",
            "end": "today"
        }
    )
]

# 调度任务配置（手动触发，不使用定时）
SCHEDULE_CONFIGS = [
    ScheduleConfig(
        name="test_job",
        factor="testfactor",
        data_source="mock_source",
        trigger={"type": "cron", "expr": "0 0 * * *"},  # 每天午夜（不会自动执行）
        is_active=False  # 设为 False，仅手动触发
    )
]
'''

    extension_file = Path(extensions_dir) / "test_extension.py"
    extension_file.write_text(extension_code)

    print(f"✓ 创建测试扩展文件: {extension_file}")

    # 3. 初始化 FactorService（自动发现扩展）
    service = FactorService(db=db_path, extensions_dir=extensions_dir)
    print(f"✓ 初始化 FactorService，数据库: {db_path}")

    # 4. 验证因子定义已注册
    factor_def = service.db.get_factor_definition("testfactor")
    if factor_def:
        print(f"✓ 因子已注册: {factor_def.name} ({factor_def.display_name})")
    else:
        print("✗ 因子注册失败")
        return False

    # 5. 验证数据源配置已注册
    ds_config = service.registry.get_data_source_config("mock_source")
    if ds_config:
        print(f"✓ 数据源配置已注册: {ds_config.name}, symbols={ds_config.params.get('symbols')}")
    else:
        print("✗ 数据源配置注册失败")
        return False

    # 6. 验证调度配置已注册
    schedule_config = service.registry.get_schedule_config("test_job")
    if schedule_config:
        print(f"✓ 调度配置已注册: {schedule_config.name}, factor={schedule_config.factor}")
    else:
        print("✗ 调度配置注册失败")
        return False

    # 7. 手动执行因子计算（模拟调度器触发）
    print("\n开始执行因子计算...")
    symbols = ds_config.params.get('symbols', [])

    from src.trading_system.factors.time_resolver import TimeRangeResolver
    start_time = TimeRangeResolver.resolve(ds_config.time_range['start'])
    end_time = TimeRangeResolver.resolve(ds_config.time_range['end'])

    print(f"  时间范围: {start_time.date()} ~ {end_time.date()}")

    for symbol in symbols:
        try:
            service.compute_and_store(
                symbol=symbol,
                factor_name="testfactor",
                source_name_or_id="mock_source",
                start_time=start_time,
                end_time=end_time
            )
            print(f"  ✓ {symbol} 计算完成")
        except Exception as e:
            print(f"  ✗ {symbol} 计算失败: {e}")
            return False

    # 8. 验证因子值已存储
    print("\n验证因子值存储...")
    for symbol in symbols:
        values = service.get_factor_values(symbol, "testfactor", limit=10)
        if values:
            print(f"  ✓ {symbol}: 存储了 {len(values)} 条记录")
            print(f"    最新值: {values[0].value} @ {values[0].timestamp}")
        else:
            print(f"  ✗ {symbol}: 未找到因子值")
            return False

    # 9. 清理
    import shutil
    shutil.rmtree(temp_dir)
    print(f"\n✓ 测试完成，清理临时目录: {temp_dir}")

    return True

if __name__ == "__main__":
    print("=" * 60)
    print("因子管理和调度系统集成测试")
    print("=" * 60)
    print()

    success = test_config_driven_pipeline()

    print()
    print("=" * 60)
    if success:
        print("✓ 所有测试通过")
    else:
        print("✗ 测试失败")
    print("=" * 60)
