"""
Example extension demonstrating config-driven factor registration.

This file shows how to register value factors (PE, PB) with TuShare data source
and daily scheduled tasks - all through declarative configuration.
"""

from src.trading_system.factors.base import BaseFactorLogic
from src.trading_system.factors.config import FactorConfig, DataSourceConfig, ScheduleConfig


# Define factor computation logic (required - users must write code for this)
class PERatioFactor(BaseFactorLogic):
    """PE Ratio factor - extracts PE value from TuShare daily_basic data."""
    def compute(self, data):
        if 'pe' not in data.columns or data.empty:
            return None
        return data['pe'].iloc[-1]  # Return latest PE value


class PBRatioFactor(BaseFactorLogic):
    """PB Ratio factor - extracts PB value from TuShare daily_basic data."""
    def compute(self, data):
        if 'pb' not in data.columns or data.empty:
            return None
        return data['pb'].iloc[-1]  # Return latest PB value


# Define factor metadata (config-driven)
FACTOR_CONFIGS = [
    FactorConfig(
        name="peratioFactor",  # Must match class name in lowercase
        category="Value",
        display_name="PE Ratio",
        description="Price-to-Earnings ratio from TuShare daily_basic",
        formula_config={"field": "pe"}
    ),
    FactorConfig(
        name="pbratiofactor",  # Must match class name in lowercase
        category="Value",
        display_name="PB Ratio",
        description="Price-to-Book ratio from TuShare daily_basic",
        formula_config={"field": "pb"}
    ),
]

# Define TuShare data source for daily_basic API
DATA_SOURCE_CONFIGS = [
    DataSourceConfig(
        name="tushare_daily_basic",
        source_class="TuShareDataSource",
        params={
            "api": "daily_basic",
            "symbols": ["000001.SZ", "600000.SH"],  # Ping An Bank, Pudong Development Bank
            "fields": ["ts_code", "trade_date", "pe", "pb", "turnover_rate"]
        },
        time_range={
            "start": "today-3d",
            "end": "today"
        },
        transformation={
            "rename": {
                "ts_code": "symbol",
                "trade_date": "timestamp"
            }
        }
    ),
]

# Define daily scheduled task (weekdays at 18:00)
SCHEDULE_CONFIGS = [
    ScheduleConfig(
        name="daily_pe_job",
        factor="peratioFactor",  # Must match FactorConfig name
        data_source="tushare_daily_basic",
        trigger={
            "type": "cron",
            "expr": "0 18 * * 1-5"  # 18:00 on weekdays
        },
        is_active=True
    ),
    ScheduleConfig(
        name="daily_pb_job",
        factor="pbratiofactor",  # Must match FactorConfig name
        data_source="tushare_daily_basic",
        trigger={
            "type": "cron",
            "expr": "5 18 * * 1-5"  # 18:05 on weekdays (stagger by 5 min)
        },
        is_active=True
    ),
]
