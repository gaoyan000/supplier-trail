import { describe, expect, it } from "vitest";

import { normalizeName } from "./normalize";

// Same cases as etl/tests/test_normalize.py: search must normalize exactly as the pipeline does.
describe("normalizeName", () => {
  it.each([
    ["FUJIAN SHENGLINMARK  TRADE CO.LTD.", "fujian shenglinmark trade co ltd"],
    ["Anhui Xinong Pharma Co., Ltd.", "anhui xinong pharma co ltd"],
    ["ANHUI XINONG PHARMA CO.,LTD", "anhui xinong pharma co ltd"],
    ["Dion Herbs & Spices", "dion herbs and spices"],
    ["Société Boudjebel S.A.", "societe boudjebel s a"],
    ["  ", ""],
    ["100% _wild_ \\ honey", "100 wild honey"],
  ])("%j → %j", (name, expected) => {
    expect(normalizeName(name)).toBe(expected);
  });
});
