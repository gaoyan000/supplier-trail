/** How FDA events are grouped and worded on public pages. FDA's terms only (design §10 Rule 2). */
export type EventRow = {
  id: number;
  type: string;
  occurredOn: string;
  summary: string;
  details: Record<string, unknown>;
  sourceUrl: string | null;
};

export const EVENT_FILTERS = [
  { key: "all", label: "All", types: null },
  { key: "alerts", label: "Import alerts", types: ["alert_listed", "alert_removed"] },
  { key: "refusals", label: "Refusals", types: ["refusal"] },
  { key: "inspections", label: "Inspections", types: ["inspection_nai", "inspection_vai", "inspection_oai"] },
  { key: "recalls", label: "Recalls", types: ["recall"] },
  { key: "actions", label: "Compliance actions", types: ["warning_letter", "compliance_action"] },
] as const;

export type EventFilter = (typeof EVENT_FILTERS)[number];
export type FilterKey = EventFilter["key"];

export function parseFilter(value: string | undefined): EventFilter {
  return EVENT_FILTERS.find((f) => f.key === value) ?? EVENT_FILTERS[0];
}

const CHIPS: Record<string, string> = {
  refusal: "Import refusal",
  recall: "Recall",
  warning_letter: "Warning letter",
  compliance_action: "Compliance action",
  inspection_nai: "Inspection",
  inspection_vai: "Inspection",
  inspection_oai: "Inspection",
  alert_listed: "Import alert",
  alert_removed: "Import alert",
};

const MAX_DESCRIPTION = 240;

function text(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function detail(event: EventRow): string | null {
  const d = event.details;
  if (event.type === "refusal") {
    const shipment = text(d.ShipmentID);
    const code = text(d.ProductCode);
    const parts = [shipment && `Shipment line ${shipment}`, code && `Product code ${code}`].filter(Boolean);
    return parts.length ? parts.join(" · ") : null;
  }
  if (event.type.startsWith("inspection_")) {
    const area = text(d.ProjectArea);
    return area && `Project area: ${area}`;
  }
  if (event.type === "recall") {
    const product = text(d.PRODUCTDESCRIPTIONTXT);
    return product && product.length > MAX_DESCRIPTION ? `${product.slice(0, MAX_DESCRIPTION)}…` : product;
  }
  return null;
}

export type EventView = { chip: string; listed: boolean; title: string; detail: string | null };

export function eventView(event: EventRow): EventView {
  return {
    chip: CHIPS[event.type] ?? "FDA record",
    listed: event.type === "alert_listed",
    title: event.summary,
    detail: detail(event),
  };
}
