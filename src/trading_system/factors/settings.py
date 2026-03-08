"""
因子模块集中配置。

优先级（从高到低）：
  1. 环境变量（FACTORS_DB_PATH, TUSHARE_TOKEN, FACTORS_LOG_DIR）
  2. workspace/config/factors.yaml
  3. 内置默认值（workspace/data/factors.db）
"""
import os
from pathlib import Path

# ── 项目根目录 ───────────────────────────────────────
# settings.py 位于 src/trading_system/factors/，向上 4 级为项目根
_ROOT = Path(__file__).resolve().parents[3]
_WORKSPACE = _ROOT / "workspace"


def _load_yaml_config() -> dict:
    """尝试加载 workspace/config/factors.yaml，失败时返回空字典。"""
    config_path = _WORKSPACE / "config" / "factors.yaml"
    if not config_path.exists():
        return {}
    try:
        import yaml
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


_yaml = _load_yaml_config()

# ── 数据库 ──────────────────────────────────────────
_default_db = str(_WORKSPACE / "data" / "factors.db")
DB_PATH: str = os.environ.get(
    "FACTORS_DB_PATH",
    _yaml.get("db_path", _default_db),
)
if not os.path.isabs(DB_PATH):
    DB_PATH = str(_ROOT / DB_PATH)

# ── 日志目录 ────────────────────────────────────────
_default_log_dir = str(_WORKSPACE / "logs")
LOG_DIR: str = os.environ.get(
    "FACTORS_LOG_DIR",
    _yaml.get("log_dir", _default_log_dir),
)
if not os.path.isabs(LOG_DIR):
    LOG_DIR = str(_ROOT / LOG_DIR)

# ── TuShare ─────────────────────────────────────────
TUSHARE_TOKEN: str = os.environ.get(
    "TUSHARE_TOKEN",
    _yaml.get("tushare_token", ""),
)
