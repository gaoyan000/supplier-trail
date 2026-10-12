import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { EventRow } from "@/lib/events";
import type { Firm, SupplierSummary } from "@/lib/suppliers";

import { SupplierRecord } from "./supplier-record";

// Fictional firm: tests and mockups never use real firms (design §10).
const firm: Firm = {
  id: 1,
  fei: "3000000000",
  slug: "example-foods-co-ltd",
  name: "Example Foods Co., Ltd",
  address: "No. 1 Sample Road",
  city: "Example City",
  country: "China",
  indexable: true,
};

const summary: SupplierSummary = {
  activeAlerts: [],
  refusals5y: 2,
  warningLetters: 1,
  lastActionOn: "2026-09-30",
  counts: { all: 3, alerts: 0, refusals: 2, inspections: 0, recalls: 0, actions: 1 },
  refusalsByYear: [
    { year: 2022, n: 0 },
    { year: 2023, n: 0 },
    { year: 2024, n: 0 },
    { year: 2025, n: 1 },
    { year: 2026, n: 1 },
  ],
};

const events: EventRow[] = [
  {
    id: 3,
    type: "refusal",
    occurredOn: "2026-09-30",
    summary: "Shipment refused · FDA charge codes: 2580 · Product: SAMPLE DRIED MUSHROOMS",
    details: { ShipmentID: "AAA-0000001-1/1/1", ProductCode: "25JGT05" },
    sourceUrl: "https://datadashboard.fda.gov/oii/firmprofile.htm?FEIu=3000000000",
  },
  {
    id: 2,
    type: "warning_letter",
    occurredOn: "2025-03-01",
    summary: "FDA Warning Letter (CFSAN)",
    details: {},
    sourceUrl: "https://datadashboard.fda.gov/oii/firmprofile.htm?FEIc=3000000000",
  },
  {
    id: 1,
    type: "recall",
    occurredOn: "2025-01-10",
    summary: "Recall F-0000-2025 · Class 1 · Undeclared allergens (wheat)",
    details: {},
    sourceUrl: null,
  },
];

function render(overrides: Partial<Parameters<typeof SupplierRecord>[0]> = {}) {
  return renderToStaticMarkup(
    <SupplierRecord
      firm={firm}
      summary={summary}
      events={events}
      filter="all"
      page={1}
      asOf="2026-10-09"
      today="2026-10-09"
      {...overrides}
    />,
  );
}

describe("SupplierRecord", () => {
  it("identifies the firm and dates the data", () => {
    const html = render();
    expect(html.match(/<h1/g)).toHaveLength(1);
    expect(html).toContain("Example Foods Co., Ltd</h1>");
    expect(html).toContain("FEI 3000000000");
    expect(html).toContain("No. 1 Sample Road, Example City, China");
    expect(html).toMatch(/Per FDA, as of <[^>]+>2026-10-09/);
  });

  it("does not repeat the city when FDA's address already ends with it", () => {
    const html = render({ firm: { ...firm, address: "No. 1 Sample Road, Example City" } });
    expect(html).toContain("· No. 1 Sample Road, Example City, China<");
  });

  it("shows each event with its date, FDA wording and source link", () => {
    const html = render();
    for (const e of events) {
      expect(html).toContain(e.occurredOn);
      expect(html).toContain(e.summary.replace("&", "&amp;"));
    }
    expect(html).toContain('href="https://datadashboard.fda.gov/oii/firmprofile.htm?FEIu=3000000000"');
    expect(html.match(/FDA source/g)).toHaveLength(2);
    expect(html).toContain("Source: FDA Enforcement Reports");
  });

  it("states counts with their time window and the last action", () => {
    const html = render();
    expect(html).toContain("2 import refusals on record (5 years)");
    expect(html).toContain("1 warning letter on record");
    expect(html).toContain("9 days ago");
    expect(html).toContain('aria-label="Import refusals by year: 2022: 0, 2023: 0, 2024: 0, 2025: 1, 2026: 1."');
  });

  it("shows no import-alert status unless a verified alert link exists", () => {
    expect(render()).not.toContain("On FDA Import Alert");
    const listed = render({
      summary: { ...summary, activeAlerts: [{ number: "99-19", title: "Salmonella", datePublished: "2026-10-07" }] },
    });
    expect(listed).toContain("On FDA Import Alert 99-19 (red list), published 2026-10-07");
  });

  it("uses a neutral empty state, never a verdict", () => {
    const html = render({
      events: [],
      summary: {
        ...summary,
        refusals5y: 0,
        warningLetters: 0,
        lastActionOn: null,
        counts: { all: 0, alerts: 0, refusals: 0, inspections: 0, recalls: 0, actions: 0 },
      },
    });
    expect(html).toContain("No records found in the FDA sources we searched");
    expect(html).not.toMatch(/✓|No issues/);
  });

  it("filters and pages with plain links, so the record reads without JavaScript", () => {
    const html = render({ filter: "refusals", summary: { ...summary, counts: { ...summary.counts, refusals: 120 } } });
    expect(html).toContain('href="/supplier/3000000000-example-foods-co-ltd?type=refusals&amp;page=2#record"');
    expect(html).toContain('href="/supplier/3000000000-example-foods-co-ltd?type=actions#record"');
    expect(html).toMatch(/aria-current="true"[^>]*>Refusals/);
    expect(html).not.toContain("<script");
  });

  it("explains what the records mean in FDA's terms", () => {
    expect(render()).toContain("it is not a court finding against the firm");
  });
});
