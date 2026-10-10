import json
from datetime import date
from pathlib import Path

import pytest

from supplier_trail_etl.transform import (
    compliance_to_event,
    inspection_to_event,
    recall_to_event,
    refusal_to_event,
)

FIXTURES = Path(__file__).parent / "fixtures"
TODAY = date(2026, 10, 9)


def load(name):
    return json.loads((FIXTURES / name).read_text())


class TestRefusal:
    def test_maps_firm_and_event(self):
        raw = load("refusals.json")[0]
        ev = refusal_to_event(raw, today=TODAY)
        assert ev.firm.fei == "2000043093"
        assert ev.firm.name == "Oak K.K., Corporation"
        assert ev.firm.country_code == "JP"
        assert "Sakaiminato" in ev.firm.address
        assert ev.type == "refusal"
        assert ev.occurred_on == date(2026, 9, 30)
        assert ev.product_code == "16AGD73"
        assert ev.source_record_id == "417-0416513-7/40002/1"
        assert ev.quarantine_reason is None

    def test_summary_uses_fda_terms_only(self):
        ev = refusal_to_event(load("refusals.json")[0], today=TODAY)
        assert ev.summary.startswith("Shipment refused")
        assert "2580" in ev.summary
        for banned in ("unsafe", "dangerous", "violator", "contaminated"):
            assert banned not in ev.summary.lower()

    def test_hash_is_stable_and_distinguishes_records(self):
        rows = load("refusals.json")
        assert refusal_to_event(rows[0], today=TODAY).source_record_hash == \
            refusal_to_event(dict(rows[0]), today=TODAY).source_record_hash
        hashes = {refusal_to_event(r, today=TODAY).source_record_hash for r in rows}
        assert len(hashes) == len(rows)

    def test_record_without_fei_is_still_mapped_by_name(self):
        raw = {**load("refusals.json")[0], "FEINumber": None}
        ev = refusal_to_event(raw, today=TODAY)
        assert ev.firm.fei is None and ev.firm.name

    def test_bad_date_is_quarantined_not_dropped(self):
        raw = {**load("refusals.json")[0], "RefusalDate": "2099-01-01"}
        assert refusal_to_event(raw, today=TODAY).quarantine_reason == "future_date"


class TestComplianceAction:
    def test_future_dated_warning_letter_is_quarantined(self):
        # The real FDA record dated 2026-10-29 found during the spike.
        ev = compliance_to_event(load("compliance_actions.json")[0], today=TODAY)
        assert ev.type == "warning_letter"
        assert ev.quarantine_reason == "future_date"

    def test_other_action_types(self):
        raw = {**load("compliance_actions.json")[1], "ActionType": "Injunction"}
        ev = compliance_to_event(raw, today=TODAY)
        assert ev.type == "compliance_action"
        assert "Injunction" in ev.summary


class TestInspection:
    @pytest.mark.parametrize("code,etype", [("NAI", "inspection_nai"), ("VAI", "inspection_vai"), ("OAI", "inspection_oai")])
    def test_classification_maps_to_type(self, code, etype):
        raw = {**load("inspections.json")[0], "ClassificationCode": code}
        assert inspection_to_event(raw, today=TODAY).type == etype

    def test_unknown_classification_rejected(self):
        raw = {**load("inspections.json")[0], "ClassificationCode": "XYZ"}
        with pytest.raises(ValueError):
            inspection_to_event(raw, today=TODAY)


class TestRecall:
    def test_maps_ires_record(self):
        ev = recall_to_event(load("recalls.json")[0], today=TODAY)
        assert ev.type == "recall"
        assert ev.firm.fei == "2921164"
        assert ev.occurred_on == date(2011, 4, 9)
        assert ev.source_record_id == "F-1143-2011"
        assert "Class 1" in ev.summary


def test_events_are_immutable():
    ev = refusal_to_event(load("refusals.json")[0], today=TODAY)
    with pytest.raises(AttributeError):
        ev.type = "other"
