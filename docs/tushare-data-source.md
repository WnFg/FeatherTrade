# TuShare Data Source

TuShare is a financial data platform focused on A-share market data. FeatherTrade includes a built-in `TuShareDataSource` that wraps the TuShare Pro API.

## Setup

```bash
pip install tushare
export TUSHARE_TOKEN=your_token_here
```

Or configure via `workspace/config/factors.yaml`:
```yaml
tushare_token: your_token_here
```

---

## API: Daily Bars (`daily`)

Returns OHLCV daily bar data for A-share stocks.

### Input Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `ts_code` | str | N | Stock code (supports multiple, comma-separated) |
| `trade_date` | str | N | Trade date (YYYYMMDD) |
| `start_date` | str | N | Start date (YYYYMMDD) |
| `end_date` | str | N | End date (YYYYMMDD) |

### Output Fields

| Name | Type | Description |
|---|---|---|
| `ts_code` | str | Stock code |
| `trade_date` | str | Trade date |
| `open` | float | Open price |
| `high` | float | High price |
| `low` | float | Low price |
| `close` | float | Close price |
| `pre_close` | float | Previous close (ex-rights) |
| `change` | float | Price change |
| `pct_chg` | float | Percent change (based on ex-rights previous close) |
| `vol` | float | Volume (lots) |
| `amount` | float | Turnover amount (thousand CNY) |

### Sample Data

```
   ts_code  trade_date  open  high   low  close  pre_close  change  pct_chg        vol      amount
0  000001.SZ  20180718  8.75  8.85  8.69   8.70       8.72   -0.02    -0.23  525152.77  460697.38
1  000001.SZ  20180717  8.74  8.75  8.66   8.72       8.73   -0.01    -0.11  375356.33  326396.99
2  000001.SZ  20180716  8.85  8.90  8.69   8.73       8.88   -0.15    -1.69  689845.58  603427.71
```

### Usage in Extension

```python
from src.trading_system.factors.config import DataSourceConfig

DataSourceConfig(
    name="tushare_daily",
    source_class="TuShareDataSource",
    params={
        "api": "daily",
        "symbols": ["000001.SZ"],
        "token": "your_token",  # or set TUSHARE_TOKEN env var
    },
    time_range={"start": "today-365d", "end": "today"},
)
```

---

## API: Daily Basic Indicators (`daily_basic`)

Returns valuation and market indicators for each trading day.

### Input Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `ts_code` | str | Y | Stock code (one of ts_code/trade_date required) |
| `trade_date` | str | N | Trade date (YYYYMMDD) |
| `start_date` | str | N | Start date (YYYYMMDD) |
| `end_date` | str | N | End date (YYYYMMDD) |

### Output Fields

| Name | Type | Description |
|---|---|---|
| `ts_code` | str | Stock code |
| `trade_date` | str | Trade date |
| `close` | float | Close price |
| `turnover_rate` | float | Turnover rate (%) |
| `turnover_rate_f` | float | Turnover rate — free float (%) |
| `volume_ratio` | float | Volume ratio |
| `pe` | float | P/E ratio (total market cap / net profit; blank if loss) |
| `pe_ttm` | float | P/E ratio TTM |
| `pb` | float | P/B ratio (total market cap / net assets) |
| `ps` | float | P/S ratio |
| `ps_ttm` | float | P/S ratio TTM |
| `dv_ratio` | float | Dividend yield (%) |
| `dv_ttm` | float | Dividend yield TTM (%) |
| `total_share` | float | Total shares (10k shares) |
| `float_share` | float | Float shares (10k shares) |
| `free_share` | float | Free float shares (10k) |
| `total_mv` | float | Total market cap (10k CNY) |
| `circ_mv` | float | Circulating market cap (10k CNY) |

### Sample Data

```
     ts_code  trade_date  turnover_rate  volume_ratio       pe      pb
0  600230.SH    20180726         2.4584          0.72   8.6928  3.7203
1  600237.SH    20180726         1.4737          0.88  166.400  1.8868
2  002465.SZ    20180726         0.7489          0.72   71.894  2.6391
```

### Usage in Extension

```python
DataSourceConfig(
    name="tushare_basic",
    source_class="TuShareDataSource",
    params={
        "api": "daily_basic",
        "symbols": ["000001.SZ"],
    },
    time_range={"start": "today-365d", "end": "today"},
)
```

---

## Quick Ingestion

For one-command data pull and factor registration, use the built-in task scripts:

```bash
# Daily bars → daily_open, daily_close, daily_vol, ...
python -m src.trading_system.factors.extensions.tushare_daily_task

# Daily basic → basic_pe, basic_pb, basic_turnover_rate, ...
python -m src.trading_system.factors.extensions.tushare_basic_task
```

Edit `SYMBOLS` at the top of each file to target your stock codes.
