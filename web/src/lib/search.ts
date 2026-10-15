/** Free lookup by firm name or FEI number. Only firms FDA identifies by FEI are searchable. */
import type { Sql } from "postgres";

import { normalizeName } from "./normalize";

export const SEARCH_LIMIT = 25;
const MIN_NAME_LENGTH = 3;
const MAX_NAME_LENGTH = 100;
const FEI_QUERY = /^(?:fei\b[\s:#]*)?(\d{3,12})$/i;

export type ParsedQuery =
  | { kind: "empty" }
  | { kind: "short" }
  | { kind: "fei"; fei: string }
  | { kind: "name"; norm: string };

export function parseQuery(q: string | undefined): ParsedQuery {
  const text = (q ?? "").trim();
  if (!text) return { kind: "empty" };
  const fei = FEI_QUERY.exec(text);
  if (fei) return { kind: "fei", fei: fei[1] };
  const norm = normalizeName(text).slice(0, MAX_NAME_LENGTH).trim();
  return norm.length < MIN_NAME_LENGTH ? { kind: "short" } : { kind: "name", norm };
}

export type FirmHit = {
  fei: string;
  slug: string;
  name: string;
  address: string | null;
  city: string | null;
  country: string | null;
};

/** `norm` must come from normalizeName, so it holds only [a-z0-9 ] and is safe inside LIKE. */
export async function searchFirms(sql: Sql, norm: string): Promise<FirmHit[]> {
  const rows = await sql<FirmHit[]>`
    SELECT fei, slug, canonical_name AS name, address, city, country
    FROM firms
    WHERE fei IS NOT NULL AND (norm_name LIKE ${`%${norm}%`} OR ${norm} <% norm_name)
    ORDER BY (norm_name = ${norm}) DESC, (norm_name LIKE ${`${norm}%`}) DESC,
             word_similarity(${norm}, norm_name) DESC, last_event_at DESC NULLS LAST, id
    LIMIT ${SEARCH_LIMIT}`;
  return [...rows];
}
