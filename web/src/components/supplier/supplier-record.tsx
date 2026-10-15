import { ExternalLink, FileText, Flag, Info, Search } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { EVENT_FILTERS, eventView, type EventRow, type FilterKey } from "@/lib/events";
import { firmPlace, relativeDays, supplierPath } from "@/lib/format";
import { PAGE_SIZE, type Firm, type SupplierSummary } from "@/lib/suppliers";

type Props = {
  firm: Firm;
  summary: SupplierSummary;
  events: EventRow[];
  filter: FilterKey;
  page: number;
  asOf: string | null;
  today: string;
};

const CARD = "rounded-md border border-border bg-surface";
const CHIP = "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[15px]";
const CHIP_LISTED = `${CHIP} border-listed-border bg-listed-bg font-semibold text-listed-fg`;
const CHIP_RECORD = `${CHIP} border-border bg-record-bg text-record-fg`;
const MONO = "font-mono text-sm font-medium";

function count(n: number, noun: string): string {
  return `${n} ${noun}${n === 1 ? "" : "s"}`;
}

function recordHref(firm: Firm, filter: FilterKey, page: number): string {
  const query = [filter !== "all" && `type=${filter}`, page > 1 && `page=${page}`].filter(Boolean).join("&");
  return supplierPath(firm.fei, firm.slug) + (query ? `?${query}` : "");
}

function Tile({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className={`${CARD} px-5 py-4`}>
      <div className="text-sm text-ink-muted">{label}</div>
      {children}
    </div>
  );
}

function Count({ n }: { n: number }) {
  return <div className="font-heading text-3xl font-semibold tabular-nums">{n}</div>;
}

function StatusChips({ summary }: { summary: SupplierSummary }) {
  if (summary.counts.all === 0 && summary.activeAlerts.length === 0) {
    return (
      <span className={CHIP_RECORD}>
        <Search aria-hidden="true" size={16} />
        No records found in the FDA sources we searched
      </span>
    );
  }
  return (
    <>
      {summary.activeAlerts.map((alert) => (
        <span key={`${alert.number}-${alert.datePublished}`} className={CHIP_LISTED}>
          <Flag aria-hidden="true" size={16} />
          On FDA Import Alert {alert.number} (red list)
          {alert.datePublished ? `, published ${alert.datePublished}` : ""}
        </span>
      ))}
      {summary.refusals5y > 0 && (
        <span className={CHIP_RECORD}>
          <FileText aria-hidden="true" size={16} />
          {count(summary.refusals5y, "import refusal")} on record (5 years)
        </span>
      )}
      {summary.warningLetters > 0 && (
        <span className={CHIP_RECORD}>
          <FileText aria-hidden="true" size={16} />
          {count(summary.warningLetters, "warning letter")} on record
        </span>
      )}
    </>
  );
}

function EventItem({ event }: { event: EventRow }) {
  const view = eventView(event);
  return (
    <li className="flex flex-wrap gap-x-5 gap-y-2 border-b border-border px-4 py-4 last:border-b-0 sm:px-6">
      <div className={`${MONO} w-[110px] flex-none pt-0.5`}>{event.occurredOn}</div>
      <div className="flex min-w-0 flex-[1_1_360px] flex-col gap-0.5">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`${view.listed ? CHIP_LISTED : CHIP_RECORD} px-2.5 py-0.5 text-sm`}>{view.chip}</span>
          <span className="font-semibold">{view.title}</span>
        </div>
        {view.detail && <div className="text-[15px] text-ink-muted [overflow-wrap:anywhere]">{view.detail}</div>}
        {event.sourceUrl ? (
          <a href={event.sourceUrl} rel="noopener" className="inline-flex items-center gap-1 self-start text-sm">
            FDA source
            <ExternalLink aria-hidden="true" size={14} />
          </a>
        ) : (
          <span className="text-sm text-ink-muted">Source: FDA Enforcement Reports</span>
        )}
      </div>
    </li>
  );
}

function RefusalsByYear({ years }: { years: SupplierSummary["refusalsByYear"] }) {
  const max = Math.max(1, ...years.map((y) => y.n));
  const label = `Import refusals by year: ${years.map((y) => `${y.year}: ${y.n}`).join(", ")}.`;
  return (
    <section className={`${CARD} flex flex-col gap-3 px-6 py-5`}>
      <h2 className="font-heading text-lg font-semibold">Import refusals by year</h2>
      <div role="img" aria-label={label} className="flex h-[150px] items-end gap-3.5 border-b border-border-strong pt-2">
        {years.map((y) => (
          <div key={y.year} className="flex h-full flex-1 flex-col items-center justify-end gap-1">
            <span className="text-sm tabular-nums">{y.n}</span>
            <div className="w-full rounded-t-sm bg-accent" style={{ height: `${(y.n / max) * 80}%` }} />
          </div>
        ))}
      </div>
      <div aria-hidden="true" className="flex gap-3.5 font-mono text-[13px] text-ink-muted">
        {years.map((y) => (
          <span key={y.year} className="flex-1 text-center">
            {y.year}
          </span>
        ))}
      </div>
    </section>
  );
}

export function SupplierRecord({ firm, summary, events, filter, page, asOf, today }: Props) {
  const place = firmPlace(firm);
  const total = summary.counts[filter];
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const first = (page - 1) * PAGE_SIZE + 1;

  return (
    <>
      <nav aria-label="Breadcrumb" className="text-sm text-ink-muted">
        <Link href="/">Home</Link> › Suppliers{firm.country ? ` › ${firm.country}` : ""} ›{" "}
        <span aria-current="page">{firm.name}</span>
      </nav>

      <section className={`${CARD} flex flex-col gap-2.5 p-5 sm:p-7`}>
        <h1 className="font-heading text-2xl font-semibold leading-tight [overflow-wrap:anywhere] sm:text-[32px]">
          {firm.name}
        </h1>
        <p className="text-ink-muted">
          <span className="font-mono font-medium text-ink">FEI {firm.fei}</span>
          {place ? ` · ${place}` : ""}
        </p>
        <div className="mt-1 flex flex-wrap gap-2">
          <StatusChips summary={summary} />
        </div>
        <p className="mt-1 text-sm text-ink-muted">
          {asOf ? (
            <>
              Per FDA, as of <span className="font-mono">{asOf}</span>
            </>
          ) : (
            "Per FDA"
          )}{" "}
          · Sources: FDA Data Dashboard, Import Alerts, Enforcement Reports
        </p>
      </section>

      <section aria-label="Summary" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Tile label="Import alerts">
          <Count n={summary.activeAlerts.length} />
        </Tile>
        <Tile label="Import refusals (5 years)">
          <Count n={summary.refusals5y} />
        </Tile>
        <Tile label="Warning letters">
          <Count n={summary.warningLetters} />
        </Tile>
        <Tile label="Last FDA action">
          {summary.lastActionOn ? (
            <>
              <div className="mt-1.5 font-mono text-xl font-medium">{summary.lastActionOn}</div>
              <div className="text-sm text-ink-muted">{relativeDays(summary.lastActionOn, today)}</div>
            </>
          ) : (
            <div className="mt-1.5 text-ink-muted">None on record</div>
          )}
        </Tile>
      </section>

      <div className="flex flex-wrap items-start gap-6">
        <section id="record" className={`${CARD} min-w-0 flex-[999_1_600px]`}>
          <div className="flex flex-col gap-3 border-b border-border px-4 pb-3 pt-5 sm:px-6">
            <h2 className="font-heading text-[22px] font-semibold">FDA record</h2>
            <nav aria-label="Filter record" className="flex flex-wrap gap-2">
              {EVENT_FILTERS.map((f) => (
                <Link
                  key={f.key}
                  href={`${recordHref(firm, f.key, 1)}#record`}
                  aria-current={f.key === filter ? "true" : undefined}
                  className={`inline-flex min-h-11 items-center gap-1.5 rounded-md border px-3 text-base no-underline ${
                    f.key === filter
                      ? "border-accent bg-accent font-semibold text-accent-fg"
                      : "border-border-strong bg-surface text-ink"
                  }`}
                >
                  {f.label} <span className="tabular-nums opacity-80">{summary.counts[f.key]}</span>
                </Link>
              ))}
            </nav>
          </div>
          {events.length ? (
            <ol>
              {events.map((event) => (
                <EventItem key={event.id} event={event} />
              ))}
            </ol>
          ) : (
            <p className="px-4 py-6 text-ink-muted sm:px-6">
              No records of this type found in the FDA sources we searched{asOf ? ` as of ${asOf}` : ""}.
            </p>
          )}
          {pageCount > 1 && (
            <nav
              aria-label="Record pages"
              className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-4 py-3 text-sm sm:px-6"
            >
              <span className="text-ink-muted tabular-nums">
                Showing {first}–{first + events.length - 1} of {total}
              </span>
              <span className="flex gap-4">
                {page > 1 && <Link href={`${recordHref(firm, filter, page - 1)}#record`}>Newer</Link>}
                {page < pageCount && <Link href={`${recordHref(firm, filter, page + 1)}#record`}>Older</Link>}
              </span>
            </nav>
          )}
        </section>

        <aside className="flex flex-[1_1_300px] flex-col gap-4">
          <RefusalsByYear years={summary.refusalsByYear} />
          <section className="flex flex-col gap-2 rounded-md border border-border bg-record-bg px-6 py-5">
            <h2 className="flex items-center gap-2 text-base font-semibold">
              <Info aria-hidden="true" size={18} />
              What these records mean
            </h2>
            <p className="text-[15px] text-record-fg">
              An import refusal means FDA determined a shipment appeared to violate FDA requirements; it is not a court
              finding against the firm. An import alert red list lets FDA detain the firm&rsquo;s listed products
              without physical examination.
            </p>
          </section>
          <p className="text-sm text-ink-muted">
            Found an error? <a href="mailto:corrections@suppliertrail.com">Report it</a>. We review every report within
            48 hours.
          </p>
        </aside>
      </div>
    </>
  );
}
