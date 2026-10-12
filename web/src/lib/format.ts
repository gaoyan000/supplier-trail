const SUPPLIER_ID = /^(\d{1,12})(?:-(.*))?$/;
const DAY_MS = 86_400_000;

export function parseSupplierId(id: string): { fei: string; slug: string } | null {
  const match = SUPPLIER_ID.exec(id);
  return match ? { fei: match[1], slug: match[2] ?? "" } : null;
}

export function supplierPath(fei: string, slug: string): string {
  return `/supplier/${fei}-${slug}`;
}

export function supplierTitle(name: string): string {
  return `${name} — FDA import refusal & import alert records`;
}

export function parsePage(value: string | undefined): number {
  return value && /^[1-9]\d{0,5}$/.test(value) ? Number(value) : 1;
}

function plural(n: number, unit: string): string {
  return `${n} ${unit}${n === 1 ? "" : "s"} ago`;
}

/** Age of an ISO date relative to `today` (also ISO), e.g. "9 days ago". */
export function relativeDays(date: string, today: string): string {
  const days = Math.round((Date.parse(today) - Date.parse(date)) / DAY_MS);
  if (days <= 0) return "today";
  if (days < 60) return plural(days, "day");
  if (days < 365) return plural(Math.floor(days / 30), "month");
  return plural(Math.floor(days / 365), "year");
}

export function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}
