import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import postgres from "postgres";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { normalizeName } from "./normalize";
import { parseQuery, SEARCH_LIMIT, searchFirms } from "./search";

describe("parseQuery", () => {
  it.each([
    ["3000000000", { kind: "fei", fei: "3000000000" }],
    [" FEI 3000000000 ", { kind: "fei", fei: "3000000000" }],
    ["fei: 3000000000", { kind: "fei", fei: "3000000000" }],
    ["Example Foods Co., Ltd", { kind: "name", norm: "example foods co ltd" }],
    ["7 Seas Foods", { kind: "name", norm: "7 seas foods" }],
    ["ab", { kind: "short" }],
    ["12", { kind: "short" }],
    ["  ", { kind: "empty" }],
    [undefined, { kind: "empty" }],
  ])("%j", (q, expected) => {
    expect(parseQuery(q)).toEqual(expected);
  });

  it("caps very long input", () => {
    const parsed = parseQuery("x".repeat(500));
    expect(parsed.kind === "name" && parsed.norm.length).toBe(100);
  });
});

const url = process.env.TEST_DATABASE_URL;
const MIGRATIONS = path.resolve(__dirname, "../../../db/migrations");

describe.skipIf(!url)("searchFirms", () => {
  const sql = postgres(url!, { onnotice: () => {} });

  // Fictional firms only (design §10).
  async function firm(fei: string | null, name: string, lastEventAt: string | null = null) {
    await sql`INSERT INTO firms ${sql({
      fei,
      identity_key: fei ? `fei:${fei}` : `name:${name}`,
      canonical_name: name,
      norm_name: normalizeName(name),
      slug: normalizeName(name).replaceAll(" ", "-"),
      city: "Example City",
      country: "China",
      last_event_at: lastEventAt,
    })}`;
  }

  beforeAll(async () => {
    await sql.unsafe("DROP SCHEMA public CASCADE; CREATE SCHEMA public;");
    for (const file of readdirSync(MIGRATIONS).sort()) {
      await sql.unsafe(readFileSync(path.join(MIGRATIONS, file), "utf8"));
    }
    await firm("3000000001", "Example Foods Co., Ltd", "2026-01-01");
    await firm("3000000002", "Example Foods Trading (Shanghai) Co Ltd", "2026-09-01");
    await firm("3000000003", "Great Example Foods Inc", "2026-09-30");
    await firm("3000000004", "EXAMPLE FOODS CO LTD", "2026-06-01");
    await firm("3000000005", "Sample Spice Exports");
    await firm(null, "Example Foods Without Fei");
    for (let i = 0; i < SEARCH_LIMIT + 5; i++) await firm(`31000000${String(i).padStart(2, "0")}`, `Demo Seafood ${i} JSC`);
  });

  afterAll(() => sql.end());

  const names = async (q: string) => (await searchFirms(sql, normalizeName(q))).map((f) => f.fei);

  it("ranks exact names first (most recent FDA action first), then prefixes, then partial matches", async () => {
    expect((await names("example foods co ltd")).slice(0, 2)).toEqual(["3000000004", "3000000001"]);
    expect(await names("Example Foods")).toEqual(["3000000002", "3000000004", "3000000001", "3000000003"]);
  });

  it("matches part of a name and tolerates small spelling differences", async () => {
    expect(await names("spice")).toEqual(["3000000005"]);
    expect(await names("sample spise exports")).toEqual(["3000000005"]);
  });

  it("returns only firms that have an FEI, with what the result list shows", async () => {
    const hits = await searchFirms(sql, "example foods without fei");
    expect(hits.every((f) => f.fei)).toBe(true);
    expect((await searchFirms(sql, "sample spice exports"))[0]).toEqual({
      fei: "3000000005",
      slug: "sample-spice-exports",
      name: "Sample Spice Exports",
      address: null,
      city: "Example City",
      country: "China",
    });
  });

  it("caps the list and finds nothing for an unknown name", async () => {
    expect(await names("demo seafood")).toHaveLength(SEARCH_LIMIT);
    expect(await names("zzzz qqqq")).toEqual([]);
  });
});
