# SupplierTrail — UI/UX Design

Companion to `design_fda_supplier_risk.md` (product, legal §10) and `research/week0_findings.md` (positioning).
Stack: Next.js (SSR/ISR for public pages) + Tailwind + shadcn/ui (Radix) + Lucide icons + Recharts.

---

## 1. Design principles

| # | Principle | Why (from project context) | In practice |
|---|---|---|---|
| 1 | **Records, not verdicts** | Legal §10: no scores, no implied wrongdoing. Equally, no implied "safe" (a paid customer relying on a green check is negligent-misrepresentation risk) | No traffic lights, no risk score, **no green check for "clean"**. Show counts, dates, FDA wording, source links |
| 2 | **Every fact is traceable** | Truth + fair-report defense; trust with QA buyers | Each event row: date · FDA wording · source link. Page header: "Per FDA, as of {date}" |
| 3 | **Calm reference, not threat dashboard** | Buyers are small importers and QA managers, not analysts. Fear-styling also reads as accusation | Editorial "registry" look: white space, borders over shadows, one accent colour |
| 4 | **Watching is the product** | FDA's free FSER tool already does lookup; we win on alerts, bulk screening, records | One primary CTA everywhere: **Watch this supplier**. Lookup is free and unlimited |
| 5 | **Two densities** | Public pages are read once from Google; the app is used weekly by people managing lists | Public = comfortable reading (16–18px, 720px measure). App = compact tables (14px, 40px rows) |

**Rejected tool defaults:** Fira Code headings (too "developer" for this audience), and status green/amber/red (conflicts with Principle 1).

---

## 2. Users and core journeys

| Journey | User | Path | Success metric |
|---|---|---|---|
| **A. Search → Watch** | Amazon/DTC importer checking a factory | Google "{firm} FDA" → supplier page → Watch → magic-link signup → watchlist | Entity page → watch rate |
| **B. Bulk screen** | QA manager with 40 suppliers | Pricing/Home → Screen your list → upload CSV → review matches → results → download FSVP records | Uploads → paid |
| **C. Alert → re-evaluate** | Any watcher | Email "Change: Supplier X added to Import Alert 99-19" → change page → **record re-evaluation** → saved to FSVP log | Alert → acknowledged rate |
| D. Listed firm | Factory on a red list | Google "how to get off import alert" → guide → "Talk to a specialist" | Lead form submits |

Journey C is the one FDA's free tool cannot do, and it maps straight onto §1.505(c) "promptly reevaluate… documented".

---

## 3. Information architecture

```text
PUBLIC (SSR, indexable)                         APP (auth, noindex)
/                      search + this week's     /app                 watchlist (home)
                       changes                  /app/screen          bulk screen (CSV)
/supplier/{fei}-{slug} supplier record          /app/changes         change feed / inbox
/import-alert/{n}      alert + entries          /app/changes/{id}    change detail + re-evaluate
/import-alert/{n}/{e}  one red-list entry       /app/records         FSVP log (all evaluations)
/country/{c}[/{ind}]   lists                    /app/settings        team, billing, alerts
/refusal-reason/{ch}
/updates/{yyyy}/{mm}   monthly changes          Global header (both): logo · Search · Pricing ·
/guides/*              FSVP & removal guides     Guides · [Sign in] / [Watchlist]
/pricing, /corrections, /methodology
```

Navigation: a **top bar only**. There is no sidebar until the app has more than 5 sections. Breadcrumbs on public pages (Home › Import alerts › 99-19 › India). The current section is underlined.

---

## 4. Visual system

### Style
**"Registry"**: a clean, document-like minimalism. Flat surfaces, 1px borders, 6px radius, almost no shadow (modals only). Data-dense tables appear only inside the app. Light-first, with a full dark theme.

### Colour tokens

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#F8FAFC` | `#0B1220` | page |
| `--surface` | `#FFFFFF` | `#111A2E` | cards, tables |
| `--ink` | `#0F172A` | `#E2E8F0` | primary text (17:1 / 13:1) |
| `--ink-muted` | `#475569` | `#94A3B8` | secondary text (7.5:1 / 6.9:1) |
| `--border` | `#E2E8F0` | `#1E293B` | dividers |
| `--accent` | `#0369A1` | `#38BDF8` | links, primary CTA, focus ring (5.9:1 on white) |
| `--accent-fg` | `#FFFFFF` | `#0B1220` | text on CTA |
| `--status-listed-bg / fg` | `#FFFBEB` / `#92400E` | `#2A1E0B` / `#FCD34D` | **"On FDA import alert"** chip (7:1) |
| `--status-record-bg / fg` | `#F1F5F9` / `#334155` | `#1E293B` / `#CBD5E1` | "Refusals on record", "Warning letter on record" |
| `--status-none-bg / fg` | `#F1F5F9` / `#475569` | same as record | "No records found in sources searched" (**neutral, never green**) |
| `--new` | `#0369A1` | `#38BDF8` | dot for "new since you last looked" |
| `--danger` | `#B91C1C` | `#F87171` | **system only**: errors, destructive actions. Never used for suppliers |

Rule: every status chip = **icon + text + colour**, so colour is never the only signal. Icons: `flag` (listed), `file-text` (on record), `search` (none found), `circle-dot` (new).

### Typography
| Role | Font | Size / weight | Notes |
|---|---|---|---|
| Headings | **Lexend** | 32/24/20/18, 600 | Designed for readability; calm, modern-official |
| Body & UI | **Source Sans 3** | 16 (public 17), 400; labels 500 | `font-variant-numeric: tabular-nums` in tables |
| Identifiers | **IBM Plex Mono** | 14, 500 | FEI numbers, alert numbers (99-19), shipment IDs, dates in tables |

Line height 1.6 body / 1.25 headings. Public reading measure max 72ch.

### Layout
- 4/8 spacing scale; section rhythm 16/24/32/48.
- Container 1200px; reading column 720px.
- Breakpoints 375 / 768 / 1024 / 1440.
- Icons: Lucide, 1.5px stroke, 16/20/24 sizes only. No emoji anywhere.

### Motion
150–200ms ease-out for state changes; skeletons for loads over 300ms; no decorative animation; `prefers-reduced-motion` disables all transitions.

---

## 5. Key screens

> All firm names, FEIs and events in these wireframes are **fictional** placeholders. Never use real firms in mockups, demos or marketing (legal §10).

### 5.1 Home (public)
```text
┌──────────────────────────────────────────────────────────────────────┐
│ SupplierTrail      Search  Import alerts  Guides  Pricing   [Sign in]│
├──────────────────────────────────────────────────────────────────────┤
│  Know when a supplier's FDA record changes.                          │
│  Free lookup of FDA import alerts, refusals and warning letters for  │
│  foreign food & supplement suppliers. Watch them and get an email    │
│  the day something changes.                                          │
│  ┌────────────────────────────────────────────────────┐ ┌─────────┐  │
│  │ 🔍 Supplier name or FEI number                      │ │ Search  │  │
│  └────────────────────────────────────────────────────┘ └─────────┘  │
│   Autocomplete: Name · City, Country · FEI 3000000000                │
│   or  Screen a whole supplier list (CSV) →                           │
├──────────────────────────────────────────────────────────────────────┤
│  This week at FDA (food)        Data as of 2026-10-09 · Methodology  │
│  ● 12 firms added to import alerts   ● 214 shipments refused         │
│  ● 3 firms removed from import alerts                                │
│  [table: date · FDA name · country · what happened · alert/charge]   │
├──────────────────────────────────────────────────────────────────────┤
│  How it works: 1 Look up  2 Watch  3 Get alerted + keep FSVP records │
│  Built for FSVP: §1.505 / §1.512 compliance-history checks           │
│  Pricing teaser · FAQ                                                │
└──────────────────────────────────────────────────────────────────────┘
```
(The 🔍 marks the Lucide `search` icon in the input; it is not an emoji.) The "This week" feed provides freshness for SEO, shows proof that we watch, and is a reason to come back.

### 5.2 Supplier page (money page)
```text
Home › Suppliers › China › Example Foods Co., Ltd
┌──────────────────────────────────────────────────────────────────────┐
│ EXAMPLE FOODS CO., LTD                       [ Watch this supplier ] │
│ FEI 3000000000 · Example City, China          [ FSVP record (PDF) ] │
│ Human foods · Snack foods                                            │
│ ⚑ On FDA import alert 99-19 (published 2025-03-14)                    │
│ Per FDA, as of 2026-10-09 · Sources ▾                                │
├──────────────┬──────────────┬──────────────┬─────────────────────────┤
│ Import alerts│ Refusals (5y)│ Warning ltrs │ Last FDA action         │
│      1       │      7       │      0       │ 2026-09-30 (9 days ago) │
├──────────────┴──────────────┴──────────────┴─────────────────────────┤
│ Record   [All] [Import alerts] [Refusals] [Inspections] [Recalls]    │
│ 2026-09-30  Refusal    "11, 274, 64" → FDA charges: … (expand)  ↗ FDA│
│             Product: 33L… Candy, shipment line MC2-…                 │
│ 2025-03-14  Import alert  Added to 99-19 (Salmonella)          ↗ FDA │
├──────────────────────────────────────────────────────────────────────┤
│ Refusals by year (bar, 5 bars, direct labels; table toggle)          │
│ ⓘ What an import refusal means (FDA definition, 2 lines)             │
│ Related: other firms on 99-19 in this province · same product code   │
│ Found an error? Report it — we review within 48 hours                │
└──────────────────────────────────────────────────────────────────────┘
```
- The ⚑ and ⓘ glyphs stand for Lucide `flag` and `info` icons.
- Mobile order: identity → status → Watch (sticky bottom bar on mobile) → counts (2×2) → record (cards, not table) → the rest.
- Charges are shown as FDA's text, with code → description expanded inline. We never paraphrase into adjectives.
- If the page is `noindex` (single-signal supplier), the same layout is still served, so it stays useful to logged-in users.

### 5.3 Red-list entry page (verbatim FDA)
The header block reads **"As published by FDA on Import Alert 99-19"**, followed by FDA's exact name, address, products and date. Under it:
- a verified FEI link if one exists ("Linked FDA record: FEI 30…"), or
- nothing at all. There is no "possible match" on public pages (§10, Rule 1).

### 5.4 Import alert page
FDA title + plain summary · counts by country (horizontal bar, top 10) · filterable entry table (country, date published, product) · link to FDA's original page · "Watch this alert" (notifies on any add or remove).

### 5.5 App: Watchlist (home after login)
```text
┌──────────────────────────────────────────────────────────────────────┐
│ Watchlist (23/25)   [ + Add suppliers ▾ ]  Search · Filter: status ▾ │
├───┬───────────────────────────┬─────────┬─────────────────┬──────────┤
│ ● │ Supplier                  │ Country │ FDA status      │ Changed  │
├───┼───────────────────────────┼─────────┼─────────────────┼──────────┤
│ ● │ Example Foods Co., Ltd    │ China   │ ⚑ Import alert  │ 2d ago   │
│   │ Sample Spice Exports      │ India   │ ▤ 2 refusals    │ 4 mo ago │
│   │ Demo Seafood JSC          │ Vietnam │ ⌕ None found    │ —        │
└───┴───────────────────────────┴─────────┴─────────────────┴──────────┘
 ● = new change, unacknowledged · Row → supplier page (app view) · Export CSV
```
- ▤ and ⌕ stand for Lucide `file-text` and `search` icons.
- Empty state: "Watch your first supplier." Search box plus "or upload a CSV", and an example row.

### 5.6 App: Bulk screen (Journey B)
A 4-step flow with a step indicator; Back is always available.
1. **Upload**: drag and drop a CSV or paste rows; a template is downloadable.
2. **Map columns**: name*, country*, address, FEI (all optional except name and country).
3. **Review matches**: grouped **Exact (FEI)**, **Likely (name + country)**, **Needs your choice** (candidate list with address shown side by side), and **Not found**. *The user confirms likely matches, which resolves the verified-link problem for private use.*
4. **Results**: status per supplier, then "Watch all", "Download FSVP records (ZIP of PDFs)" and "Export CSV".

### 5.7 App: Change detail + re-evaluation (Journey C, the differentiator)
```text
Change · 2026-10-08 · Example Foods Co., Ltd (FEI 3000000000)
  Added to FDA Import Alert 99-19 (Salmonella) — published 2026-10-07  ↗ FDA
  Before: no import alerts   →   After: 1 import alert
──────────────────────────────────────────────────────────────
Record your re-evaluation (FSVP §1.505(c))
  Decision:  ( ) Continue — no change to verification
             ( ) Continue with added verification (describe)
             ( ) Hold shipments pending review
             ( ) Stop importing from this supplier
  Notes: [                                                    ]
  Evaluated by: [name]  Title: [ ]  Date: [2026-10-09]
  [ Save to FSVP log ]          Save as draft (autosaved)
```
The saved record is dated, attributed and immutable, with edits appended as versions. The PDF export carries the FDA snapshot used. Wording note: we record **the user's** decision; our UI never suggests which option to pick.

### 5.8 Alert email
- Subject: `Change: Example Foods Co., Ltd added to FDA Import Alert 99-19`
- Body: one fact line, source link, **[Review and record re-evaluation]** button.
- Daily digest option.
- Plain-text alternative.

### 5.9 Pricing
Three columns (Free / Starter $29 / Pro $99) plus a "$19 one-time FSVP record" strip. Starter is highlighted. A "Very small importer?" callout explains §1.512 in two lines. An FAQ covers "How is this different from FDA's free search?", answered honestly: alerts, bulk, records.

---

## 6. Content and copy rules (enforced in CI)

- **FDA's words**: "refused", "import alert", "warning letter", "FDA charge: SALMONELLA". Banned: unsafe, dangerous, violator, blacklisted, risk score, "clean", "safe", "approved".
- **Neutral empty state**: "No records found in the FDA sources we searched (list) as of {date}." Never "No issues" or a ✓.
- **Dates**: absolute ISO date + relative ("2026-09-30 · 9 days ago"). Data freshness is shown on every page.
- **Numbers**: tabular figures; counts always have a time window ("Refusals (5 years)").
- **Headings and titles**: `{FDA name} — FDA import refusal & import alert records`.
- **Errors**: say what happened, why, and what to do next (e.g. "CSV row 14 is missing a country. Add it or skip the row").

---

## 7. Accessibility and quality checklist

- WCAG 2.2 AA: contrast verified per token (table §4); focus ring 2px `--accent` with 2px offset; skip link; one `h1` per page with sequential headings.
- Status = icon + text + colour; charts get a table toggle and an `aria-label` summary.
- Tables: sortable with `aria-sort`; they become cards under 768px. No horizontal page scroll at 375px.
- Touch targets ≥44px; the sticky Watch bar on mobile respects the safe area.
- Forms: visible labels, inline validation on blur, error under the field, focus moves to the first error; re-evaluation drafts autosave.
- Performance: public pages SSR/ISR, no client JS needed to read the record; LCP < 2.0s; fonts `display=swap` with only 2 weights each; charts lazy-loaded below the fold.
- `prefers-reduced-motion` and `prefers-color-scheme` both honoured.

---

## 8. Build order (matches design §8 weeks)

| Week | Screens |
|---|---|
| 2 | Tokens + layout shell, Home (search + this-week feed), Supplier page, Import alert page, Red-list entry page, Methodology, Corrections |
| 3 | Sign-in (magic link), Watchlist, Change feed + **change detail with re-evaluation**, alert email, Pricing + Stripe, $19 PDF |
| 4 | Bulk screen flow, FSVP log + ZIP export, guides template |

**Mockups (built 2026-10-09):** Home, Supplier page and Change + re-evaluation, clickable on a design canvas: https://claude.ai/artifact/JPBUiHQLJQ8P9SZ2kzBabD (private; share from its Share menu before sending to interviewees). All data in them is fictional.

**Before building:** use the 3 mockups and show them to the 5 interviewees. Their reaction to the re-evaluation screen is the best early test of willingness to pay.
