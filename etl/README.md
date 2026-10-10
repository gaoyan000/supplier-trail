# SupplierTrail data pipeline (`etl/`)

Pulls public FDA data into Postgres for supplier pages and change alerts. Design: `../docs/design_fda_supplier_risk.md` §2, §4, §5, §10.

## Setup (local)

```bash
brew install postgresql@16 && brew services start postgresql@16
createdb suppliertrail_dev && createdb suppliertrail_test
cd etl
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp .env.example .env        # add FDA API credentials; never commit .env
.venv/bin/st-etl migrate
```

## Jobs

| Command | Source | Notes |
|---|---|---|
| `st-etl sync refusals [--full]` | Data Dashboard `import_refusals` (Human Foods) | FEI on every row |
| `st-etl sync compliance [--full]` | `compliance_actions` (Food/Cosmetics) | Warning letters, injunctions, seizures |
| `st-etl sync inspections [--full]` | `inspections_classifications` (Food/Cosmetics) | NAI / VAI / OAI |
| `st-etl sync recalls [--full]` | Enforcement Reports (iRES), CFSAN | FEI on every row |
| `st-etl sync red-lists [--only 99-19]` | Import-alert HTML pages | Adds/removals → `alert_listed` / `alert_removed` events |
| `st-etl resolve` | — | Red-list entry → FEI **candidates** (never auto-verified) |
| `st-etl review-export out.csv` | — | Candidates + FDA firm-profile URL for human verification |
| `st-etl stats` | — | Counts for sizing and monitoring |

Without `--full`, a sync stops at the first page with no new rows (daily mode). Every raw page is archived to `data/raw/<source>/<date>/` (gitignored).

## Safety rules built in

- **Quarantine, don't drop:** future, missing or implausible dates are stored with `quarantined = true` and never count toward pages or alerts.
- **Red-list drop guard:** if an alert's parsed entries fall by more than 20%, the snapshot is refused (probable scraper break) instead of recording mass removals.
- **No automatic public links:** name and FEI-in-notes matches are `unverified` candidates. Only `verify_candidate()`, after a person checks FDA's firm profile, sets `red_list_entries.firm_id` (design §10 Rule 1).
- **Polite:** ≤ 2 requests/second, retries with backoff, identifying User-Agent.
- **Never call FDA internal endpoints** (`/internal/*`, the Qlik engine).

## Tests

```bash
.venv/bin/pytest            # unit + integration (uses suppliertrail_test)
.venv/bin/pytest -m "not integration"
```
