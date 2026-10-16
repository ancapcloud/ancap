import { describe, it, expect } from "vitest";
import { calculateEarningsScenario, exampleEarningsInputs, formatScenarioAmount } from "../earningsScenario";
import { economyByLang } from "@/locales/economy";

describe("illustrative earnings calculation", () => {
  it("deducts the fee, per-order costs and fixed costs exactly once", () => {
    expect(calculateEarningsScenario(exampleEarningsInputs)).toEqual({ gross: "1000.00000000", fee: "100.00000000", costs: "200.00000000", net: "700.00000000", loss: false });
  });
  it("preserves ACP precision, rounds fees once and permits losses", () => {
    expect(calculateEarningsScenario({ price: "0.00000003", orders: "1", feePercent: "50", variableCost: "0", fixedCost: "0" })?.fee).toBe("0.00000002");
    expect(calculateEarningsScenario({ ...exampleEarningsInputs, orders: "0" })).toMatchObject({ net: "-50.00000000", loss: true });
    expect(calculateEarningsScenario({ ...exampleEarningsInputs, feePercent: "100" })?.net).toBe("-200.00000000");
  });
  it("rejects incomplete, negative, fractional-order and out-of-range inputs", () => {
    for (const patch of [{ price: "" }, { price: "-1" }, { price: "1e5" }, { price: "0.000000001" }, { orders: "1.5" }, { feePercent: "100.01" }, { feePercent: "2.123" }, { variableCost: "NaN" }]) expect(calculateEarningsScenario({ ...exampleEarningsInputs, ...patch })).toBeNull();
  });
  it("formats high precision without converting ACP totals to floating point", () => {
    expect(formatScenarioAmount("-0.00000001", "en")).toBe("−0.00000001");
    expect(formatScenarioAmount("999999999999.00000001", "en")).toBe("999,999,999,999.00000001");
  });
  it("provides matching nonempty copy and five planned steps in five languages", () => {
    expect(Object.keys(economyByLang).sort()).toEqual(["en", "ru", "uk", "de", "zh-Hant"].sort());
    for (const copy of Object.values(economyByLang)) {
      expect(Object.keys(copy).sort()).toEqual(Object.keys(economyByLang.en).sort());
      expect(copy.steps).toHaveLength(5); expect(copy.stepNotes).toHaveLength(5);
      for (const value of Object.values(copy).flat()) expect(value.trim()).not.toBe("");
    }
  });
});
