import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import postgres from "postgres";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { getDataAsOf, getEvents, getFirmByFei, getSummary, PAGE_SIZE } from "./suppliers";

const url = process.env.TEST_DATABASE_URL;
const MIGRATIONS = path.resolve(__dirname, "../../../db/migrations");
const TODAY = "2026-10-09";

describe.skipIf(!url)("supplier queries", () => {
  const sql = postgres(url!, { onnotice: () => {} });
  let firmId: number;
  let hash = 0;

  async function event(type: string, occurredOn: string | null, extra: Record<string, unknown> = {}) {
    hash += 1;
    await sql`INSERT INTO events ${sql({
      firm_id: firmId,
      type,
      occurred_on: occurredOn,
      summary: `${type} ${hash}`,
      source: "test",
      source_record_hash: `h${hash}`,
      ...extra,
    })}`;
  }

  beforeAll(async () => {
    await sql.unsafe("DROP SCHEMA public CASCADE; CREATE SCHEMA public;");
    for (const file of readdirSync(MIGRATIONS).sort()) {
      await sql.unsafe(readFileSync(path.join(MIGRATIONS, file), "utf8"));
    }
    [{ id: firmId }] = await sql`
      INSERT INTO firms (fei, identity_key, canonical_name, norm_name, slug, city, country, indexable)
      VALUES ('3000000000', 'fei:3000000000', 'Example Foods Co., Ltd', 'example foods co ltd',
              'example-foods-co-ltd', 'Example City', 'China', true)
      RETURNING id::int AS id`;
    await sql`INSERT INTO import_alerts (number, title, page_url) VALUES ('99-19', 'Salmonella', 'https://fda.example/99-19')`;

    await event("refusal", "2026-09-30");
    await event("refusal", "2019-01-15"); // older than 5 years
    await event("refusal", "2026-10-01", { quarantined: true, quarantine_reason: "future_date" });
    await event("warning_letter", "2025-03-01");
    await event("inspection_nai", "2024-06-01");
    await event("recall", "2023-02-02");

    // An unverified red-list entry: no firm_id on the entry or its event (design §10 Rule 1).
    const [{ id: unverified }] = await sql`
      INSERT INTO red_list_entries (alert_number, entry_key, fda_name, slug, first_seen)
      VALUES ('99-19', 'k-unverified', 'EXAMPLE FOODS CO LTD', 'example-foods-co-ltd', ${TODAY}) RETURNING id`;
    await event("alert_listed", "2026-10-07", { firm_id: null, red_list_entry_id: unverified });

    await sql`INSERT INTO ingest_runs (source, status, finished_at) VALUES
      ('a', 'ok', '2026-10-08T12:00:00Z'), ('b', 'failed', '2026-10-09T12:00:00Z')`;
  });

  afterAll(() => sql.end());

  it("finds a firm by FEI and returns null for an unknown one", async () => {
    expect(await getFirmByFei(sql, "3000000000")).toMatchObject({
      id: firmId,
      fei: "3000000000",
      slug: "example-foods-co-ltd",
      name: "Example Foods Co., Ltd",
      indexable: true,
    });
    expect(await getFirmByFei(sql, "1")).toBeNull();
  });

  it("counts only this firm's non-quarantined events", async () => {
    const summary = await getSummary(sql, firmId, TODAY);
    expect(summary.refusals5y).toBe(1);
    expect(summary.warningLetters).toBe(1);
    expect(summary.lastActionOn).toBe("2026-09-30");
    expect(summary.counts).toEqual({ all: 5, alerts: 0, refusals: 2, inspections: 1, recalls: 1, actions: 1 });
    expect(summary.refusalsByYear).toEqual([
      { year: 2022, n: 0 },
      { year: 2023, n: 0 },
      { year: 2024, n: 0 },
      { year: 2025, n: 0 },
      { year: 2026, n: 1 },
    ]);
  });

  it("shows no import alert for an unverified red-list match", async () => {
    expect((await getSummary(sql, firmId, TODAY)).activeAlerts).toEqual([]);
    expect(await getEvents(sql, firmId, ["alert_listed", "alert_removed"], 1)).toEqual([]);
  });

  it("lists events newest first and filters by type", async () => {
    const all = await getEvents(sql, firmId, null, 1);
    expect(all.map((e) => e.occurredOn)).toEqual(["2026-09-30", "2025-03-01", "2024-06-01", "2023-02-02", "2019-01-15"]);
    expect((await getEvents(sql, firmId, ["refusal"], 1)).map((e) => e.type)).toEqual(["refusal", "refusal"]);
  });

  it("shows a verified import alert and its event", async () => {
    const [{ id: verified }] = await sql`
      INSERT INTO red_list_entries (alert_number, entry_key, fda_name, slug, first_seen, date_published, firm_id)
      VALUES ('99-19', 'k-verified', 'EXAMPLE FOODS CO LTD', 'example-foods-co-ltd', ${TODAY}, '2026-10-07', ${firmId})
      RETURNING id`;
    await event("alert_listed", "2026-10-07", { red_list_entry_id: verified, alert_number: "99-19" });

    const summary = await getSummary(sql, firmId, TODAY);
    expect(summary.activeAlerts).toEqual([{ number: "99-19", title: "Salmonella", datePublished: "2026-10-07" }]);
    expect(summary.counts.alerts).toBe(1);
    expect(summary.lastActionOn).toBe("2026-10-07");

    await sql`UPDATE red_list_entries SET active = false WHERE id = ${verified}`;
    expect((await getSummary(sql, firmId, TODAY)).activeAlerts).toEqual([]);
  });

  it("pages through long records", async () => {
    await sql`INSERT INTO events (firm_id, type, occurred_on, summary, source, source_record_hash)
      SELECT ${firmId}, 'inspection_vai', '2020-01-01', 'bulk', 'test', 'bulk' || n FROM generate_series(1, ${PAGE_SIZE}) n`;
    expect(await getEvents(sql, firmId, ["inspection_vai"], 1)).toHaveLength(PAGE_SIZE);
    expect(await getEvents(sql, firmId, ["inspection_vai"], 2)).toHaveLength(0);
    expect((await getEvents(sql, firmId, null, 2)).length).toBeGreaterThan(0);
  });

  it("reports the date of the last successful FDA fetch", async () => {
    expect(await getDataAsOf(sql)).toBe("2026-10-08");
  });
});
