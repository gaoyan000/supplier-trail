"""Core design assumption: FEI links sources, and red-list names can be resolved to FEIs."""
import pytest

from conftest import require_key
from fda_clients import IMPORT_ALERT_LIST_URL, IMPORT_ALERT_URL, dashboard, get_html, parse_alert_list, parse_red_list

SAMPLE_SIZE = 50


@pytest.fixture(autouse=True)
def _key():
    require_key("FDA_DASHBOARD_KEY")


@pytest.fixture(scope="module")
def refused_foreign_feis():
    _, body = dashboard("import_refusals", filters={"ProductCategory": ["Human Foods"]}, rows=2000,
                        sort="RefusalDate", order="DESC", columns=["FEINumber", "CountryName"])
    feis = []
    for r in body["result"]:
        if r.get("FEINumber") and r.get("CountryName") != "United States" and r["FEINumber"] not in feis:
            feis.append(r["FEINumber"])
    return feis[:SAMPLE_SIZE]


def hit_rate(endpoint: str, feis: list[str]) -> tuple[float, int]:
    status, body = dashboard(endpoint, filters={"FEINumber": feis}, rows=5000, columns=["FEINumber"])
    assert status == 200, body
    found = {r["FEINumber"] for r in body.get("result") or []}
    return len(found & set(feis)) / len(feis), len(body.get("result") or [])


def test_multi_value_fei_filter_works(refused_foreign_feis):
    _, body = dashboard("import_refusals", filters={"FEINumber": refused_foreign_feis[:5]}, rows=500,
                        columns=["FEINumber"])
    assert {r["FEINumber"] for r in body["result"]} <= set(refused_foreign_feis[:5])


def test_refused_firms_link_to_other_datasets(refused_foreign_feis, metric):
    assert len(refused_foreign_feis) == SAMPLE_SIZE

    inspections, n_insp = hit_rate("inspections_classifications", refused_foreign_feis)
    actions, n_act = hit_rate("compliance_actions", refused_foreign_feis)

    metric("join.refusal_fei_to_other_sets", sample=SAMPLE_SIZE,
           inspections_hit_rate=round(inspections, 3), inspection_rows=n_insp,
           compliance_actions_hit_rate=round(actions, 3), compliance_rows=n_act)
    assert inspections > 0 or actions > 0, "FEIs from refusals never appear elsewhere"


def test_red_list_names_resolve_to_fei(metric, save_sample):
    alerts = parse_alert_list(get_html(IMPORT_ALERT_LIST_URL))
    page = next(a["page"] for a in alerts if a["number"] == "99-19")
    china = [f for f in parse_red_list(get_html(IMPORT_ALERT_URL.format(page=page))) if f["country"] == "CHINA"]
    sample = china[:30]

    matches = []
    for firm in sample:
        _, body = dashboard("import_refusals", filters={"FirmName": [firm["name"]]}, rows=50,
                            columns=["FEINumber", "FirmName"])
        feis = sorted({r["FEINumber"] for r in body.get("result") or [] if r.get("FEINumber")})
        matches.append({**firm, "fei_candidates": feis})

    resolved = [m for m in matches if len(m["fei_candidates"]) == 1]
    ambiguous = [m for m in matches if len(m["fei_candidates"]) > 1]
    save_sample("red_list_name_to_fei", matches, n=len(matches))
    metric("join.red_list_name_to_fei_exact", sample=len(sample), resolved_unique=len(resolved),
           ambiguous=len(ambiguous), unresolved=len(sample) - len(resolved) - len(ambiguous))
    assert resolved, "No red-list firm name matched a refusal record exactly"
