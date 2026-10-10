"""Settings from etl/.env. Secrets are read here and never logged."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ETL_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ETL_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    database_url: str
    test_database_url: str
    fda_user: str
    dashboard_key: str
    ires_key: str
    pcb_key: str
    raw_dir: Path
    request_interval_s: float = 0.5  # ≤ 2 requests/second to FDA (design §2)


def load_settings() -> Settings:
    raw_dir = Path(os.environ.get("RAW_DIR", "../data/raw"))
    return Settings(
        database_url=os.environ.get("DATABASE_URL", "postgresql:///suppliertrail_dev"),
        test_database_url=os.environ.get("TEST_DATABASE_URL", "postgresql:///suppliertrail_test"),
        fda_user=os.environ.get("FDA_DASHBOARD_USER", ""),
        dashboard_key=os.environ.get("FDA_DASHBOARD_KEY", ""),
        ires_key=os.environ.get("ENFORCEMENT_REPORTS_KEY", ""),
        pcb_key=os.environ.get("PCB_API_KEY", ""),
        raw_dir=raw_dir if raw_dir.is_absolute() else (ETL_ROOT / raw_dir).resolve(),
    )


def require(value: str, name: str) -> str:
    if not value:
        raise RuntimeError(f"{name} is not set in etl/.env")
    return value
