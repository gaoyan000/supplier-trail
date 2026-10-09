import json
from pathlib import Path

import pytest

from fda_clients import env

SAMPLES = Path(__file__).parent / "samples"
_metrics: dict = {}


@pytest.fixture
def save_sample():
    """Save a small slice of real records for inspection and later parser fixtures."""
    def _save(name: str, records, n: int = 25):
        SAMPLES.mkdir(exist_ok=True)
        (SAMPLES / f"{name}.json").write_text(json.dumps(records[:n], indent=2, ensure_ascii=False))
    return _save


@pytest.fixture
def metric():
    def _record(source: str, **values):
        _metrics.setdefault(source, {}).update(values)
    return _record


def require_key(var: str):
    if not env(var):
        pytest.skip(f"{var} not set in spike/.env")


def pytest_sessionfinish(session, exitstatus):
    if _metrics:
        SAMPLES.mkdir(exist_ok=True)
        (SAMPLES / "metrics.json").write_text(json.dumps(_metrics, indent=2))
        print("\n\n=== DATA ACCESS METRICS ===")
        print(json.dumps(_metrics, indent=2))
