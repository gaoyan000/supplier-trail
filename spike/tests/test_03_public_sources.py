"""No-key sources: import-alert HTML (red lists) and openFDA food enforcement."""
import re

import pytest
import requests

from fda_clients import IMPORT_ALERT_LIST_URL, IMPORT_ALERT_URL, OPENFDA_URL, UA, get_html, parse_alert_list, parse_red_list

SALMONELLA_ALERT = "99-19"


@pytest.fixture(scope="module")
def alerts():
    return parse_alert_list(get_html(IMPORT_ALERT_LIST_URL))


@pytest.fixture(scope="module")
def salmonella_red_list(alerts):
    page = next(a["page"] for a in alerts if a["number"] == SALMONELLA_ALERT)
    return parse_red_list(get_html(IMPORT_ALERT_URL.format(page=page)))


def test_import_alert_index(alerts, save_sample, metric):
    assert len(alerts) >= 100
    assert all(re.fullmatch(r"\d{2}-\d{2,3}", a["number"]) for a in alerts)
    save_sample("import_alert_index", alerts, n=len(alerts))
    metric("import_alerts.index", count=len(alerts), types=sorted({a["type"] for a in alerts}))


def test_red_list_parses(salmonella_red_list, save_sample, metric):
    firms = salmonella_red_list
    assert len(firms) >= 500
    assert all(f["name"] and f["country"] for f in firms)
    by_country = {}
    for f in firms:
        by_country[f["country"]] = by_country.get(f["country"], 0) + 1
    top = dict(sorted(by_country.items(), key=lambda kv: -kv[1])[:5])
    save_sample("red_list_99_19", firms, n=100)
    metric("import_alerts.red_list_99_19", firms=len(firms), countries=len(by_country), top_countries=top)


def test_red_list_dates_parse(salmonella_red_list):
    dated = [f for f in salmonella_red_list if re.fullmatch(r"\d{2}/\d{2}/\d{4}", f["date_published"])]
    assert len(dated) / len(salmonella_red_list) >= 0.95


def test_openfda_food_enforcement(save_sample, metric):
    r = requests.get(OPENFDA_URL, params={"limit": 100, "sort": "report_date:desc"}, headers=UA, timeout=60)

    assert r.status_code == 200
    body = r.json()
    records = body["results"]
    assert {"recalling_firm", "country", "reason_for_recall", "recall_number"} <= set(records[0])
    save_sample("openfda_food_enforcement", records)
    metric("openfda.food_enforcement", total=body["meta"]["results"]["total"],
           newest_report=records[0].get("report_date"), has_fei_field="fei_number" in records[0] or
           "openfda" in records[0] and "fei_number" in records[0]["openfda"])
