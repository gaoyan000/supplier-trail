import json
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from supplier_trail_etl.db import (
    MIGRATIONS_DIR,
    insert_event,
    migrate,
    refresh_firm_aggregates,
    upsert_firm,
)
from supplier_trail_etl.transform import compliance_to_event, refusal_to_event

pytestmark = pytest.mark.integration
FIXTURES = Path(__file__).parent / "fixtures"
TODAY = date(2026, 10, 9)


def refusals():
    return json.loads((FIXTURES / "refusals.json").read_text())


def scalar(conn, sql, *args):
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchone()[0]


def test_migrate_is_idempotent(conn):
    assert migrate(conn, MIGRATIONS_DIR) == []  # already applied by the fixture


def test_upsert_firm_same_identity_same_id_and_latest_name(conn):
    ev = refusal_to_event(refusals()[0], today=TODAY)
    first = upsert_firm(conn, ev.firm, seen_on=TODAY)
    renamed = replace(ev.firm, name="Oak KK Corporation")
    assert upsert_firm(conn, renamed, seen_on=TODAY) == first
    assert scalar(conn, "select canonical_name from firms where id=%s", first) == "Oak KK Corporation"


def test_insert_event_dedupes_by_hash(conn):
    ev = refusal_to_event(refusals()[0], today=TODAY)
    firm_id = upsert_firm(conn, ev.firm, seen_on=TODAY)
    assert insert_event(conn, firm_id, ev) is True
    assert insert_event(conn, firm_id, ev) is False
    assert scalar(conn, "select count(*) from events") == 1


def test_quarantined_event_is_stored_flagged(conn):
    raw = json.loads((FIXTURES / "compliance_actions.json").read_text())[0]
    ev = compliance_to_event(raw, today=TODAY)
    insert_event(conn, upsert_firm(conn, ev.firm, seen_on=TODAY), ev)
    assert scalar(conn, "select quarantine_reason from events") == "future_date"


def test_aggregates_indexable_needs_two_signals_and_ignore_quarantine(conn):
    raw = refusals()[0]
    one = refusal_to_event(raw, today=TODAY)
    firm_id = upsert_firm(conn, one.firm, seen_on=TODAY)
    insert_event(conn, firm_id, one)
    refresh_firm_aggregates(conn, today=TODAY)
    assert scalar(conn, "select indexable from firms where id=%s", firm_id) is False
    assert scalar(conn, "select risk_status from firms where id=%s", firm_id) == "recent_refusals"

    bad = refusal_to_event({**raw, "ShipmentID": "x/1", "RefusalDate": "2099-01-01"}, today=TODAY)
    insert_event(conn, firm_id, bad)
    refresh_firm_aggregates(conn, today=TODAY)
    assert scalar(conn, "select indexable from firms where id=%s", firm_id) is False

    second = refusal_to_event({**raw, "ShipmentID": "x/2", "RefusalDate": "2025-01-01"}, today=TODAY)
    insert_event(conn, firm_id, second)
    refresh_firm_aggregates(conn, today=TODAY)
    assert scalar(conn, "select indexable from firms where id=%s", firm_id) is True
    assert scalar(conn, "select last_event_at from firms where id=%s", firm_id) == date(2026, 9, 30)


def test_old_refusals_only_is_clear(conn):
    ev = refusal_to_event({**refusals()[0], "RefusalDate": "2015-01-01"}, today=TODAY)
    firm_id = upsert_firm(conn, ev.firm, seen_on=TODAY)
    insert_event(conn, firm_id, ev)
    refresh_firm_aggregates(conn, today=TODAY)
    assert scalar(conn, "select risk_status from firms where id=%s", firm_id) == "clear"
