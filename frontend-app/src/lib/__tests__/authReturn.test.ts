import { describe, expect, it } from "vitest";
import { safeAuthReturn } from "../authReturn";

describe("authentication return destination", () => {
  it("keeps a selected workflow or wallet recovery destination", () => {
    expect(safeAuthReturn("/ai/run/token-risk-report")).toBe("/ai/run/token-risk-report");
    expect(safeAuthReturn("/wallet/acp#password-security")).toBe("/wallet/acp#password-security");
  });
  it.each([null, "", "https://example.com", "//example.com", "/\\example.com", "/\n/example.com"])("rejects unsafe destination %s", path => {
    expect(safeAuthReturn(path)).toBe("/dashboard");
  });
});
