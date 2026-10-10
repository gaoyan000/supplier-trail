"""Map raw FDA records to immutable firm/event records. Summaries use FDA's own terms only (design §10 Rule 2)."""
from dataclasses import dataclass, field
from datetime import date

from .normalize import check_date, parse_fda_date, record_hash


@dataclass(frozen=True)
class FirmRecord:
    fei: str | None
    name: str
    address: str | None = None
    city: str | None = None
    country_code: str | None = None
    country: str | None = None


@dataclass(frozen=True)
class EventRecord:
    firm: FirmRecord
    type: str
    occurred_on: date | None
    summary: str
    source: str
    source_record_id: str | None
    source_record_hash: str
    quarantine_reason: str | None
    product_code: str | None = None
    alert_number: str | None = None
    source_url: str | None = None
    details: dict = field(default_factory=dict)


def _clean(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _join_address(*parts) -> str | None:
    return ", ".join(p for p in (_clean(x) for x in parts) if p) or None


def _dashboard_firm(raw: dict, name_field: str) -> FirmRecord:
    state = raw.get("State")
    return FirmRecord(
        fei=_clean(raw.get("FEINumber")),
        name=_clean(raw.get(name_field)) or "Not supplied",
        address=_join_address(raw.get("AddressLine1"), raw.get("AddressLine2"), raw.get("City"), state, raw.get("ZipCode")),
        city=_clean(raw.get("City")),
        country_code=_clean(raw.get("CountryCode")),
        country=_clean(raw.get("CountryName")),
    )


def _event(*, firm, etype, raw_date, summary, source, record_id, raw, today, **extra) -> EventRecord:
    occurred = parse_fda_date(raw_date)
    return EventRecord(
        firm=firm,
        type=etype,
        occurred_on=occurred,
        summary=summary,
        source=source,
        source_record_id=record_id,
        source_record_hash=record_hash(source, raw),
        quarantine_reason=check_date(occurred, today=today),
        details=raw,
        **extra,
    )


def refusal_to_event(raw: dict, *, today: date) -> EventRecord:
    charges = _clean(raw.get("RefusalCharges")) or "not listed"
    product = _clean(raw.get("ProductCodeDescription"))
    summary = f"Shipment refused · FDA charge codes: {charges}" + (f" · Product: {product}" if product else "")
    return _event(
        firm=_dashboard_firm(raw, "FirmName"), etype="refusal", raw_date=raw.get("RefusalDate"),
        summary=summary, source="dashboard.import_refusals", record_id=_clean(raw.get("ShipmentID")),
        raw=raw, today=today, product_code=_clean(raw.get("ProductCode")), source_url=_clean(raw.get("FirmProfile")),
    )


def compliance_to_event(raw: dict, *, today: date) -> EventRecord:
    action = _clean(raw.get("ActionType")) or "Compliance action"
    etype = "warning_letter" if action.lower() == "warning letter" else "compliance_action"
    center = _clean(raw.get("Center"))
    summary = f"FDA {action}" + (f" ({center})" if center else "")
    return _event(
        firm=_dashboard_firm(raw, "LegalName"), etype=etype, raw_date=raw.get("ActionTakenDate"),
        summary=summary, source="dashboard.compliance_actions", record_id=_clean(raw.get("CaseInjunctionID")),
        raw=raw, today=today, source_url=_clean(raw.get("FirmProfile")),
    )


_INSPECTION_TYPES = {"NAI": "inspection_nai", "VAI": "inspection_vai", "OAI": "inspection_oai"}


def inspection_to_event(raw: dict, *, today: date) -> EventRecord:
    code = (_clean(raw.get("ClassificationCode")) or "").upper()
    if code not in _INSPECTION_TYPES:
        raise ValueError(f"unknown inspection classification: {code!r}")
    summary = f"FDA inspection · Classification: {_clean(raw.get('Classification')) or code}"
    return _event(
        firm=_dashboard_firm(raw, "LegalName"), etype=_INSPECTION_TYPES[code], raw_date=raw.get("InspectionEndDate"),
        summary=summary, source="dashboard.inspections_classifications", record_id=_clean(raw.get("InspectionID")),
        raw=raw, today=today, source_url=_clean(raw.get("FirmProfile")),
    )


def recall_to_event(raw: dict, *, today: date) -> EventRecord:
    firm = FirmRecord(
        fei=_clean(raw.get("FIRMFEINUM")),
        name=_clean(raw.get("FIRMLEGALNAM")) or "Not supplied",
        country=_clean(raw.get("FIRMCOUNTRYNAM")),
    )
    klass = _clean(raw.get("CENTERCLASSIFICATIONTYPETXT"))
    reason = _clean(raw.get("PRODUCTSHORTREASONTXT"))
    summary = f"Recall {raw.get('RECALLNUM')}" + (f" · Class {klass}" if klass else "") + (f" · {reason}" if reason else "")
    return _event(
        firm=firm, etype="recall", raw_date=raw.get("RECALLINITIATIONDT"), summary=summary,
        source="ires.recalls", record_id=_clean(raw.get("RECALLNUM")), raw=raw, today=today,
    )
