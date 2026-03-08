"""
每日指标因子快捷注册扩展。

用法：
    python -m src.trading_system.factors.extensions.tushare_basic_task

执行后将：
1. 注册 basic_close, basic_pe, basic_pb, ... 共 16 个因子定义
2. 从 TuShare daily_basic 接口抓取近一年数据
3. 将因子值存入数据库
"""
from src.trading_system.factors.config import DataSourceConfig
from src.trading_system.factors.quick_register import QuickRegisterConfig
from src.trading_system.factors.settings import DB_PATH, TUSHARE_TOKEN
from src.trading_system.factors.time_resolver import TimeRangeResolver

# ── 配置 ──────────────────────────────────────────────

SYMBOLS = ["000001.SZ"]
TIME_RANGE = {"start": "today-365d", "end": "today"}

DATA_SOURCE_CONFIGS = [
    DataSourceConfig(
        name="tushare_basic",
        source_class="TuShareDataSource",
        params={
            "api": "daily_basic",
            "symbols": SYMBOLS,
            "token": TUSHARE_TOKEN,
        },
        time_range=TIME_RANGE,
    )
]

QUICK_REGISTER_CONFIGS = [
    QuickRegisterConfig(
        data_source="tushare_basic",
        fields=[
            "close", "turnover_rate", "turnover_rate_f", "volume_ratio",
            "pe", "pe_ttm", "pb", "ps", "ps_ttm",
            "dv_ratio", "dv_ttm",
            "total_share", "float_share", "free_share",
            "total_mv", "circ_mv",
        ],
        prefix="basic_",
        category="TuShareBasic",
        description_template="每日指标因子：{field}",
    )
]

# ── 主动执行入口 ──────────────────────────────────────

def run(db_path: str = DB_PATH):
    """注册因子并抓取数据存入数据库。"""
    from src.trading_system.factors.service import FactorService

    service = FactorService(db=db_path)

    # 1. 注册因子定义 + 绑定 ColumnExtractLogic
    config = QUICK_REGISTER_CONFIGS[0]
    factor_names = service.quick_register(config)
    print(f"已注册 {len(factor_names)} 个因子: {factor_names}")

    # 2. 解析时间范围
    start_time = TimeRangeResolver.resolve(TIME_RANGE["start"])
    end_time = TimeRangeResolver.resolve(TIME_RANGE["end"])
    print(f"时间范围: {start_time.date()} ~ {end_time.date()}")

    # 3. 抓取数据并存储因子值
    ds_name = DATA_SOURCE_CONFIGS[0].name
    for symbol in SYMBOLS:
        for factor_name in factor_names:
            try:
                service.compute_and_store(symbol, factor_name, ds_name, start_time, end_time)
            except Exception as e:
                print(f"  [ERROR] {symbol}/{factor_name}: {e}")
                continue
        sample = service.get_factor_values(symbol, factor_names[0], limit=3)
        print(f"  {symbol}: 已存储, 示例 {factor_names[0]} -> {[(v.timestamp, v.value) for v in sample[:3]]}")

    print("完成")


if __name__ == "__main__":
    run()
