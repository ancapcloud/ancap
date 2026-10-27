import { describe, expect, it } from "vitest";
import { formatValueEstimate } from "./workflowValue";
import { workflowValueCopy } from "../locales/workflowValue";

describe("private value estimates", () => {
  it.each([null, "", "NaN", "Infinity"])("keeps unknown or invalid values unknown: %s", value => expect(formatValueEstimate(value, "en")).toBeNull());
  it("retains explicit zero", () => expect(formatValueEstimate("0", "en")).toBe("0"));
  it("retains negative estimates", () => expect(formatValueEstimate("-1234.5", "en")).toBe("-1,234.5"));
  it("formats for the active language", () => expect(formatValueEstimate("-1234.5", "de")).toBe("-1.234,5"));
  it.each(Object.entries(workflowValueCopy))("provides complete copy for %s", (_lang, copy) => {
    expect(Object.keys(copy).sort()).toEqual(Object.keys(workflowValueCopy.en).sort());
    expect(Object.values(copy).every(text => text.trim().length > 0)).toBe(true);
    expect(copy.scope).toContain("{days}"); expect(copy.scope).toContain("{limit}");
    expect(copy.estimatesWarning).toContain("ROI");
  });
});
