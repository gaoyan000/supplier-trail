# Public-API SEO SaaS — Design Handoff

## 1. Goal

Build a web product on top of a public API/dataset that can:

- Attract organic traffic through programmatic SEO.
- Target a niche with lower SEO competition than generic API-based sites.
- Monetize through subscriptions, ads, or both.
- Convert static lookup traffic into recurring usage through alerts, monitoring, and saved searches.
- Prefer commercially valuable, frequently changing datasets over entertainment or commodity APIs.

The working product principle is:

```text
Public API
    ↓
Large / hard-to-use public dataset
    ↓
Structured entity pages
    ↓
Programmatic SEO
    ↓
Free search / lookup
    ↓
Watch / Alert / Saved Search
    ↓
Recurring subscription
```

The product should not simply expose raw API data. The value is created by turning raw data into useful intelligence, rankings, comparisons, and alerts.

---

## 2. Current Opportunity Ranking

### Tier 1 — Best candidates

1. **Government Contract Recompete Radar**
   - Data: USAspending / federal contract data.
   - Target users: government contractors, sales teams, consultants, investors.
   - Core insight: identify contracts likely to expire or be recompeted in the next 3–18 months.
   - Monetization: $49–299+/month B2B subscription.
   - SEO surface: contractor pages, agencies, NAICS codes, states, expiring contracts.

2. **FDA Import / Supplier Risk Monitor**
   - Data: FDA import alerts, recalls, warning/enforcement data.
   - Target users: importers, distributors, sourcing teams, supplement/food/device companies.
   - Core insight: supplier risk and regulatory history.
   - Monetization: $29–299+/month depending on monitored suppliers and API/bulk access.
   - SEO surface: manufacturer pages, country pages, product categories, alert types.
   - Current belief: likely the best small niche for lower SEO competition and meaningful revenue.

3. **Employer Compliance / OSHA Intelligence**
   - Data: OSHA / Department of Labor / FastDOL-style enforcement records.
   - Target users: general contractors, procurement teams, insurance brokers, lenders, PE, supplier-risk teams.
   - Core insight: employer safety and compliance risk.
   - Monetization: $99–499+/month for vendor screening and bulk monitoring.
   - SEO surface: company pages, industry pages, state pages, violation type pages.

### Tier 2 — Strong but more competitive or complex

4. **Medical Device Recall Intelligence**
   - Data: openFDA.
   - Monetization: ads for consumer traffic + subscriptions for professional users.
   - Main feature: company/device recall history and alerts.

5. **Biotech Clinical Trial Change Detector**
   - Data: ClinicalTrials.gov.
   - Monetization: investor subscriptions / research tooling.
   - Main feature: detect changes in completion dates, enrollment, endpoints, status, sponsors, etc.
   - More differentiated than a generic PDUFA or catalyst calendar.

6. **Government Revenue Growth Screener**
   - Data: USAspending + public-company/ticker mapping.
   - Target users: investors.
   - Main feature: identify public companies with accelerating federal award activity.
   - Potential outputs:
     - fastest-growing defense contractors
     - companies with rising federal awards
     - AI companies winning government contracts
     - new DoD suppliers

### Lower priority / avoid for MVP

- Generic NPI lookup
- Generic patent search
- Generic weather / currency / crypto / recipe / movie / Pokémon / QR / stock quote tools

These are either too crowded or too easy to replicate without a strong differentiation layer.

---

## 3. Recommended Product Direction

The current strongest directions are:

### Option A — Government Contract Recompete Radar

**Positioning**

> Find federal contracts likely to be recompeted before the solicitation appears.

**Core user flow**

```text
Google search
    ↓
Contractor / agency / NAICS landing page
    ↓
See awards + estimated contract end / recompete windows
    ↓
Click "Watch this contractor" or "Alert me"
    ↓
Create account
    ↓
Email / dashboard alerts
    ↓
Paid subscription
```

**Example SEO routes**

```text
/contractors/palantir
/contractors/booz-allen
/contractors/leidos

/agencies/dod/contracts-expiring
/agencies/nasa/contracts-expiring

/naics/541512/upcoming-contracts

/government-contracts/california
/government-contracts/virginia
```

**Free tier**

- Contractor lookup
- Agency lookup
- Recent awards
- Basic filters
- Limited expiring-contract results
- Public charts and summary pages

**Paid tier**

- Watchlists
- Recompete alerts
- Saved searches
- Keyword alerts
- CSV export
- Bulk screening
- Team accounts
- API / Slack alerts

**Potential pricing**

```text
Free
$49/mo   Solo / small contractor
$99/mo   Pro
$299/mo  Team / bulk monitoring
$500+    API / enterprise
```

---

### Option B — FDA Supplier Risk Monitor

**Positioning**

> Check whether a supplier has FDA import-alert, recall, warning, or enforcement history before you buy from them.

**Target industries**

- Food
- Supplements
- Medical devices
- Cosmetics
- Pharmaceuticals
- Importers / distributors
- Sourcing and compliance teams

**Core user flow**

```text
Search supplier / manufacturer
    ↓
Risk profile page
    ↓
Import alerts / recalls / enforcement history
    ↓
Click "Monitor supplier"
    ↓
Receive alerts on status changes
    ↓
Subscription
```

**Example SEO routes**

```text
/fda-import-alert/china
/fda-import-alert/india

/company/shenzhen-xyz
/company/guangzhou-abc

/fda-import-alert/seafood
/fda-import-alert/dietary-supplements
/fda-import-alert/cosmetics

/fda-warning-letters/{company}
/fda-recalls/{company}
```

**Free tier**

- Public supplier lookup
- Basic regulatory history
- Limited recent events

**Paid tier**

- Supplier watchlists
- Email alerts
- Bulk supplier screening
- CSV import
- API
- Team accounts
- Risk scoring / benchmarking

**Potential pricing**

```text
Free       5 lookups
$29/mo     25 monitored suppliers
$99/mo     250 monitored suppliers
$299/mo    Bulk / API / team
```

---

### Option C — Employer Compliance / OSHA Intelligence

**Positioning**

> Screen companies and contractors for safety and labor-compliance risk.

**Core output**

Example company profile:

```text
Company: ABC Roofing LLC

OSHA inspections        14
Serious violations       7
Repeat violations        2
Total penalties       $184K
Last violation        47 days ago

Industry percentile:
Worse than 82% of roofing contractors
```

**Potential customers**

- General contractors
- Insurance brokers
- Commercial lenders
- Procurement teams
- Property managers
- Private equity
- Supplier-risk teams

**Example SEO routes**

```text
/company/{company}/osha
/company/{company}/labor-violations
/state/california/osha
/industry/roofing/osha
/industry/construction/safety-violations
```

**Premium feature**

Upload a vendor list and screen all vendors at once.

---

## 4. SEO Strategy

The SEO strategy should emphasize **structured, useful, entity-specific pages**, not generic AI-written articles.

### Page types

#### Entity pages
Examples:

```text
/company/{company}
/contractor/{contractor}
/agency/{agency}
/supplier/{supplier}
/device/{device}
/trial/{trial}
```

#### Cross-dimensional pages

```text
/company/{company}/{agency}
/agency/{agency}/{industry}
/state/{state}/{category}
/country/{country}/{risk-type}
```

#### Ranking pages

These are important for discovery and backlinks.

Examples:

```text
/top-ai-government-contractors
/top-nasa-contractors
/fastest-growing-defense-contractors
/top-osha-violators-by-industry
/fda-import-alerts-by-country
/most-recalled-medical-device-companies
```

#### Time-sensitive pages

```text
/contracts-expiring/2027
/fda-recalls/2026/october
/clinical-trial-updates/2026/october
```

### SEO principles

- Target long-tail commercial or research intent.
- Avoid generating thin pages.
- Every indexed page should contain genuinely differentiated structured data.
- Create internal-linking clusters around entities, categories, and rankings.
- Add useful charts, trend views, comparisons, and change history.
- Use sitemap segmentation by page type.
- Avoid indexing empty or near-duplicate pages.
- Use canonical URLs and structured metadata.

---

## 5. Monetization Strategy

Use both ads and subscriptions.

### Funnel

```text
Google
   ↓
Free SEO landing page
   ↓
Useful structured data
   ↓
Ads for anonymous traffic
   ↓
Watch / Alert / Save button
   ↓
Account creation
   ↓
Subscription
```

### Ads

Best for high-volume informational traffic.

Possible networks:

- AdSense initially
- Premium ad network later when traffic is high enough

### Subscription

Subscription should pay for **ongoing intelligence**, not merely access to raw data.

Good paid triggers:

- New event appears
- Status changes
- Contract approaches expiration
- Supplier gets new FDA action
- Employer gets a new violation
- Trial date or endpoint changes
- Company wins a new contract
- Search result matches saved criteria

### Higher-priced B2B features

- Bulk upload
- Team workspaces
- Data export
- API access
- Slack/email/webhook integration
- Saved filters
- Historical trend analysis
- Custom alerts

---

## 6. Product Moat

The API itself is not the moat.

Potential moats:

1. **Normalized data**
   - Clean entity names
   - Deduplicate companies
   - Resolve aliases
   - Map subsidiaries / parent companies

2. **Derived metrics**
   - Growth
   - Risk scores
   - Expiration / recompete likelihood
   - Industry percentiles
   - Trend detection
   - Change detection

3. **Historical snapshots**
   - Store API state over time
   - Detect records changing

4. **Entity graph**
   - Company ↔ agency
   - Supplier ↔ country ↔ product
   - Contractor ↔ NAICS ↔ state
   - Trial ↔ sponsor ↔ drug ↔ indication

5. **Alerts**
   - The recurring alerting layer creates retention.

6. **SEO authority**
   - Indexed historical pages and backlinks become an acquisition moat.

---

## 7. MVP Architecture

Recommended initial stack:

```text
Public API / Government Dataset
          ↓
Python ETL / scheduled jobs
          ↓
PostgreSQL
          ↓
Derived metrics / enrichment
          ↓
Next.js
          ↓
Cloudflare
```

Supporting services:

```text
PostgreSQL
Redis (optional at first)
Next.js
Python ETL
Stripe
Resend / Postmark
Cloudflare
```

### Suggested components

#### Ingestion

- Scheduled pulls from source APIs.
- Rate-limit aware.
- Persist raw responses for debugging.
- Normalize into internal schema.

#### Database

Core tables may include:

```text
entities
entity_aliases
events
source_records
categories
locations
relationships
snapshots
watchlists
alerts
users
subscriptions
```

#### Change detection

On each ingest:

```text
fetch latest
    ↓
normalize
    ↓
compare to previous snapshot
    ↓
detect meaningful change
    ↓
save event
    ↓
trigger alert
```

#### Frontend

- Server-side / static rendered pages for SEO.
- Search interface.
- Entity pages.
- Filters and rankings.
- Authenticated watchlists/dashboard.

---

## 8. Recommended MVP Scope

Do not launch with multiple datasets.

Choose one vertical and prove:

1. Google can index and rank the pages.
2. Users click into entity pages.
3. Users create alerts/watchlists.
4. Users are willing to pay.

### Suggested MVP for Government Recompete Radar

Build only:

```text
Contractor pages
Agency pages
Recent awards
Contract end dates
Expiring-contract filters
Watchlists
Email alerts
```

Skip initially:

- AI assistant
- Slack
- Complex dashboards
- Full enterprise permissions
- Advanced ML scoring
- Mobile app

### Suggested MVP for FDA Supplier Risk

Build only:

```text
Supplier search
Supplier pages
Import-alert history
Recall / enforcement history
Watch supplier
Email alerts
```

Then add bulk supplier upload after early demand is proven.

---

## 9. AI / ML Usage

AI is **not required for the MVP**.

Use deterministic structured data first.

Later AI features can include:

### Government contracts

- Explain why a contractor's awards are rising.
- Summarize major recent wins.
- Categorize contract descriptions.
- Cluster similar contract opportunities.

### FDA

- Summarize enforcement history.
- Normalize supplier names.
- Classify product categories.
- Explain changes in regulatory status.

### OSHA / compliance

- Summarize violation patterns.
- Extract risk themes.
- Normalize employer aliases.

Important principle:

> AI should summarize or enrich authoritative source data, not replace it.

---

## 10. Key Success Metrics

### SEO

- Indexed pages
- Search impressions
- Organic clicks
- Click-through rate
- Pages receiving impressions
- Top 10 / Top 3 keywords
- Backlinks
- Organic sessions per indexed page

### Product

- Search → entity-page conversion
- Entity page → signup conversion
- Signup → watchlist conversion
- Alert open rate
- Weekly returning users

### Revenue

- Free → paid conversion
- MRR
- ARPU
- Churn
- CAC from organic traffic
- Revenue per 1,000 organic visitors

---

## 11. Validation Plan Before Heavy Development

For each candidate niche:

1. Generate ~100 realistic long-tail queries.
2. Search Google and inspect SERPs.
3. Identify whether results are:
   - official government pages
   - weak directories
   - SEO farms
   - strong SaaS competitors
4. Estimate how many unique high-quality pages the dataset can support.
5. Check whether data changes often enough to justify alerts.
6. Identify a user who can economically justify paying $20–500/month.
7. Build 20–100 static prototype pages.
8. Submit sitemap and observe indexing/impressions.
9. Add signup/watch buttons.
10. Only then invest in a full SaaS workflow.

---

## 12. Current Recommendation

### Best long-term business

**Government Contract Recompete Radar**

Why:

- High commercial value.
- Recurring data.
- Natural alerts.
- Large SEO surface.
- B2B customers can support relatively high subscription prices.
- Many possible expansion paths.

### Best small-niche starting point

**FDA Supplier Risk Monitor**

Why:

- More focused.
- Likely lower SEO competition.
- High pain point for affected users.
- Clear recurring monitoring use case.
- Relatively simple initial product.

### Strong alternative

**Employer Compliance / OSHA Intelligence**

Especially attractive if the product focuses on B2B vendor screening rather than a generic OSHA lookup.

---

## 13. Immediate Next Decision

Select one of:

```text
A. Government Contract Recompete Radar
B. FDA Supplier Risk Monitor
C. Employer Compliance / OSHA Intelligence
```

Then complete:

1. Source/API audit.
2. Competitor list.
3. 100 target SEO keywords.
4. URL/site architecture.
5. Database schema.
6. MVP screen wireframes.
7. Pricing experiment.
8. 2–4 week implementation plan.

