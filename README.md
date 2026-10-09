# SupplierTrail

**suppliertrail.com** — FDA's records, watched for you. Change alerts, bulk supplier screening and dated FSVP records for small US food and dietary-supplement importers.

## Status

- ✅ Design and launch checklist written
- ✅ FDA data access verified (17/18 tests pass; FEI Portal API key pending)
- ✅ Week 0 research: SERP audit, 100 keywords, FSVP regulation check
- ⏳ Importer interviews, local app scaffold

## Layout

```text
docs/
  public_api_seo_saas_handoff.md   original idea handoff
  design_fda_supplier_risk.md      product + technical design (start here)
  launch_prerequisites.md          accounts / legal / setup checklist
  research/                        Week 0 findings, keywords, 21 CFR FSVP text
spike/                             FDA data-access validation (Python, pytest)
```

## Run the data-access tests

```bash
cd spike
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # fill in your FDA API credentials
.venv/bin/pytest
```
