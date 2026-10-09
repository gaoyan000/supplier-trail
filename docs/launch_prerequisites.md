# Launch Prerequisites — SupplierTrail (FDA Supplier Risk Monitor)

Everything to set up **before** development starts, in order. Companion to `design_fda_supplier_risk.md`.

Legend: ⭐ = easy to forget · ⏳ = has a waiting period, start early

---

## Order of work

```text
A1 Name ─→ A2 LLC + EIN ─→ B1–B6 Accounts (~1 hour once name is set) ─→ D Local setup ─→ E Pre-launch
                    └──────→ C1 FDA API keys ⏳ (start in parallel)
```

| # | Item | Owner | Time | Status |
|---|---|---|---|---|
| A1 | Brand name | You | 1–2 days | ✅ SupplierTrail |
| A2 | LLC, EIN, bank | You | 1–14 days ⏳ | ☐ |
| A3 | Password manager + 2FA | You | 30 min | ☐ |
| B1 | Domain | You | 15 min | ✅ suppliertrail.com |
| B2 | Hosting (Cloudflare) | You | 30 min | ☐ |
| B3 | Database (Neon) | You | 15 min | ☐ |
| B4 | GitHub org + repo | You / Claude | 15 min | ☐ |
| B5 | Business email + sending | You | 1 hour | ☐ |
| B6 | Stripe | You | 1 hour (+ verification ⏳) | ☐ |
| C1 | FDA data access | You | 1 hour (+ approval ⏳) | ☐ |
| D1 | Local project setup | Claude | 1 day | ☐ |
| E1 | Legal pages | You | half a day | ☐ |
| E2 | SEO + analytics | You / Claude | 1 hour | ☐ |
| E3 | Monitoring + backups | Claude | 2 hours | ☐ |
| E4 | Go-to-market basics | You | ongoing | ☐ |

---

## Phase A — Business and identity

### A1. ⭐ Brand name
**Why:** the domain, GitHub org, Stripe account and email all depend on it.

- Do **not** put "FDA" in the name or domain. It can look like an official government site, which hurts trust and invites complaints.
- Starting ideas (availability unchecked): `SupplierLedger`, `ImportClear`, `FSVPCheck`, `RedListWatch`, `SourceVerify`.

**Actions**
- [ ] Shortlist 5 names.
- [ ] Check `.com` availability (Cloudflare Registrar or Namecheap).
- [ ] Search the USPTO trademark database for conflicts: <https://tmsearch.uspto.gov>
- [ ] Check X and LinkedIn handle availability.
- [x] **Chosen: SupplierTrail** — domain `suppliertrail.com` bought 2026-10-09
- [x] USPTO screen 2026-10-09: **SUPPLIERTRAIL — no marks (live or dead)**. SUPPLIERTRAK (CyberMetrics) is **dead/cancelled 2017**. Note for the lawyer review: live **TRAIL** marks in class 9/35/42 (Trail Systems Oy, equipment/storage management software; Newpoint Advisors, asset/fiduciary database software). Assessed low risk (different goods and buyers, compound mark). Always write it as one word: "SupplierTrail". Consider filing class 42 after launch (~$350/class).

### A2. ⭐ ⏳ LLC + EIN + business bank account
**Why:** the site publishes negative facts about named companies, and an LLC keeps a lawsuit away from your personal assets. Stripe and the bank also want a business identity.

**Actions**
- [ ] Form an LLC in your home state, or Wyoming/Delaware. You can use a filing service (Stripe Atlas, Northwest Registered Agent, LegalZoom). Cost ~$100–500.
- [ ] Get an EIN (free, ~10 minutes online): <https://www.irs.gov/ein>
- [ ] Open a business bank account (Mercury or Relay, both free).
- [ ] **Bind media / E&O liability insurance before public launch** (~$500–1,500/yr). The site names companies in connection with FDA actions, so this must be in place before any page is public (see design §10).

### A3. ⭐ Password manager + 2FA
**Actions**
- [ ] Create a 1Password or Bitwarden vault. Every credential in this doc goes there.
- [ ] Turn on 2FA for GitHub, Cloudflare, Stripe, the domain registrar and the bank.

---

## Phase B — Infrastructure accounts

### B1. Domain: Cloudflare Registrar
**Why:** at-cost pricing (~$10/yr for `.com`), no upsells, and DNS is already in the same place.

**Actions**
- [ ] Create a Cloudflare account.
- [x] Bought `suppliertrail.com` (2026-10-09).
- [ ] Turn on auto-renew and confirm WHOIS privacy is on.
- [ ] Optional: buy `.io` / `.co` as defensive registrations.

### B2. Hosting: Cloudflare Workers (recommended) or Vercel

| | Cloudflare Workers + OpenNext | Vercel Pro |
|---|---|---|
| Cost | $5/mo | $20/mo (the free Hobby plan **forbids commercial use**) |
| 100K+ SEO pages (ISR: pages regenerated on a schedule) | Works, with the cache stored in R2 | Easiest; ISR is native |
| Same vendor as domain/DNS/storage | ✅ | ❌ |

**Decision:** Cloudflare. If Next.js on Workers causes friction in week 2, switch to Vercel; it's about an hour's work.

**Actions**
- [ ] Upgrade to Workers Paid ($5/mo).
- [ ] Create an R2 bucket `raw-snapshots` (for the raw FDA data we save).
- [ ] Create an API token with Workers + R2 edit permissions for deploys, and save it in the vault.

### B3. Database: Neon Postgres
**Actions**
- [ ] Create a Neon project in a US region (`us-east`).
- [ ] Create a `main` branch and a `dev` branch.
- [ ] Save both connection strings in the vault.
- [ ] Free tier at the start; plan for ~$19/mo once traffic arrives.

### B4. GitHub: version control + scheduled ETL
**Actions**
- [ ] Create a GitHub **organization** named after the brand. Keeping it separate from your personal account makes the project easy to sell or hand over later.
- [ ] Create a **private** repo `suppliertrail/app`.
- [ ] Add branch protection on `main` (require a PR and passing CI).
- [ ] Add repo secrets: `DATABASE_URL`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `OPENFDA_API_KEY`, `FDA_DASHBOARD_API_KEY`, `RESEND_API_KEY`, `STRIPE_SECRET_KEY`.
- [ ] The scheduled FDA data pull (ETL) runs as a GitHub Actions cron job. That's free for private repos up to 2,000 min/mo.

### B5. ⭐ Business email
**Actions**
- [ ] **Receiving:** use Cloudflare Email Routing (free) to forward `hello@`, `support@` and `corrections@` to your Gmail. Or get Google Workspace ($7/mo) for a real inbox.
- [ ] **Sending alerts:** create a Resend account and verify the domain.
- [ ] Send from a subdomain such as `alerts.suppliertrail.com`, so the main domain's sender reputation stays clean.
- [ ] Add the SPF, DKIM and DMARC records in Cloudflare DNS (Resend gives you the values). Without these, alert emails land in spam.
- [ ] Send a test email to Gmail and Outlook and confirm it reaches the inbox.

### B6. ⭐ ⏳ Payments: Stripe
**Actions**
- [ ] Create a Stripe account with the LLC's details and EIN, and connect the business bank account.
- [ ] Create the products:
  - Starter: $29/mo
  - Pro: $99/mo
  - FSVP supplier evaluation report: $19 one-time
- [ ] Turn on Stripe Tax (SaaS is taxable in some US states).
- [ ] Set up the Customer Portal (cancel, upgrade, invoices).
- [ ] Stay in **test mode** until launch.

---

## Phase C — Data access

### C1. ⭐ ⏳ FDA data access
**Actions**
- [ ] Get an openFDA API key (free; raises rate limits): <https://open.fda.gov/apis/authentication/>
- [ ] Register for the FDA Data Dashboard API (needs an account and approval can take days, so start early): <https://datadashboard.fda.gov>
- [ ] Download one sample from each source in §2 of the design doc:
  - Import Alerts (red/green lists)
  - Import Refusal Report
  - Data Dashboard: inspections and compliance actions
  - openFDA food enforcement (recalls)
  - Warning letters
- [ ] For each sample, record the fields available and **whether the FEI number is present**.
- [ ] Read FDA's website terms. FDA data is public domain, but don't use FDA logos or imply you're endorsed by FDA.

---

## Phase D — Local development setup (Claude can do this)

### D1. Project folder + tooling
```text
~/projects/suppliertrail/
├── docs/               ← handoff + design + this file
├── etl/                ← Python 3.12, uv
├── web/                ← Next.js, Node 22, pnpm
├── db/migrations/
├── .github/workflows/
├── .env.example
└── .gitignore
```

**Actions**
- [ ] Install the tools: `uv`, Node 22, `pnpm`, `gh`, `wrangler`, and Docker or Postgres.app.
- [ ] Create the folder structure above.
- [ ] Move `public_api_seo_saas_handoff.md`, `design_fda_supplier_risk.md` and `launch_prerequisites.md` into `docs/`.
- [ ] Add a `.gitignore` (`.env`, `node_modules`, `.venv`, `__pycache__`, `.wrangler`, `.next`).
- [ ] Add a `.env.example` with every variable name from B4 and **no values**.
- [ ] `git init`, make the first commit, and push to `suppliertrail/app`.

---

## Phase E — Pre-launch setup

### E1. ⭐ Legal pages
**Actions**
- [ ] **Terms of Service:** data provided as-is from public FDA sources; not legal advice; limitation of liability.
- [ ] **Privacy Policy.**
- [ ] **Data & Corrections Policy:** a `corrections@` address and a 48-hour response promise.
- [ ] **FSVP disclaimer** on reports and pricing: "The importer is responsible for its own supplier evaluation."
- [ ] ToS must include: as-is data from public FDA sources, no warranty, liability capped at fees paid, the user verifies with FDA, and governing law in a state with a strong anti-SLAPP statute (design §10, Rule 5).
- [ ] **One-hour review by a media / First Amendment lawyer** (also ask about the live TRAIL marks, see A1) (~$300–1,000) covering page templates, title wording, the banned-words list, the ToS and the corrections policy. **Required before launch.**
- Termly or Iubenda can generate the ToS and Privacy Policy (~$10/mo). Write the Corrections Policy and FSVP disclaimer yourself.

### E2. ⭐ SEO + analytics
**Actions**
- [ ] **Google Search Console:** verify the domain with a DNS TXT record in Cloudflare.
- [ ] **Bing Webmaster Tools:** import the site from Search Console. Bing also feeds ChatGPT search and DuckDuckGo.
- [ ] **Analytics:** turn on Cloudflare Web Analytics (free, cookieless) or Plausible ($9/mo).
- [ ] **Product funnel:** PostHog free tier. Track page view → watch click → signup → paid.

### E3. ⭐ Monitoring + backups
**Actions**
- [ ] **Sentry** (free) for errors in both the website and the ETL.
- [ ] **UptimeRobot or Better Stack** (free):
  - a homepage check
  - a heartbeat check that fires if the daily ETL hasn't run
- [ ] **Backups:** Neon point-in-time restore (on by default), plus a weekly `pg_dump` to R2 via GitHub Actions.

### E4. ⭐ Go-to-market basics
**Actions**
- [ ] Create a LinkedIn company page and an X account.
- [ ] Find 3–5 places to post: Amazon seller forums, r/FulfillmentByAmazon, food-importer LinkedIn groups.
- [ ] Build a list of 20 FSVP importers to contact for the 5 interviews (design doc §8, Week 0, task 5).
- [ ] Line up 2–3 FDA compliance consultants as lead-gen partners.

---

## Estimated cost

**One-time**

| Item | Cost |
|---|---|
| LLC formation | $100–500 |
| Domain (first year) | ~$10 |
| Lawyer review (pre-launch) | $300–1,000 |
| Media / E&O insurance (first year, pre-launch) | $500–1,500 |

**Monthly at launch**

| Item | Cost |
|---|---|
| Cloudflare Workers Paid | $5 |
| Neon, GitHub, Resend, Sentry, PostHog, Search Console | $0 (free tiers) |
| Google Workspace (optional) | $0–7 |
| Legal page generator (optional) | $0–10 |
| **Total** | **≈ $6–25/mo** |

**Later (with traction):** Neon Launch $19, Resend Pro $20.

> Prices are typical-cost estimates and haven't been checked against the providers' current pricing.
