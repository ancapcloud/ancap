import { test, expect } from "@playwright/test";

test("card checkout displays explicit USD terms and disables missing fiat prices", async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", e => errors.push(e.message));
  await page.addInitScript(() => localStorage.setItem("ancap_cookie_consent_v1", JSON.stringify({ necessary: true, analytics: false, marketing: false })));
  await page.route("**/v1/**", route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/users/me")) return route.fulfill({ json: { id: "credit-fixture", email: "credit@example.test", display_name: "Credit fixture" } });
    if (path.endsWith("/ledger/balance")) return route.fulfill({ json: { account_id: "fixture-account", balances: [] } });
    if (path.endsWith("/payments/stripe/status")) return route.fulfill({ json: { configured: true } });
    if (path.endsWith("/workflow-store/credit-packages")) return route.fulfill({ json: { items: [
      { slug: "explicit", title: "Explicit USD package", description: "Fixture", price: { amount: "999", currency: "ACP" }, fiat_price: { amount: "25", currency: "USD" }, credit_amount: { amount: "100", currency: "ACP" }, accepted_currencies: ["ACP"], bonus_percent: 0, recommended_for: [] },
      { slug: "token-only", title: "ACP-only package", description: "Fixture", price: { amount: "71", currency: "ACP" }, credit_amount: { amount: "71", currency: "ACP" }, accepted_currencies: ["ACP"], bonus_percent: 0, recommended_for: [] },
    ] } });
    return route.fulfill({ json: { items: [] } });
  });
  await page.goto("/wallet/credits");
  const explicit = page.locator(".card").filter({ has: page.getByText("Explicit USD package", { exact: true }) });
  await expect(explicit).toContainText("999 ACP");
  await expect(explicit).toContainText("25 USD");
  await expect(explicit).not.toContainText("999 USD");
  await expect(explicit.getByRole("button").nth(1)).toBeEnabled();
  const unavailable = page.locator(".card").filter({ has: page.getByText("ACP-only package", { exact: true }) });
  await expect(unavailable.getByRole("button").nth(1)).toBeDisabled();
  await expect(unavailable).not.toContainText("71 USD");
  expect(errors).toEqual([]);
  await page.screenshot({ path: testInfo.outputPath("explicit-fiat-pricing.png"), fullPage: true });
});
