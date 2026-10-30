import { describe, it, expect } from "vitest";
import { acpToRacpEquivalent } from "./racpDisplay";

describe("rACP display equivalents", () => {
  it("scales eight-decimal ACP exactly without changing accounting", () => {
    expect(acpToRacpEquivalent("1")).toBe("10");
    expect(acpToRacpEquivalent("0.00000001")).toBe("0.0000001");
    expect(acpToRacpEquivalent("32883823.16372116")).toBe("328838231.6372116");
    expect(acpToRacpEquivalent("-0.25")).toBe("-2.5");
  });
  it("rejects malformed accounting values", () => {
    for (const value of ["NaN", "1e9", "0.000000001", ""]) expect(() => acpToRacpEquivalent(value)).toThrow();
  });
});
