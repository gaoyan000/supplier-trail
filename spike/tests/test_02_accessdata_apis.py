"""accessdata.fda.gov REST APIs: Enforcement Reports (iRES recalls), Product Code Builder, FEI lookup."""
import pytest

from conftest import require_key
from fda_clients import accessdata

IRES_COLUMNS = ("recallnum,firmlegalnam,firmfeinum,firmcountrynam,centercd,productdescriptiontxt,"
                "productshortreasontxt,recallinitiationdt,centerclassificationtypetxt,eventlmd")


def test_ires_food_recalls_with_fei(save_sample, metric):
    require_key("ENFORCEMENT_REPORTS_KEY")
    payload = {"displaycolumns": IRES_COLUMNS, "filter": "[{'centercd':['CFSAN']}]",
               "start": 1, "rows": 500, "sort": "productid", "sortorder": "desc"}

    status, body = accessdata("iresapi/recalls/", payload, "ENFORCEMENT_REPORTS_KEY")

    assert status == 200 and body.get("MESSAGE") == "success", body
    records = body["RESULT"]
    coverage = sum(1 for r in records if r.get("FIRMFEINUM")) / len(records)
    foreign = [r for r in records if r.get("FIRMCOUNTRYNAM") != "United States"]
    save_sample("ires_food_recalls", records)
    metric("ires.recalls.food", total=body["RESULTCOUNT"], sampled=len(records),
           fei_coverage=round(coverage, 3), foreign_share=round(len(foreign) / len(records), 3))
    assert coverage >= 0.8


def test_pcb_product_search(save_sample, metric):
    require_key("PCB_API_KEY")

    status, body = accessdata("pcbapi/v1/product/name/", "spice", "PCB_API_KEY")

    assert status == 200 and body.get("MESSAGE") == "success", body
    result = body["RESULT"]
    assert {"INDID", "PRODDESC"} <= set(result["COLUMNS"])
    rows = [dict(zip(result["COLUMNS"], row)) for row in result["DATA"]]
    save_sample("pcb_spice_products", rows)
    metric("pcb.product_name", query="spice", results=body["RESULTCOUNT"])


def test_fei_lookup_by_name(metric):
    require_key("FEI_PORTAL_KEY")
    payload = {"FIRMNAME": "DASENLIN FOOD CO., LTD", "FIRMADDRESS1": "", "FIRMADDRESS2": "", "FIRMCITY": "",
               "FIRMSTATE": "", "FIRMCOUNTRY": "CN", "FIRMPROVINCE": "", "FIRMZIP": ""}

    status, body = accessdata("feiapi/firmdata/feidata/", payload, "FEI_PORTAL_KEY")

    metric("fei_api.lookup", status=status, message=body.get("MESSAGE"))
    if body.get("STATUSCODE") == 401:
        pytest.fail("FEI API denied the key (401). Access to this API may need separate approval.")
    assert body.get("MESSAGE", "").lower().startswith("success"), body
