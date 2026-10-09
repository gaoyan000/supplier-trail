# Design — SupplierTrail (suppliertrail.com): FDA Supplier Risk Monitor

Response to `public_api_seo_saas_handoff.md`. This doc makes the §13 decision, then works through the §13 checklist.

---

## 0. Decision: B (FDA Supplier Risk Monitor), with a validation gate

**Why B over A and C**

| | A. Gov Recompete | B. FDA Supplier Risk | C. OSHA |
|---|---|---|---|
| SEO competition | **High.** HigherGov, GovTribe and GovWin already have contractor/agency pages and expiring-contract views, and their domains are strong | **Medium (checked 2026-10-07).** Firm-name searches are open (no page for the exact firm in 7/8 tests); lookup-tool and FSVP head terms are contested by FDA's free FSER tool and Registrar Corp ComplyHub. See `research/week0_findings.md` | Medium. Violation Tracker is free; OSHA's own search is poor |
| Entity resolution | Medium (UEI helps) | **Verified workable.** FEI is on 100% of refusals, inspections, warning letters and recalls; red lists lack FEI but 80% resolve by exact name (see §2) | **Hard.** No stable employer ID; names are messy |
| How often data changes | Monthly | Weekly (red-list adds/removals, refusals) | Weekly |
| Buyer reach | Contractors (crowded sales channel) | SMB importers, Amazon/DTC supplement and cosmetics brands, customs brokers | GCs (where ISN, Avetta and Highwire are entrenched) |
| Time to MVP | 4–6 wks | **3–4 wks** | 5–6 wks (entity cleanup) |

A is the bigger business, but you would be entering a SERP that is already won. B lets you cheaply test the whole funnel (index → click → watch → pay). The ETL, entity, snapshot and alert core carries over to A or C if B fails.

**Gate:** if the 40 prototype pages get fewer than 500 impressions/week after 6 weeks of indexing, stop and re-run the test on C.

> ✅ SERP check done 2026-10-07 (web-search proxy, not a logged-out Google session). Full results: `research/week0_findings.md`. **Key change:** FDA's free *Firm/Supplier Evaluation Resources* tool already does one-firm lookup, so the free lookup is table stakes. We sell monitoring, bulk screening and dated records (see §1).

---

## 1. Positioning and users

> **"FDA's records, watched for you. Get an alert the day a supplier's FDA status changes, screen your whole supplier list at once, and keep a dated FSVP record of every check, built for small importers."**

Why this wording: FDA's free FSER tool already does one-firm lookup (§0). What it lacks, and we sell, is **change alerts, bulk screening, a dated evaluation record, and pages indexed by Google**.

### Lead customer: food & supplement importers with FSVP obligations

Under FSMA's **Foreign Supplier Verification Program** (21 CFR Part 1, Subpart L), the US importer of food (dietary supplements included) must:

1. **Evaluate each foreign supplier's compliance history** before approving it, including whether the supplier is subject to an **FDA warning letter, import alert, or other compliance action** (§1.505).
2. **Re-evaluate promptly when it becomes aware of new information** about those risks, and at least every 3 years (§1.505(c)).
3. **Keep written records** of those evaluations and make them available to FDA on request (§1.510).

Requirement 1 is the lookup, requirement 2 is the **alert**, and requirement 3 is the **report**. So the paid product maps straight onto a legal obligation, rather than being a nice-to-have. Most small importers do this today by hand across FDA sites, once a year, in a spreadsheet, if they do it at all. FSVP is a common source of FDA 483 observations for small importers.

> ✅ Verified against eCFR 2026-10-01 (`research/cfr_1.5xx.txt`). Corrections and additions:
> - Record retention is **≥2 years** (§1.510(c)), not 3.
> - **Very small importers** (< $1M/yr human food, §1.512) have a *simplified* FSVP whose core is exactly the compliance-history check (warning letters, import alerts) plus prompt re-evaluation on new information. **This is our sharpest segment.**
> - Supplement importers that are themselves Part 111 manufacturers (§1.511(a)) are **exempt from §1.505**: they are detention-avoidance buyers, not FSVP buyers. Other supplement importers (§1.511(c)) must still do the compliance-history check.
> - The importer may rely on another entity's evaluation only if a *qualified individual* performed it (§1.505(d)), so our report stays "facts + sources" and the importer signs the evaluation.

> *Example: Raj, QA manager at a spice importer with 40 suppliers in India and Vietnam, uploads his supplier list. 2 come back flagged: one red-listed for Salmonella, one refused 3× this year. He downloads 40 supplier evaluation PDFs into his FSVP file. Six months later he gets an email: "Supplier X added to Import Alert 99-19." That email is his "aware of new information" trigger, and the re-evaluation record is generated for him.*

### All segments

| Segment | Pain | Pays for | Priority |
|---|---|---|---|
| **FSVP importers (food, spices, seafood, supplements)** | Legal duty to evaluate and re-evaluate suppliers, with documentation; FDA FSVP inspections | Bulk screening, change alerts, evaluation reports | **Lead** |
| SMB importers / Amazon & DTC supplement brands | A shipment detained at the port (DWPE) means $5–50K stuck plus lost inventory. These are also FSVP importers, often without knowing it | Pre-buy check + monitoring of 5–50 suppliers | High |
| Customs brokers / freight forwarders | Clients' shipments get flagged | Bulk screening, team seat | Medium |
| **The listed firms themselves** | They want to get off an import alert | Monitoring of their own status, plus **lead-gen to FDA consultants** | Side revenue |

The last row is easy to miss. Queries like "how to get removed from import alert 66-40" carry high commercial intent, and consultants pay well for those leads.

**MVP scope consequence:** FSVP covers food and supplements only, so the MVP ingests **food + dietary supplement records only** (FDA industry codes 02–41, 45–47, 50, 52–54). Devices, cosmetics and drugs come later. That is less ETL and a sharper message.

**Competitors (verified):**
- **FDA FSER tool**: free one-firm lookup, no alerts, bulk upload or records, not indexed by Google.
- **Registrar Corp ComplyHub**: paid FSVP monitoring with shipment data; pricing not public, likely aimed at larger importers.
- **globalkeysolutions.net / regdatalab.com**: programmatic FDA record pages competing for firm-name SEO.

Our angle: self-serve monitoring + records at $29–99/mo for **very small importers**, no sales call. Week 0 interviews must ask whether they use FDA FSER or ComplyHub today.

---

## 2. Source audit — ✅ verified 2026-10-06/07

Verified by `spike/` (17/18 tests pass; run `cd spike && .venv/bin/pytest`). Real samples are saved in `spike/samples/`.

### Sources used by the MVP

| Source | Content | Access | Key | FEI coverage | Volume (measured) | Refresh |
|---|---|---|---|---|---|---|
| **Data Dashboard API** `import_refusals` | Every refused shipment line: firm, address, country, product code, charges, date | JSON POST, Authorization-User/Key headers | **FEI** | **100%** of recent food refusals | ~1,000 food rows per ~5 weeks (≈10K/yr); 99% foreign; 427 distinct firms in 5 weeks | Daily |
| **Data Dashboard API** `compliance_actions` | **Warning letters**, injunctions, seizures | same | **FEI** | 100% | All product types; filter `ProductType = Food/Cosmetics` | Daily |
| **Data Dashboard API** `inspections_classifications`, `inspections_citations` | Inspection outcome (NAI/VAI/OAI), 483 citations with CFR references | same | **FEI** | 100% | Only **30%** of refused foreign firms have any inspection | Weekly |
| **Import Alerts** HTML (`cms_ia/ialist.html` + `importalert_N.html`) | **154** active alerts; red list grouped by country; product codes; problems; date published | Scrape (`div.div-info` blocks) | **Name + address only** (FEI only occasionally, in free-text notes) | ~0% | 99-19 (Salmonella) alone: 1,223 firms, 81 countries | Daily diff |
| **Enforcement Reports (iRES) API** | Recalls with classification, reason, product | Form POST, `payload=` JSON, unique `signature` per call | **FEI** (`firmfeinum`) | 100% | 37,792 food (CFSAN) recalls; sample was 100% US firms | Weekly |
| **Product Code Builder API** | Industry → class → product code tree | Form POST | code | n/a | e.g. "spice" → 337 codes | Monthly |

### Dropped or blocked

| Source | Decision | Why |
|---|---|---|
| openFDA food enforcement | **Dropped** | The same recall data as iRES but **without FEI** |
| fda.gov warning-letters page scrape | **Dropped** | Replaced by Data Dashboard `compliance_actions`, which has FEI |
| Import Refusal Report bulk download | **Dropped** | Replaced by the Data Dashboard API (same data, queryable) |
| **FEI Portal API** (`rest/feiapi`) | **Blocked**: 401 | The account has FEI *Portal* (website) access but no API key. Requested by email to `OIIWebApplicationTechTeam@fda.hhs.gov`. Not on the critical path. |

### API mechanics learned (for the ETL)

- **Data Dashboard:** `POST /v1/{endpoint}` with JSON `{start, rows, sort, sortorder, filters, columns}`. All of `sort`, `sortorder`, `filters` and `columns` are required, even when empty. Max **5,000 rows/page**; paging with `start` returns no overlap. Filters take value lists, e.g. `{"FEINumber": [...50 FEIs]}` or `{"CountryName": ["China"]}`. Food category value: `ProductCategory = "Human Foods"`. A success response carries `statuscode: 400` in the body, and "no results" is `412`. Check `message`, not just the HTTP status.
- **accessdata APIs (iRES, PCB):** responses are cached per URL, so every call needs a unique `?signature=`. iRES dates are `MM/DD/YYYY` strings and sort as text, so sort by `productid` instead.
- **Data quality:** FDA data contains bad dates (e.g. a warning letter dated 3 weeks in the future). The ETL must reject or quarantine future and impossible dates.
- **Rate:** all calls answered in under 2 s; no throttling seen at spike volume. Still use polite pacing in production (≤ 2 req/s).

### Entity resolution (the moat), as measured

```text
FEI-keyed sources (refusals, inspections, warning letters, recalls)
        └─ join directly on FEI ............................ 100% coverage
Red-list firms (name + address only)
        ├─ step 1: exact name match → refusal records ....... 24/30 resolved (80%), 0 ambiguous
        ├─ step 2: normalized name + country fuzzy match .... (to build; target ≥90% total)
        ├─ step 3: FEI API lookup by name + address ......... (once key granted)
        └─ unresolved → firm page without FEI, slug = name-country, noindex until resolved
```

Each name-based link stores `match_method` and `match_confidence`. **Publishing a link is governed by the verified-link rule in §10.** The match rate above is for internal use; it is *not* the public publish rate.

**Product insight from the join:** 70% of refused foreign suppliers have **no FDA inspection record** and none had compliance actions. For most foreign food suppliers, **refusals + red lists are the only public signal**, and nobody presents them together. That gap is our core content.

---

## 3. SEO: URL architecture

```text
/supplier/{fei}-{slug}                      entity page (core; food-only count TBD in Week 1)
/supplier/{fei}-{slug}/refusals             only if ≥3 refusals
/import-alert/{number}                      e.g. /import-alert/99-19 (154 active; numbers can be NN-NNN, e.g. 16-105)
/import-alert/{number}/{country}            red list filtered by country
/import-alert/{number}/{entry-slug}         one red-list entry, FDA's exact name + address (no FEI claim)
/country/{country}                          e.g. /country/china
/country/{country}/{industry}               e.g. /country/india/spices
/industry/{industry}                        e.g. /industry/dietary-supplements
/refusal-reason/{charge}                    e.g. /refusal-reason/salmonella
/rankings/most-refused-{industry}-exporters-{country}
/updates/{yyyy}/{mm}                        monthly: new red-list adds, removals, warning letters
/guides/how-to-get-off-fda-import-alert     the only hand-written pages (5–10), lead-gen
```

**Index rules (to avoid thin pages):**
- `noindex` any supplier with exactly one refusal and no other events, until it gets a second signal.
- Cross-dimension pages are indexed only when they have ≥10 rows.
- Sitemaps are split by type: `suppliers-*.xml`, `alerts.xml`, `countries.xml`, `updates.xml`.
- JSON-LD `Organization` on supplier pages and `Dataset` on alert/country pages.
- Every page shows "Source: FDA, fetched {date}" with links to the originals. This builds trust and is your legal cover.

**Seed keyword patterns** (expand to 100 in Week 0 using real firm names from the data):

```text
{firm name} fda                      import alert {number}
{firm name} import alert             fda red list {country}
{firm name} fda warning letter       fda import refusal {product}
fda detention without physical examination {product}
how to get off fda import alert      fda import alert {industry} {country}
is {firm} fda registered             fda refused shipments {month} {year}

# FSVP intent (lead-customer queries; feed the guide pages)
fsvp supplier evaluation template    fsvp compliance history check
fsvp requirements dietary supplements fsvp reevaluation new information
fsvp records fda inspection          foreign supplier verification checklist
```

Add `/guides/fsvp-supplier-evaluation`, `/guides/fsvp-for-amazon-supplement-sellers` and `/guides/fsvp-reevaluation` to the guide set. They target the buyer directly and link to the screening tool.

---

## 4. Database schema (Postgres)

```sql
firms            (id, fei UNIQUE NULL, canonical_name, slug, country, city, address,
                  identity_key UNIQUE,      -- fei, or hash(normalized name + address + country) when no FEI
                  first_seen, last_event_at, risk_status, indexable bool)
firm_aliases     (firm_id, name, address, source,
                  match_method,             -- fei | exact_name | fuzzy_name | fei_api | manual
                  match_confidence,
                  link_status,              -- verified | unverified | disputed | rejected  (§10)
                  verified_by, verified_at)
red_list_entries (id, alert_number, fda_name, fda_address, country, date_published,
                  slug, firm_id NULL,       -- set only when the alias link_status = verified
                  active bool, removed_on NULL)
correction_requests (id, page_url, firm_id NULL, alias_id NULL, requester_email, message,
                  status, received_at, resolved_at, outcome)
import_alerts    (number PK,                -- text, 'NN-NN' or 'NN-NNN'
                  title, industry, type, page_url, last_published)
events           (id, firm_id, type, occurred_on, product_code, alert_number NULL,
                  summary, details jsonb, source, source_url,
                  source_record_id,         -- ShipmentID | recallnum | CaseInjunctionID | InspectionID
                  source_record_hash UNIQUE,
                  quarantined bool DEFAULT false)  -- bad/future dates held back from pages + alerts
                  -- type: alert_listed | alert_removed | refusal | recall |
                  --       warning_letter | inspection_oai | inspection_vai | inspection_nai
snapshots        (id, source, fetched_at, content_hash, raw_path)   -- raw stored in R2/S3
product_codes    (code PK, industry, description)
users            (id, email, plan, stripe_customer_id, created_at)
watches          (user_id, firm_id NULL, saved_query jsonb NULL, created_at)
alert_deliveries (id, user_id, event_id, channel, sent_at, opened_at)
```

`risk_status` is **factual, not a score**: `on_red_list` / `recent_refusals` / `clear`. (`on_green_list` is dropped until green lists are confirmed: 99-19 showed only red-list firms.) Don't ship a 0–100 "risk score" about named companies in the MVP. It is a defamation risk, and the facts already sell the product.

**Change detection (red lists):** for each alert, parse the firm set → compare it with the previous snapshot's set → write `alert_listed` / `alert_removed` events → `source_record_hash` dedupes them → a daily alert job joins new events to `watches`.

---

## 5. Architecture

```text
GitHub Actions cron (or a $5 VPS)
   └─ Python ETL: fetch → store raw in R2 → normalize → validate dates → upsert → diff → events

Daily jobs (incremental, sorted by date DESC, stop at last-seen date):
   dashboard.import_refusals      filter ProductCategory=Human Foods
   dashboard.compliance_actions   filter ProductType=Food/Cosmetics
   import_alerts.scrape           154 pages → red-list set diff → listed/removed events
Weekly jobs:
   dashboard.inspections_*        only for FEIs we hold (batched 50 FEIs per filter)
   ires.recalls                   centercd=CFSAN
   entity.resolve                 exact → fuzzy → FEI API (when available)
Monthly:
   pcb.product_codes              refresh reference table
One-off backfill: full history of food refusals via 5,000-row pages.
Postgres (Neon / Supabase)
Next.js on Vercel or Cloudflare (ISR, revalidate 24h; on-demand revalidate for changed firms)
Stripe Checkout + Customer Portal      Resend (alert emails, daily digest)
Auth: magic link (Auth.js / Supabase Auth)
```

Skip for now: Redis, a search engine (Postgres `pg_trgm` is enough for name search), queues, and AI.

---

## 6. MVP screens

**Supplier page** (the money page):

```text
┌──────────────────────────────────────────────────────────────┐
│ Zhejiang ABC Biotech Co., Ltd.            FEI 3012345678     │
│ Hangzhou, China · Dietary supplements                         │
│ ● ON FDA RED LIST — Import Alert 54-1 since 2025-03-14        │
│ [ 🔔 Watch this supplier ]   [ FSVP evaluation report $19 ]   │
├──────────────────────────────────────────────────────────────┤
│ Import alerts 1   Refusals (5y) 7   Warning letters 1         │
│ Last FDA action 23 days ago                                   │
├──────────────────────────────────────────────────────────────┤
│ Timeline                                                      │
│ 2026-09-12  Refusal  — Unapproved new drug (vitamin C caps)   │
│ 2025-03-14  Added to Import Alert 54-1                        │
│ 2024-11-02  Warning letter — CGMP                             │
├──────────────────────────────────────────────────────────────┤
│ Refusals by charge (bar)   Refusals by year (bar)             │
│ Similar suppliers in Hangzhou · Other firms on 54-1           │
│ Source: FDA (links) · fetched 2026-10-06 · Report an error    │
└──────────────────────────────────────────────────────────────┘
```

Other screens: home/search, import-alert page, country/industry list, watchlist dashboard (table: firm, status, last change), and pricing.

---

## 7. Monetization and pricing experiment

| Plan | Price | Limits |
|---|---|---|
| Free | $0 | Unlimited public pages, **3 watches**, weekly digest |
| Starter | $29/mo | 25 watches, instant email alerts, CSV export, **unlimited FSVP evaluation PDFs for watched suppliers** |
| Pro | $99/mo | 250 watches, CSV bulk upload/screen, 3 seats, **re-evaluation log** (every alert plus the user's acknowledgement, exportable for an FDA inspection) |
| One-off report | $19 | FSVP supplier evaluation PDF, no account needed |

**FSVP evaluation report contents:** supplier identity (name, address, FEI), date of check, sources searched with links, findings per source (import alerts, refusals, warning letters, recalls, inspection classifications), a "no records found" statement where applicable, and a blank section for the importer's own conclusion and signature. We supply the facts; **the importer makes the evaluation**. Never word the report as "approved" or "compliant".

- **The one-off report is the experiment.** Many SMB buyers check a supplier once, before a PO, and will never subscribe. If report sales beat subscriptions, lean into that.
- **The subscription sells the re-evaluation requirement.** The legal duty to re-evaluate on new information is what turns a one-off check into a recurring need.
- **Lead-gen:** a "Need help getting removed?" CTA on red-listed firm pages and the guides goes to 2–3 partner consultants, at $50–200 per qualified lead.
- **Ads:** none at launch. AdSense on a niche B2B site pays pennies and makes a risk tool look cheap. Revisit if a consumer-facing recall section grows.

---

## 8. Plan (4 weeks + observation)

**Week 0 (2–3 days): validation, no product code**
1. ✅ **Done 2026-10-07.** SERP audit of 30 seed queries → `research/week0_findings.md` §2. Repeat the P1 queries in incognito Google to confirm.
2. ✅ **Done 2026-10-07.** Checked every source in §2: access, fields and FEI presence. 17/18 tests pass; samples are in `spike/samples/`. The FEI API key is pending with FDA (non-blocking).
3. ✅ **Done 2026-10-07.** 100 keywords → `research/keywords_100.csv` (50 P1). Still to do: volume check via Keyword Planner.
4. ✅ **Done 2026-10-07.** Read 21 CFR 1.505, 1.510, 1.511 and 1.512; claims confirmed with the corrections noted in §1 → `research/week0_findings.md` §1.
6. Find FDA FSER's import-alert↔FEI linkage (browser network inspection of a firm profile). If it's reachable, it replaces most name matching and yields "verified" links under §10.
5. Talk to 5 FSVP importers (spice/seafood importers, Amazon supplement sellers via forums or LinkedIn). Ask how they check suppliers today and whether they'd pay $29/mo. → verify: 5 call notes; ≥2 say yes

**Week 1: data**
- Promote `spike/fda_clients.py` + `samples/` into `etl/`; the saved samples become parser test fixtures.
- Backfill the full food-refusal history (5,000-row pages) and record the real distinct-FEI count. This sizes the supplier-page count in §3.
- ETL for import alerts (scrape + diff), refusals, warning letters (`compliance_actions`), and iRES recalls. → verify: counts match the FDA Dashboard totals ±1%
- Date validation: quarantine future and impossible dates. → verify: the known 2026-10-29 warning letter is quarantined
- Entity build: FEI join, then exact name, then fuzzy name + country for red-list firms. → verify: ≥90% of red-list firms resolved; hand-check 50 random matches with 0 wrong links

**Week 2: SEO pages**
- Supplier, import-alert, country and industry pages; sitemaps; JSON-LD; index rules.
- Launch, submit to Search Console. → verify: GSC shows discovered URLs

**Week 3: conversion**
- Magic-link auth, watches, daily diff → email alert, Stripe ($29/$99), $19 report.
- → verify: a test watch on a firm with a staged synthetic event delivers an email

**Week 4: content + outreach**
- 5 guide pages, monthly `/updates` page, a post in 2–3 Amazon-seller / import forums.

**Weeks 5–10: observe.** Track impressions/week, entity page → watch rate, watch → paid, report sales.
Go/no-go at week 10: ≥2K impressions/week **and** ≥1 paying user, or pivot (reuse the pipeline for C or A).

---

## 9. Risks

| Risk | Mitigation |
|---|---|
| Wrong firm matched → you publicly say a clean company is red-listed | **Verified-link rule (§10)**: unverified matches are never public; disputed links are hidden immediately; 48h review |
| Google treats it as scaled thin content | Index rules in §3; every page must show unique timeline data |
| Import alert HTML changes and the scraper breaks | Raw snapshots + parser tests on saved fixtures + alert if the row count drops >20% |
| FDA data errors (e.g. future-dated records) show up as false alerts | Date validation; `quarantined` events never reach pages or emails |
| FDA API access is revoked, rate-limited or changes shape | Keys are per-account and free; raw snapshots in R2 let pages keep serving; the spike test suite runs nightly as a canary |
| FEI API key never granted | Not needed: exact + fuzzy name matching covers ≥80%; unresolved red-list firms get `noindex` pages |
| Recall data is mostly US firms, so weak for foreign-supplier pages | Treat recalls as secondary; refusals + red lists are the primary signal for foreign suppliers |
| Low willingness to pay | The $19 report and lead-gen are non-subscription revenue to test early |
| Report mistaken for legal compliance advice | Report states facts plus sources only; disclaimer that the FSVP evaluation is the importer's responsibility; no "approved" wording |

---

## 10. Legal risk and mitigations

> Risk analysis, not legal advice. A media/First Amendment lawyer reviews page templates and terms before launch (see `launch_prerequisites.md` E1).

### Where the risk is

Accurately republishing FDA records is protected by **truth** and, in most states, the **fair report privilege**. That privilege **does not cover misattribution**: attaching an FDA record to the wrong company is our own false statement. **Section 230 does not apply**, because the matching is our content. Anti-SLAPP statutes help, since food safety is a public issue.

| Scenario | Likely claim | Risk |
|---|---|---|
| FEI-keyed record on its own FEI page, quoted accurately | none | 🟢 Low |
| Red-list entry shown with FDA's exact name/address | none (fair report) | 🟢 Low |
| **Record name-matched to the wrong company** | defamation, trade libel, tortious interference | 🔴 High |
| "High risk" / "unsafe" / "violator" labels or scores | defamation by implication | 🟠 Medium |
| Stale status (firm removed from list, page still says listed) | defamation (now false) | 🟠 Medium |
| SEO titles implying violations | defamation by implication | 🟠 Medium |
| Wrong data in a paid FSVP report | contract / negligent misrepresentation | 🟡 Low–Med |

Realistic plaintiffs are **US importers and distributors** (in recalls and warning letters) more than foreign factories. Most likely event: a cease-and-desist email. Even a weak suit costs $10–50K+ to defend, so we prevent errors and respond fast.

### Rule 1: verified-link rule (the core control)

| What it is | Shown publicly? |
|---|---|
| Record carrying FEI X, from FDA → shown on FEI X's page | ✅ always |
| Red-list entry → its own page, FDA's exact name + address, no FEI claim | ✅ always (indexable) |
| Red-list entry ↔ FEI page link where `link_status = verified` | ✅ |
| Any other match (`unverified`) | ❌ not public. Logged-in users only, labelled "Possible match, unverified. Confirm with FDA". Never indexed. |
| `disputed` / `rejected` link | ❌ hidden immediately |

`verified` requires one of:
- the FEI appears in FDA's own text for that entry,
- the FEI API returns that FEI for FDA's name + address, or
- exact normalized name + same country + address similarity ≥ threshold **and** human review.

Human review is cheap at our scale: about 1,200 entries on the largest alert, and most firms appear on few alerts.

### Rule 2: FDA's words only

- Use FDA terms verbatim: "refused", "FDA charge: SALMONELLA", "Import Alert 99-19", "Classification: OAI".
- **Banned in UI, titles, meta and emails:** unsafe, dangerous, contaminated (unless quoting FDA), violator, fraud, blacklisted, risk score / grade.
- Title template: `{FDA name} — FDA import refusal & import alert records`.
- Standard explainer on every page: "An import refusal means FDA determined a shipment appeared to violate FDA requirements; it is not a court finding against the firm."

### Rule 3: freshness and provenance

- Every fact shows "per FDA, as of {fetched date}" and a link to the FDA source.
- Removals are published on the next daily run, e.g. "Removed from Import Alert 99-19 on {date}". Records FDA deletes are hidden within 48h.
- If the ETL fails for more than 72h, pages show a "data may be out of date" banner.
- Raw FDA snapshots are kept in R2 for at least 3 years as evidence of what FDA published, and when.

### Rule 4: corrections

- "Report an error" link on every page, plus `corrections@`, stored in `correction_requests`.
- **A disputed match is hidden immediately** while under review. The FDA record itself stays, since it is FDA's fact. Respond within 48h and log the outcome.
- A firm saying "we fixed the problem" is not a correction. Point them to FDA's removal process (or the consultant lead-gen).

### Rule 5: paid-report and contract protection

- ToS: data is as-is from public FDA sources, no warranty, liability capped at fees paid in the last 12 months, not legal advice, the user verifies with FDA, governing law in a state with a strong anti-SLAPP statute.
- FSVP reports list the **match method** for every record and the snapshot date. The importer makes the evaluation.

### Rule 6: business shields (before launch)

- LLC formed; no personal name on the site as publisher.
- **Media liability (E&O) insurance bound before launch.**
- One-hour lawyer review of templates, the banned-words list, ToS and the corrections policy.

### Rule 7: no individuals

- Firm names that look like a person's name (sole proprietors): page is `noindex` and the name is not used in the title.
- Never publish personal contact details, even when FDA lists them.

### Enforcement in code

- CI test: rendered templates contain none of the banned words.
- CI test: a page render fails if it would show an alias whose `link_status != verified`.
- Daily job: firms whose `risk_status` disagrees with the latest snapshot → fix or hide before pages revalidate.
