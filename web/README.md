# SupplierTrail web

Public site (Next.js App Router, Tailwind). Reads the Postgres database that `etl/` fills.
Design: `docs/ui_ux_design.md`; legal rules for what a page may show: `docs/design_fda_supplier_risk.md` §10.

## Run locally

```bash
cp .env.example .env.local   # points at the local suppliertrail_dev database
npm install
npm run dev                  # http://localhost:3000/supplier/<fei>-<slug>
```

## Test

```bash
createdb suppliertrail_web_test   # once; the suite resets this database's schema
npm test
npm run lint && npx next typegen && npx tsc --noEmit
```

## Layout

- `src/lib/suppliers.ts`: read-only queries. Quarantined events and unverified red-list links are never returned.
- `src/lib/events.ts`: how FDA events are grouped and worded (FDA's terms only).
- `src/components/supplier/supplier-record.tsx`: the supplier page, a pure view over those queries.
- `src/app/supplier/[id]/page.tsx`: route, metadata, 404 and canonical redirect.
