import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("ancap_cookie_consent_v1", JSON.stringify({ necessary: true, analytics: false, marketing: false }));
  });
  await page.route("**/users/me", route => route.fulfill({ json: {
    id: "scanner-fixture", email: "scanner@example.com", display_name: "Scanner test",
  } }));
  await page.route("**/payment-scanner/parse", route => route.fulfill({ json: {
    detected_network: "acp", address: "acp1fixture", amount: "10", currency: "ACP",
    confidence: 0.8, parse_notes: [],
  } }));
  await page.goto("/payment-scanner");
});

test("editing payment input clears the reviewed payment and wallet continuation", async ({ page }) => {
  await page.locator("textarea").fill("acp:acp1fixture?amount=10");
  await page.getByRole("button", { name: "Preview payment", exact: true }).click();
  await page.getByRole("checkbox").check();
  await expect(page.getByRole("link", { name: "Continue in wallet" })).toBeVisible();
  await page.locator("textarea").fill("a different invoice");
  await expect(page.getByRole("checkbox")).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Continue in wallet" })).toHaveCount(0);
});

test("failed replacement parse cannot retain an old reviewed result", async ({ page }) => {
  await page.locator("textarea").fill("acp:acp1fixture?amount=10");
  await page.getByRole("button", { name: "Preview payment", exact: true }).click();
  await expect(page.getByRole("checkbox")).toBeVisible();
  await page.route("**/payment-scanner/parse", route => route.fulfill({ status: 422, json: { detail: "Invalid invoice" } }));
  await page.getByRole("button", { name: "Preview payment", exact: true }).click();
  await expect(page.getByText(/Invalid invoice/)).toBeVisible();
  await expect(page.getByRole("checkbox")).toHaveCount(0);
});

test("unsupported images are rejected before uploading", async ({ page }) => {
  let uploads = 0;
  await page.route("**/payment-scanner/parse-image", route => { uploads++; return route.abort(); });
  await page.locator('input[type="file"]').nth(1).setInputFiles({
    name: "invoice.svg", mimeType: "image/svg+xml", buffer: Buffer.from("<svg/>")
  });
  await expect(page.getByText("Choose a JPEG, PNG, WebP or GIF image up to 10 MB.")).toBeVisible();
  expect(uploads).toBe(0);
});
