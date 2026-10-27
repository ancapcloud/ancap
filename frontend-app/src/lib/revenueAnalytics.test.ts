import { describe, expect, it } from "vitest";
import { topWorkflowsByCurrency } from "./revenueAnalytics";

describe("currency-isolated revenue rankings", () => {
  it("keeps independent rankings and limits without mutating the API response", () => {
    const rows = [
      { workflow_slug: "small", currency: "ACP", captured_amount: "2" },
      { workflow_slug: "usd", currency: "USD", captured_amount: "900" },
      { workflow_slug: "large", currency: "ACP", captured_amount: "10" },
    ];
    expect(topWorkflowsByCurrency(rows, 1)).toEqual([
      { currency: "ACP", items: [rows[2]] },
      { currency: "USD", items: [rows[1]] },
    ]);
    expect(rows.map(r => r.workflow_slug)).toEqual(["small", "usd", "large"]);
  });
  it("handles empty and zero-valued data deterministically", () => {
    expect(topWorkflowsByCurrency([])).toEqual([]);
    expect(topWorkflowsByCurrency([
      { workflow_slug: "b", currency: "ACP" },
      { workflow_slug: "a", currency: "ACP", captured_amount: "0" },
    ])[0].items.map(r => r.workflow_slug)).toEqual(["a", "b"]);
  });
});
