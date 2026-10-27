import { test, expect } from "@playwright/test";

test("analytics keeps currencies separate including cost-only currencies", async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.route("**/v1/**", route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/users/me")) return route.fulfill({ json: { id: "revenue-fixture", email: "fixture@example.com", display_name: "Fixture" } });
    if (path.endsWith("/workflow-store/admin/revenue")) return route.fulfill({ json: {
      window_days: 30,
      totals: [{ currency: "ACP", status: "captured", amount: "10" }, { currency: "USD", status: "captured", amount: "20" }],
      estimated_margin_totals: [{ currency: "ACP", amount: "7" }, { currency: "USD", amount: "15" }],
      estimated_cost_totals: [{ currency: "ACP", amount: "3" }, { currency: "USD", amount: "5" }, { currency: "sACP", amount: "2" }],
      referral_commission_totals: [], run_status_counts: {}, payment_status_counts: {},
      skus: [{ workflow_slug: "acp-workflow", currency: "ACP", captured_amount: "10" }, { workflow_slug: "usd-workflow", currency: "USD", captured_amount: "20" }],
    } });
    return route.fulfill({ json: {} });
  });
  await page.goto("/dashboard/analytics");
  await expect(page.getByRole("note")).toContainText("Internal ledger");
  const margin = page.locator("div.rounded-lg").filter({ has: page.getByText("Est. Margin", { exact: true }) }).first();
  await expect(margin).toContainText("7.00 ACP");
  await expect(margin).toContainText("15.00 USD");
  await expect(page.getByRole("region", { name: "Captured ACP", exact: true })).toContainText("acp-workflow");
  await expect(page.getByRole("region", { name: "Captured USD", exact: true })).toContainText("usd-workflow");
  await expect(page.getByText("Gross 0.00 · Margin 0.00 · Cost 2.00 · Referral 0.00")).toBeVisible();
  expect(errors).toEqual([]);
  await page.screenshot({ path: testInfo.outputPath("currency-analytics.png"), fullPage: true });
});
