"""FDA Data Dashboard API: the FEI-keyed backbone (refusals, inspections, citations, compliance actions)."""
import pytest

from conftest import require_key
from fda_clients import dashboard

FOOD_CATEGORY = "Human Foods"

ENDPOINTS = {
    "import_refusals": ["FEINumber", "FirmName", "CountryName", "ProductCode", "RefusalDate", "RefusalCharges"],
    "inspections_classifications": ["FEINumber", "LegalName", "CountryName", "InspectionEndDate", "Classification"],
    "inspections_citations": ["FEINumber", "LegalName", "InspectionEndDate", "ActCFRNumber", "ShortDescription"],
    "compliance_actions": ["FEINumber", "LegalName", "CountryName", "ActionType", "ActionTakenDate"],
}


@pytest.fixture(autouse=True)
def _key():
    require_key("FDA_DASHBOARD_KEY")


def fei_coverage(records) -> float:
    return sum(1 for r in records if r.get("FEINumber")) / len(records)


@pytest.mark.parametrize("endpoint,required", ENDPOINTS.items())
def test_endpoint_returns_records_with_required_fields(endpoint, required, save_sample, metric):
    status, body = dashboard(endpoint, rows=200)

    assert status == 200 and body.get("message") == "Success.", body
    records = body["result"]
    assert len(records) == 200
    missing = [f for f in required if f not in records[0]]
    assert not missing, f"{endpoint} missing fields {missing}; got {list(records[0])}"
    save_sample(f"dashboard_{endpoint}", records)
    metric(f"dashboard.{endpoint}", reachable=True, fields=list(records[0]))


def test_recent_food_refusals_have_fei(save_sample, metric):
    status, body = dashboard(
        "import_refusals",
        filters={"ProductCategory": [FOOD_CATEGORY]},
        rows=1000, sort="RefusalDate", order="DESC",
    )

    assert status == 200 and body["result"], body
    records = body["result"]
    coverage = fei_coverage(records)
    foreign = [r for r in records if r.get("CountryName") not in ("United States", None)]
    save_sample("food_refusals_recent", records)
    metric("dashboard.import_refusals.food_recent_1000",
           newest=records[0]["RefusalDate"], oldest=records[-1]["RefusalDate"],
           fei_coverage=round(coverage, 3), foreign_share=round(len(foreign) / len(records), 3),
           unique_fei=len({r["FEINumber"] for r in records if r.get("FEINumber")}))
    assert coverage >= 0.9, f"Only {coverage:.0%} of recent food refusals carry an FEI"


def test_filter_by_country():
    status, body = dashboard("import_refusals", filters={"CountryName": ["China"]}, rows=50,
                             sort="RefusalDate", order="DESC")

    assert status == 200 and body["result"]
    assert {r["CountryName"] for r in body["result"]} == {"China"}


def test_pagination_returns_distinct_pages(metric):
    common = dict(filters={"ProductCategory": [FOOD_CATEGORY]}, rows=5000, sort="RefusalDate", order="DESC",
                  columns=["ShipmentID", "RefusalDate"])
    _, page1 = dashboard("import_refusals", start=1, **common)
    _, page2 = dashboard("import_refusals", start=5001, **common)

    ids1 = {r["ShipmentID"] for r in page1["result"]}
    ids2 = {r["ShipmentID"] for r in page2["result"]}
    metric("dashboard.pagination", page_size=len(page1["result"]), page2_size=len(page2["result"]),
           overlap=len(ids1 & ids2))
    assert len(page1["result"]) == 5000 and page2["result"]
    assert page1["result"][-1]["RefusalDate"] >= page2["result"][0]["RefusalDate"]


def test_food_warning_letters_available(save_sample, metric):
    status, body = dashboard("compliance_actions", filters={"ActionType": ["Warning Letter"]},
                             rows=1000, sort="ActionTakenDate", order="DESC")

    assert status == 200 and body["result"], body
    records = body["result"]
    product_types = sorted({r.get("ProductType") for r in records})
    save_sample("warning_letters_recent", records)
    metric("dashboard.compliance_actions.warning_letters",
           newest=records[0]["ActionTakenDate"], fei_coverage=round(fei_coverage(records), 3),
           product_types=product_types)
    assert fei_coverage(records) >= 0.9
