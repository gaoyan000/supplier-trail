import { describe, expect, it } from "vitest";

import { parsePage, parseSupplierId, relativeDays, supplierPath, supplierTitle } from "./format";

describe("parseSupplierId", () => {
  it("splits the FEI from the slug", () => {
    expect(parseSupplierId("3000000000-example-foods-co-ltd")).toEqual({
      fei: "3000000000",
      slug: "example-foods-co-ltd",
    });
  });

  it("accepts a bare FEI", () => {
    expect(parseSupplierId("3000000000")).toEqual({ fei: "3000000000", slug: "" });
  });

  it.each(["example-foods", "", "30x0-foods", "-foods", "1234567890123456-foods"])("rejects %j", (id) => {
    expect(parseSupplierId(id)).toBeNull();
  });
});

describe("supplierPath", () => {
  it("builds the canonical URL path", () => {
    expect(supplierPath("3000000000", "example-foods-co-ltd")).toBe("/supplier/3000000000-example-foods-co-ltd");
  });
});

describe("relativeDays", () => {
  it.each([
    ["2026-10-09", "today"],
    ["2026-10-08", "1 day ago"],
    ["2026-09-30", "9 days ago"],
    ["2026-07-09", "3 months ago"],
    ["2025-10-09", "1 year ago"],
    ["2021-02-01", "5 years ago"],
  ])("%s → %s", (date, expected) => {
    expect(relativeDays(date, "2026-10-09")).toBe(expected);
  });
});

describe("supplierTitle", () => {
  it("uses the title template from design §10 Rule 2", () => {
    expect(supplierTitle("Example Foods Co., Ltd")).toBe(
      "Example Foods Co., Ltd — FDA import refusal & import alert records",
    );
  });
});

describe("parsePage", () => {
  it.each([
    [undefined, 1],
    ["1", 1],
    ["3", 3],
    ["0", 1],
    ["-2", 1],
    ["abc", 1],
    ["2.5", 1],
  ])("%j → %i", (value, expected) => {
    expect(parsePage(value)).toBe(expected);
  });
});
