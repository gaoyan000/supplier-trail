import pytest

from supplier_trail_etl.config import load_settings
from supplier_trail_etl.db import MIGRATIONS_DIR, connect, migrate


@pytest.fixture
def conn():
    """A clean, migrated test database per test."""
    with connect(load_settings().test_database_url) as c:
        with c.cursor() as cur:
            cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        c.commit()
        migrate(c, MIGRATIONS_DIR)
        yield c
        c.rollback()
