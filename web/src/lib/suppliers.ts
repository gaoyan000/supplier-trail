/** Read-only queries behind the supplier page. Quarantined events never leave the database. */
import type { Sql } from "postgres";

import type { EventRow, FilterKey } from "./events";

export const PAGE_SIZE = 50;

export type Firm = {
  id: number;
  fei: string;
  slug: string;
  name: string;
  address: string | null;
  city: string | null;
  country: string | null;
  indexable: boolean;
};

export type ActiveAlert = { number: string; title: string; datePublished: string | null };

export type SupplierSummary = {
  /** Only red-list entries whose link to this firm is verified (design §10 Rule 1). */
  activeAlerts: ActiveAlert[];
  refusals5y: number;
  warningLetters: number;
  lastActionOn: string | null;
  counts: Record<FilterKey, number>;
  refusalsByYear: { year: number; n: number }[];
};

export async function getFirmByFei(sql: Sql, fei: string): Promise<Firm | null> {
  const rows = await sql<Firm[]>`
    SELECT id::int AS id, fei, slug, canonical_name AS name, address, city, country, indexable
    FROM firms WHERE fei = ${fei}`;
  return rows[0] ?? null;
}

export async function getSummary(sql: Sql, firmId: number, today: string): Promise<SupplierSummary> {
  const [[totals], refusalsByYear, activeAlerts] = await Promise.all([
    sql`
      SELECT count(*) FILTER (WHERE type = 'refusal' AND occurred_on >= ${today}::date - interval '5 years')::int
               AS refusals_5y,
             count(*) FILTER (WHERE type = 'warning_letter')::int AS warning_letters,
             max(occurred_on)::text AS last_action_on,
             count(*)::int AS "all",
             count(*) FILTER (WHERE type IN ('alert_listed', 'alert_removed'))::int AS alerts,
             count(*) FILTER (WHERE type = 'refusal')::int AS refusals,
             count(*) FILTER (WHERE type LIKE 'inspection\_%')::int AS inspections,
             count(*) FILTER (WHERE type = 'recall')::int AS recalls,
             count(*) FILTER (WHERE type IN ('warning_letter', 'compliance_action'))::int AS actions
      FROM events WHERE firm_id = ${firmId} AND NOT quarantined`,
    sql<{ year: number; n: number }[]>`
      SELECT y::int AS year, count(e.id)::int AS n
      FROM generate_series(extract(year FROM ${today}::date)::int - 4, extract(year FROM ${today}::date)::int) y
      LEFT JOIN events e ON e.firm_id = ${firmId} AND e.type = 'refusal' AND NOT e.quarantined
                        AND extract(year FROM e.occurred_on) = y
      GROUP BY y ORDER BY y`,
    sql<ActiveAlert[]>`
      SELECT r.alert_number AS number, a.title, r.date_published::text AS "datePublished"
      FROM red_list_entries r JOIN import_alerts a ON a.number = r.alert_number
      WHERE r.firm_id = ${firmId} AND r.active
      ORDER BY r.date_published DESC NULLS LAST, r.alert_number`,
  ]);
  return {
    activeAlerts: [...activeAlerts],
    refusals5y: totals.refusals_5y,
    warningLetters: totals.warning_letters,
    lastActionOn: totals.last_action_on,
    counts: {
      all: totals.all,
      alerts: totals.alerts,
      refusals: totals.refusals,
      inspections: totals.inspections,
      recalls: totals.recalls,
      actions: totals.actions,
    },
    refusalsByYear: [...refusalsByYear],
  };
}

export async function getEvents(
  sql: Sql,
  firmId: number,
  types: readonly string[] | null,
  page: number,
): Promise<EventRow[]> {
  const rows = await sql<EventRow[]>`
    SELECT id::int AS id, type, occurred_on::text AS "occurredOn", summary, details, NULLIF(source_url, '') AS "sourceUrl"
    FROM events
    WHERE firm_id = ${firmId} AND NOT quarantined ${types ? sql`AND type IN ${sql(types)}` : sql``}
    ORDER BY occurred_on DESC, id DESC
    LIMIT ${PAGE_SIZE} OFFSET ${(page - 1) * PAGE_SIZE}`;
  return [...rows];
}

/** Date of the last successful FDA fetch, shown as "Per FDA, as of …". */
export async function getDataAsOf(sql: Sql): Promise<string | null> {
  const [row] = await sql`SELECT max(finished_at)::date::text AS as_of FROM ingest_runs WHERE status = 'ok'`;
  return row.as_of;
}
