import { describe, expect, it } from "vitest";

import { eventView, parseFilter, type EventRow } from "./events";

const base: EventRow = {
  id: 1,
  type: "refusal",
  occurredOn: "2026-09-30",
  summary: "Shipment refused · FDA charge codes: 2580 · Product: SAMPLE DRIED MUSHROOMS",
  details: {},
  sourceUrl: "https://datadashboard.fda.gov/oii/firmprofile.htm?FEIu=3000000000",
};

describe("eventView", () => {
  it("shows a refusal with FDA's summary, shipment line and product code", () => {
    const view = eventView({ ...base, details: { ShipmentID: "AAA-0000001-1/1/1", ProductCode: "25JGT05" } });
    expect(view).toEqual({
      chip: "Import refusal",
      listed: false,
      title: base.summary,
      detail: "Shipment line AAA-0000001-1/1/1 · Product code 25JGT05",
    });
  });

  it("shows an inspection with its project area", () => {
    const view = eventView({
      ...base,
      type: "inspection_vai",
      summary: "FDA inspection · Classification: Voluntary Action Indicated (VAI)",
      details: { ProjectArea: "Foodborne Biological Hazards" },
    });
    expect(view.chip).toBe("Inspection");
    expect(view.detail).toBe("Project area: Foodborne Biological Hazards");
  });

  it("shows a recall with FDA's product description, shortened", () => {
    const view = eventView({
      ...base,
      type: "recall",
      summary: "Recall F-0000-2025 · Class 1 · Undeclared allergens (wheat)",
      details: { PRODUCTDESCRIPTIONTXT: "x".repeat(400) },
    });
    expect(view.chip).toBe("Recall");
    expect(view.detail).toHaveLength(241);
    expect(view.detail?.endsWith("…")).toBe(true);
  });

  it.each([
    ["warning_letter", "Warning letter"],
    ["compliance_action", "Compliance action"],
  ])("labels %s as %s with no extra detail", (type, chip) => {
    expect(eventView({ ...base, type, details: {} })).toMatchObject({ chip, detail: null, listed: false });
  });

  it.each(["alert_listed", "alert_removed"])("marks %s as an import-alert event", (type) => {
    const view = eventView({ ...base, type, summary: "Added to red list, Import Alert 99-19" });
    expect(view.chip).toBe("Import alert");
    expect(view.listed).toBe(type === "alert_listed");
  });

  it("leaves detail empty when FDA's record has no extra fields", () => {
    expect(eventView(base).detail).toBeNull();
  });
});

describe("parseFilter", () => {
  it.each([
    ["refusals", "refusals"],
    ["actions", "actions"],
    [undefined, "all"],
    ["nonsense", "all"],
  ])("%j → %s", (value, expected) => {
    expect(parseFilter(value).key).toBe(expected);
  });
});
