/** Mirrors normalize_name in etl/src/supplier_trail_etl/normalize.py; firms.norm_name is stored in this form. */
export function normalizeName(name: string): string {
  return name
    .normalize("NFKD")
    .replace(/[^\x00-\x7f]/g, "")
    .toLowerCase()
    .replaceAll("&", " and ")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}
