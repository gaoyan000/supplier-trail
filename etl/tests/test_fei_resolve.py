from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from supplier_trail_etl.db import refresh_firm_aggregates, upsert_firm
from supplier_trail_etl.fda.fei_api import FdaBlockedError, FeiMatch, FeiResult
from supplier_trail_etl.fda.import_alerts import AlertIndexRow, parse_red_list
from supplier_trail_etl.fei_resolve import AgreementTooLowError, agreement, apply_lookups, lookup_entries
from supplier_trail_etl.redlist import apply_red_list_snapshot, upsert_alert
from supplier_trail_etl.resolve import resolve_red_list
from supplier_trail_etl.transform import FirmRecord

pytestmark = pytest.mark.integration
FIXTURE = (Path(__file__).parent / "fixtures" / "red_list_99_19_canada.html").read_text()
TODAY = date(2026, 10, 16)


def rows(conn, sql, *args):
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchall()


def match(fei, name, city="Winkler"):
    return FeiResult("found", FeiMatch(fei=fei, legal_name=name, address="1 Sample St", city=city,
                                       country_code="CA", merged=False), {"STATUSCODE": 400})


class FakeClient:
    """Answers by firm name; raises FdaBlockedError for names in `block`."""

    def __init__(self, answers, block=()):
        self.answers, self.block, self.calls = answers, set(block), []

    def find(self, payload):
        self.calls.append(payload["firmname"])
        if payload["firmname"] in self.block:
            raise FdaBlockedError("block page")
        return self.answers.get(payload["firmname"], FeiResult("not_found", None, {"STATUSCODE": 412}))


@pytest.fixture
def entries(conn):
    upsert_alert(conn, AlertIndexRow("99-19", "DWPE", date(2026, 10, 6), "Salmonella", "importalert_263.html"))
    apply_red_list_snapshot(conn, "99-19", parse_red_list(FIXTURE, alert_number="99-19"), today=TODAY)
    upsert_firm(conn, FirmRecord(fei="9999999999", name="Some US Firm", country_code="US", country="United States"),
                seen_on=TODAY)  # teaches the country index that "Canada" is CA
    upsert_firm(conn, FirmRecord(fei="1111111111", name="Other Canada Firm", country_code="CA", country="Canada"),
                seen_on=TODAY)
    conn.commit()
    return {name: eid for eid, name in rows(conn, "select id, fda_name from red_list_entries")}


def test_lookups_are_stored_once_and_never_repeated(conn, entries):
    client = FakeClient({"DELMAR COMMODITIES LTD": match("3000000001", "DELMAR COMMODITIES LTD")})
    stats = lookup_entries(conn, client, limit=10)
    assert stats["looked_up"] == 6 and stats["found"] == 1 and stats["not_found"] == 5
    assert rows(conn, "select status, fei from fei_api_lookups where entry_id=%s", entries["DELMAR COMMODITIES LTD"]) == [
        ("found", "3000000001")]
    assert lookup_entries(conn, client, limit=10)["looked_up"] == 0
    assert len(client.calls) == 6


def test_limit_and_food_alerts_only(conn, entries):
    upsert_alert(conn, AlertIndexRow("66-40", "DWPE", None, "Drugs", "importalert_190.html"))
    drug = parse_red_list(FIXTURE, alert_number="66-40")[:1]
    apply_red_list_snapshot(conn, "66-40", [replace(drug[0], entry_key="drug-1")], today=TODAY)
    client = FakeClient({})
    assert lookup_entries(conn, client, limit=2)["looked_up"] == 2
    lookup_entries(conn, client, limit=100)
    assert len(client.calls) == 6  # the drug alert entry is never sent


def test_a_block_stops_the_run_and_keeps_earlier_results(conn, entries):
    client = FakeClient({}, block={"Bio-Essential Botanicals"})
    with pytest.raises(FdaBlockedError):
        lookup_entries(conn, client, limit=10)
    stored = rows(conn, "select count(*) from fei_api_lookups")[0][0]
    assert stored == len(client.calls) - 1
    assert "Bio-Essential Botanicals" not in {n for (n,) in rows(
        conn, "select e.fda_name from fei_api_lookups l join red_list_entries e on e.id = l.entry_id")}


def test_apply_creates_new_firm_and_publishes_a_verified_link(conn, entries):
    lookup_entries(conn, FakeClient({"DELMAR COMMODITIES LTD": match("3000000001", "DELMAR COMMODITIES LTD")}), limit=10)
    assert apply_lookups(conn, today=TODAY) == {"applied": 1, "new_firms": 1}
    refresh_firm_aggregates(conn, today=TODAY)

    firm_id, name, city, country, status, indexable = rows(
        conn, "select id, canonical_name, city, country, risk_status, indexable from firms where fei='3000000001'")[0]
    assert (name, city, country, status, indexable) == ("DELMAR COMMODITIES LTD", "Winkler", "Canada", "on_red_list", True)
    entry = entries["DELMAR COMMODITIES LTD"]
    assert rows(conn, "select firm_id from red_list_entries where id=%s", entry)[0][0] == firm_id
    assert rows(conn, "select match_method, link_status, verified_by from red_list_candidates where entry_id=%s",
                entry) == [("fei_api", "verified", "fei_api")]
    assert rows(conn, "select count(*) from events where firm_id=%s and type='alert_listed'", firm_id)[0][0] == 1
    assert apply_lookups(conn, today=TODAY) == {"applied": 0, "new_firms": 0}


def test_apply_links_an_existing_firm_without_renaming_it(conn, entries):
    lookup_entries(conn, FakeClient({"AgroCrop Exports, Ltd": match("1111111111", "AGROCROP EXPORTS LTD")}), limit=10)
    assert apply_lookups(conn, today=TODAY) == {"applied": 1, "new_firms": 0}
    assert rows(conn, "select canonical_name from firms where fei='1111111111'") == [("Other Canada Firm",)]


def test_not_found_and_ambiguous_are_never_linked(conn, entries):
    ambiguous = FeiResult("ambiguous", None, {"STATUSCODE": 400})
    lookup_entries(conn, FakeClient({"DELMAR COMMODITIES LTD": ambiguous}), limit=10)
    assert apply_lookups(conn, today=TODAY)["applied"] == 0
    assert rows(conn, "select count(*) from red_list_entries where firm_id is not null")[0][0] == 0


def test_agreement_with_exact_name_candidates_guards_apply(conn, entries):
    upsert_firm(conn, FirmRecord(fei="1000000001", name="DELMAR COMMODITIES LTD", country_code="CA", country="Canada"),
                seen_on=TODAY)
    upsert_firm(conn, FirmRecord(fei="1000000002", name="AgroCrop Exports, Ltd", country_code="CA", country="Canada"),
                seen_on=TODAY)
    resolve_red_list(conn)
    lookup_entries(conn, FakeClient({
        "DELMAR COMMODITIES LTD": match("1000000001", "DELMAR COMMODITIES LTD"),
        "AgroCrop Exports, Ltd": match("3000000009", "AGROCROP EXPORTS LTD"),
    }), limit=10)

    report = agreement(conn)
    assert (report["compared"], report["agree"]) == (2, 1)
    assert report["disagreements"][0]["fda_name"] == "AgroCrop Exports, Ltd"

    with pytest.raises(AgreementTooLowError):
        apply_lookups(conn, today=TODAY, min_agreement=0.98, min_compared=2)
    assert rows(conn, "select count(*) from red_list_entries where firm_id is not null")[0][0] == 0
    assert apply_lookups(conn, today=TODAY, min_agreement=0.98, min_compared=50)["applied"] == 2
