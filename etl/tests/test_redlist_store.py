from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from supplier_trail_etl.db import insert_event, refresh_firm_aggregates, upsert_firm
from supplier_trail_etl.fda.import_alerts import AlertIndexRow, parse_red_list
from supplier_trail_etl.redlist import SnapshotDropError, apply_red_list_snapshot, upsert_alert
from supplier_trail_etl.resolve import resolve_red_list, verify_candidate
from supplier_trail_etl.transform import FirmRecord

pytestmark = pytest.mark.integration
FIXTURE = (Path(__file__).parent / "fixtures" / "red_list_99_19_canada.html").read_text()
ALERT = AlertIndexRow("99-19", "DWPE", date(2026, 10, 6), "Salmonella", "importalert_263.html")
DAY1, DAY2 = date(2026, 10, 8), date(2026, 10, 9)


def rows(conn, sql, *args):
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchall()


@pytest.fixture
def entries():
    return parse_red_list(FIXTURE, alert_number="99-19")


def test_first_snapshot_lists_every_entry_with_fda_date(conn, entries):
    upsert_alert(conn, ALERT)
    added, removed = apply_red_list_snapshot(conn, "99-19", entries, today=DAY1)
    assert (added, removed) == (6, 0)
    listed = rows(conn, "select occurred_on from events where type='alert_listed' order by occurred_on")
    assert len(listed) == 6 and listed[0][0] == date(2009, 9, 16)


def test_same_snapshot_twice_changes_nothing(conn, entries):
    upsert_alert(conn, ALERT)
    apply_red_list_snapshot(conn, "99-19", entries, today=DAY1)
    assert apply_red_list_snapshot(conn, "99-19", entries, today=DAY2) == (0, 0)


def test_removed_entry_is_deactivated_with_event(conn, entries):
    upsert_alert(conn, ALERT)
    apply_red_list_snapshot(conn, "99-19", entries, today=DAY1)
    assert apply_red_list_snapshot(conn, "99-19", entries[1:], today=DAY2) == (0, 1)
    (active, removed_on), = rows(conn, "select active, removed_on from red_list_entries where entry_key=%s",
                                 entries[0].entry_key)
    assert active is False and removed_on == DAY2
    assert rows(conn, "select count(*) from events where type='alert_removed'")[0][0] == 1


def test_existing_entry_details_refresh_without_new_events(conn, entries):
    upsert_alert(conn, ALERT)
    apply_red_list_snapshot(conn, "99-19", entries, today=DAY1)
    grown = [replace(entries[0], product_codes=entries[0].product_codes + ("99Z--99",)), *entries[1:]]
    assert apply_red_list_snapshot(conn, "99-19", grown, today=DAY2) == (0, 0)
    codes = rows(conn, "select product_codes from red_list_entries where entry_key=%s", entries[0].entry_key)[0][0]
    assert "99Z--99" in codes
    assert rows(conn, "select count(*) from events")[0][0] == 6


def test_large_drop_is_refused_as_probable_parse_failure(conn, entries):
    upsert_alert(conn, ALERT)
    many = [replace(entries[0], entry_key=f"k{i}", fda_name=f"Firm {i}") for i in range(20)]
    apply_red_list_snapshot(conn, "99-19", many, today=DAY1)
    with pytest.raises(SnapshotDropError):
        apply_red_list_snapshot(conn, "99-19", many[:5], today=DAY2)
    assert rows(conn, "select count(*) from red_list_entries where active")[0][0] == 20


CODES = {"Canada": "CA", "Mexico": "MX", "United States": "US", "South Korea": "KR"}


def _firm(conn, fei, name, country="Canada", code="from-name"):
    code = CODES.get(country) if code == "from-name" else code
    return upsert_firm(conn, FirmRecord(fei=fei, name=name, country_code=code, country=country), seen_on=DAY1)


def test_resolution_creates_unverified_candidates_only(conn, entries):
    upsert_alert(conn, ALERT)
    apply_red_list_snapshot(conn, "99-19", entries, today=DAY1)
    exact = _firm(conn, "1000000001", "DELMAR COMMODITIES LTD")
    fuzzy = _firm(conn, "1000000002", "Christan Mark Division of Karplasto Inc")
    noted = _firm(conn, "3003034798", "Original Bulk Packed Spice Co", country="United States")
    _firm(conn, "1000000003", "DELMAR COMMODITIES LTD", country="Mexico")  # wrong country

    stats = resolve_red_list(conn)

    cands = {(r[0], r[1]): r[2:] for r in rows(
        conn, "select e.fda_name, c.firm_id, c.match_method, c.link_status from red_list_candidates c "
              "join red_list_entries e on e.id=c.entry_id")}
    assert cands[("DELMAR COMMODITIES LTD", exact)] == ("exact_name", "unverified")
    assert cands[("Christan Mark Div of Karplasto Inc", fuzzy)] == ("fuzzy_name", "unverified")
    # FEI written in FDA notes may belong to another firm (a packer), so it is a candidate, never auto-verified.
    assert cands[("DION HERBS & SPICES", noted)] == ("fei_in_text", "unverified")
    assert all(status == "unverified" for _, status in cands.values())
    assert rows(conn, "select count(*) from red_list_entries where firm_id is not null")[0][0] == 0
    assert stats["entries_with_candidates"] == 3


def test_verify_links_entry_and_flags_firm(conn, entries):
    upsert_alert(conn, ALERT)
    apply_red_list_snapshot(conn, "99-19", entries, today=DAY1)
    firm_id = _firm(conn, "1000000001", "DELMAR COMMODITIES LTD")
    resolve_red_list(conn)
    entry_id = rows(conn, "select id from red_list_entries where fda_name='DELMAR COMMODITIES LTD'")[0][0]

    verify_candidate(conn, entry_id=entry_id, firm_id=firm_id, reviewer="yan",
                     evidence_url="https://datadashboard.fda.gov/oii/firmprofile.htm?FEIi=1000000001")
    refresh_firm_aggregates(conn, today=DAY2)

    assert rows(conn, "select firm_id from red_list_entries where id=%s", entry_id)[0][0] == firm_id
    assert rows(conn, "select risk_status from firms where id=%s", firm_id)[0][0] == "on_red_list"
    assert rows(conn, "select count(*) from events where firm_id=%s and type='alert_listed'", firm_id)[0][0] == 1
    assert rows(conn, "select link_status from firm_aliases where firm_id=%s", firm_id)[0][0] == "verified"


def test_country_names_compared_by_code_across_fda_spellings(conn):
    upsert_alert(conn, ALERT)
    korea = [replace(parse_red_list(FIXTURE, alert_number="99-19")[0], entry_key="kr1",
                     fda_name="DAELIM FISHERIES UNION CO.", country="KOREA (THE REPUBLIC OF)")]
    apply_red_list_snapshot(conn, "99-19", korea, today=DAY1)
    # One FDA dataset spells it "Korea (the Republic of)" with code KR; the firm's own record says "South Korea".
    _firm(conn, "2000000001", "Some Other Firm", country="Korea (the Republic of)", code="KR")
    target = _firm(conn, "2000000002", "DAELIM FISHERIES UNION CO.", country="South Korea")
    resolve_red_list(conn)
    assert rows(conn, "select firm_id, match_method from red_list_candidates")[0] == (target, "exact_name")


def test_country_name_without_code_uses_alias():
    from supplier_trail_etl.resolve import country_code_for
    index = {"syria": "SY"}
    assert country_code_for("SYRIAN ARAB REPUBLIC", None, index) == "SY"
    assert country_code_for("Burma", None, index) == "MM"
    assert country_code_for("Anything", "de", index) == "DE"
    assert country_code_for("Atlantis", None, index) is None
