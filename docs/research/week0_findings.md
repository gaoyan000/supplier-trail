# Week 0 Findings: SERP Audit, Keywords, FSVP Regulation

Date: 2026-10-07. Companion to `../design_fda_supplier_risk.md`.

> **Method caveat:** the SERP audit used a web-search tool, not a logged-out Google session. Rankings approximate Google; repeat the P1 queries in an incognito Google window before committing. No search-volume data was available, so priorities are by intent and SERP weakness, not volume.

---

## 1. FSVP regulation: verified against eCFR (21 CFR Part 1, Subpart L, as of 2026-10-01)

Raw text is saved in `cfr_1.5xx.txt`.

| Claim in design | Verdict | Exact text / section |
|---|---|---|
| Importer must evaluate supplier compliance history incl. warning letters and import alerts | ✅ **Confirmed** | §1.505(a)(1)(iii)(B): "…including whether the foreign supplier is the subject of an FDA warning letter, import alert, or other FDA compliance action related to food safety" |
| Evaluation must be documented | ✅ | §1.505(a)(2): "You must document the evaluation" |
| Re-evaluate promptly on new information | ✅ **Confirmed** | §1.505(c)(1): "you must promptly reevaluate the concerns … when you become aware of new information about these factors, and the reevaluation must be documented" |
| …and at least every 3 years | ✅ | §1.505(c)(2) |
| Records signed, dated, producible to FDA | ✅ | §1.510(a)(2) sign and date; §1.510(b) available promptly, offsite records retrievable within 24h |
| Retention | ⚠️ **Correct the design**: 2 years, not 3 | §1.510(c): ≥2 years after created; evaluation records ≥2 years after use discontinued |
| Dietary supplements covered | ✅ with nuance | §1.511(c) "other importers of dietary supplements" must still comply with §1.505(a)(1)(ii)–(iv), which includes the compliance-history check. §1.511(a)/(b) importers that are themselves (or whose customer is) Part 111 manufacturers are **exempt from §1.505** |
| **Very small importers (< $1M/yr food)** | ✅ **Strongest finding** | §1.512(c)(1)(i): "you must evaluate … whether the foreign supplier is the subject of an FDA warning letter, import alert, or other FDA compliance action related to food safety, and document the evaluation". §1.512(c)(1)(ii): promptly re-evaluate on new info, and every 3 years |
| Someone else may do the evaluation | ⚠️ Nuance | §1.505(d) / §1.512(c)(1)(iii): the importer may rely on another entity's evaluation **if performed by a "qualified individual"**, and must document its review |

**Implications**
1. For **very small importers**, the compliance-history check is close to *the whole* FSVP supplier evaluation. Our product covers it almost completely. This is the sharpest wedge: small Amazon/DTC food and supplement importers.
2. **Supplement manufacturers** that import ingredients for their own Part 111 production (§1.511(a)) are exempt from §1.505. They are not FSVP buyers; they are still "avoid detention" buyers.
3. Our report supplies **facts**; the importer (or its qualified individual) performs and signs the evaluation. That is consistent with the legal design in §10. Don't market it as "the evaluation".

---

## 2. SERP audit (30 seed queries, 6 clusters)

| Cluster | Queries | Who ranks | Gap? |
|---|---|---|---|
| **Firm names** (8) | DASENLIN, Bikanervala, Karma Ayurveda, MDH, Anhui Xinong, Fuzhou Golden Banyan, Dalian Xinglongken, Boudjebel | **No result for the exact firm in 7/8.** Lookalike pages from `globalkeysolutions.net` (FDA inspection records), `regdatalab.com`, Panjiva; news only for famous brands (MDH) | ✅ **Big gap.** FDA's own firm profiles are not indexed |
| **Alert numbers** (6) | 99-19, 66-41, 16-131, 45-02, 99-45, 23-14 | **FDA accessdata page is #1** for most; then FDA country pages, JETRO PDFs, govdelivery PDFs, news | ⚠️ #1 is unbeatable; #2–5 weak, so aim to be the best non-FDA result |
| **Country × category** (6) | China food list, India spices red list, China supplements, DWPE spices, India salmonella 2026, refused Sept 2026 | News (Business Today, The Wire, Siasat), STR trade-report blog, AgroSpectrum, old ERS reports | ✅ Gap: no structured, current list pages |
| **How-to / removal** (2) | get off import alert, removal petition | Certified Laboratories, Registrar Corp, Diaz Trade Law, Datamyne, FDA's removal page | ✅ Paid intent confirmed (labs, lawyers), so lead-gen is viable |
| **Lookup / tool** (3) | check supplier on import alert, compliance history lookup, supplier FDA registered | **FDA Firm/Supplier Evaluation Resources** (datadashboard.fda.gov/oii/fd/fser.htm), Registrar Corp **ComplyHub**, Redica, an Apify "FDA Import Alert & Supplier Ban Monitor" (0–100 risk score), ArgusHQ enforcement MCP | ❌ **Contested** (see §3) |
| **FSVP** (5) | supplier evaluation, compliance history check, very small importer, re-evaluation, Amazon sellers | fda.gov, eCFR/Cornell LII, **Registrar Corp blog dominates**, law firms, NSF, miratag templates, a Fiverr gig | ⚠️ Head terms are Registrar's; long tail is winnable (small sites rank) |

---

## 3. Competitors found (updates design §0)

| Competitor | What it is | Threat | Our angle |
|---|---|---|---|
| **FDA Data Dashboard: Firm/Supplier Evaluation Resources** | **Free, official** one-search lookup by firm name/FEI across inspections, citations, compliance actions, recalls, import refusals **and alerts**. Explicitly built for FSVP | 🔴 **High for one-off lookup.** "Free lookup" is no longer unique | FDA's tool has **no monitoring/alerts, no bulk upload, no evaluation record, and isn't indexed by Google**. We sell what FDA doesn't do |
| **Registrar Corp: ComplyHub** + Marketplace | Paid FSVP software: supplier monitoring with 100M+ shipment records, scoring, document management; Marketplace claims compliance history for 500K suppliers | 🔴 **High for paid FSVP** | Likely priced for mid/large importers (pricing not public; verify). We target **very small importers**: self-serve, $29/mo, no sales call |
| **Redica Systems** | Enterprise quality/regulatory intelligence | 🟡 Different segment (pharma/enterprise) | None needed |
| **globalkeysolutions.net**, **regdatalab.com** | Programmatic FDA record pages (inspections, warning letters) indexed by Google | 🟠 **Direct SEO competitors** for firm-name queries | They show inspections/warning letters; neither showed import refusals + red lists per firm in these SERPs. Verify coverage |
| Apify "FDA Import Alert & Supplier Ban Monitor", ArgusHQ MCP | Developer tools / scrapers with risk scores | 🟢 Low (dev audience) | Evidence the data is reachable; also a reminder of the risk-score legal issue |
| Consultants (Certified Labs, Diaz Trade Law, Registrar services) | Removal petitions, FSVP consulting | Partners, not competitors | **Lead-gen buyers** |

### Follow-up — ✅ resolved 2026-10-09

**Result:** FDA's firm profile lists current import alerts by FEI (FEI 3015850818 → Import Alert 99-19, 08/24/2022, matching our scraped entry exactly). It is served by FDA's internal Qlik backend, so we use it for **manual verification only**, not automation. See design §8 task 6 and §10 Rule 1.

Original note:

FDA's FSER tool shows import alerts **per firm (with FEI)**. If the Dashboard exposes that linkage (firm profile pages or an undocumented dataset), it could replace most of our red-list name matching *and* make links "verified" under the §10 legal rule. Endpoint guesses (`import_alerts`, etc.) returned 404. **Next step:** inspect a firm-profile page's network calls in a browser for a known red-listed FEI (e.g. 3013266062).

---

## 4. Revised positioning (from findings)

Old: "Check any supplier's FDA history in 10 seconds." FDA now does that for free.

New:
> **"FDA's records, watched for you. Get an alert the day a supplier's FDA status changes, screen your whole supplier list at once, and keep a dated FSVP record of every check, built for small importers."**

| What | FDA FSER (free) | ComplyHub (paid) | **Us** |
|---|---|---|---|
| One-firm lookup | ✅ | ✅ | ✅ (and **indexed in Google**) |
| Daily change alerts on watched suppliers | ❌ | ✅ | ✅ |
| Bulk screen a CSV of suppliers | ❌ | ✅ | ✅ |
| Dated, signed-ready FSVP evaluation record | ❌ | ✅ | ✅ |
| Self-serve price for a < $1M importer | n/a | ? (verify) | **$29/mo** |

---

## 5. Keywords

`keywords_100.csv` holds 100 keywords built from **real FDA data** (firm names from refusal and red-list samples, the 25 most relevant food alerts, measured top countries and charges).

| Cluster | Count | Priority | Target page |
|---|---|---|---|
| Firm names | 20 | P1 | supplier / red-list entry pages |
| FSVP | 15 | P1 | guides + pricing |
| How-to / tool | 15 | P1 | guides, home search, pricing |
| Country × category | 15 | P2 | country/industry pages |
| Refusal reason | 10 | P2 | refusal-reason pages |
| Alert numbers | 25 | P3 | import-alert pages (FDA owns #1) |

**Next:** run the 50 P1 keywords through a volume tool (Google Keyword Planner is free with an Ads account; Ahrefs/Semrush trial) before Week 2.
