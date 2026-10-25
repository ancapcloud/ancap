import { test, expect } from "@playwright/test";
import { paymentScannerCopy } from "../src/locales/paymentScanner";

const copy = paymentScannerCopy.en;

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("ancap_cookie_consent_v1", JSON.stringify({ necessary: true, analytics: false, marketing: false }));
  });
  await page.route("**/users/me", route => route.fulfill({ json: {
    id: "scanner-fixture", email: "scanner@example.com", display_name: "Scanner test",
  } }));
  await page.route("**/payment-scanner/parse", route => route.fulfill({ json: {
    detected_network: "acp", address: "acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9", amount: "10", currency: "ACP",
    confidence: 0.8, parse_notes: [], can_pay_acp: true, recommendations: [],
  } }));
  await page.goto("/payment-scanner");
});

test("editing payment input clears the reviewed payment and wallet continuation", async ({ page }) => {
  await page.locator("textarea").fill("acp:acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9?amount=10");
  await page.getByRole("button", { name: copy.preview, exact: true }).click();
  await page.getByRole("checkbox").check();
  await expect(page.getByRole("link", { name: copy.pay })).toHaveAttribute("href", "/wallet/acp#payTo=acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9&payAmount=10");
  await page.locator("textarea").fill("a different invoice");
  await expect(page.getByRole("checkbox")).toHaveCount(0);
  await expect(page.getByRole("link", { name: copy.pay })).toHaveCount(0);
});

test("failed replacement parse cannot retain an old reviewed result", async ({ page }) => {
  await page.locator("textarea").fill("acp:acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9?amount=10");
  await page.getByRole("button", { name: copy.preview, exact: true }).click();
  await expect(page.getByRole("checkbox")).toBeVisible();
  await page.route("**/payment-scanner/parse", route => route.fulfill({ status: 422, json: { detail: "Invalid invoice" } }));
  await page.getByRole("button", { name: copy.preview, exact: true }).click();
  await expect(page.getByText(/Invalid invoice/)).toBeVisible();
  await expect(page.getByRole("checkbox")).toHaveCount(0);
});

test("unsupported images are rejected before uploading", async ({ page }) => {
  let uploads = 0;
  await page.route("**/payment-scanner/parse-image", route => { uploads++; return route.abort(); });
  await page.locator('input[type="file"]').nth(1).setInputFiles({
    name: "invoice.svg", mimeType: "image/svg+xml", buffer: Buffer.from("<svg/>")
  });
  await expect(page.getByText(copy.imageSize, { exact: true })).toBeVisible();
  expect(uploads).toBe(0);
});

test("a spoofed raster upload is rejected before preview or upload", async ({ page }) => {
  const dialogs: string[] = [];
  page.on("dialog", async dialog => { dialogs.push(dialog.message()); await dialog.dismiss(); });
  let uploads = 0;
  await page.route("**/payment-scanner/parse-image", route => { uploads++; return route.abort(); });
  await page.locator('input[type="file"]').nth(1).setInputFiles({
    name: "invoice.png", mimeType: "image/png",
    buffer: Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" onload="window.__scannerXss=true;alert(1)"></svg>'),
  });
  await expect(page.getByText(copy.error, { exact: true })).toBeVisible();
  await expect(page.locator('img[alt="invoice.png"]')).toHaveCount(0);
  expect(uploads).toBe(0);
  expect(await page.evaluate(() => (window as Window & { __scannerXss?: boolean }).__scannerXss)).toBeUndefined();
  expect(dialogs).toEqual([]);
});

test("valid raster preview is browser-encoded PNG and parsed labels stay text", async ({ page }) => {
  await page.route("**/payment-scanner/parse-image", route => route.fulfill({ json: {
    detected_network: "acp", address: "acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9", amount: "10", currency: "ACP",
    confidence: 0.8, parse_notes: ["<img src=x onerror=alert('note-xss')>"],
    label: "<script>window.__scannerXss = true</script>",
  } }));
  const png = await page.evaluate(() => {
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = 2;
    return canvas.toDataURL("image/png").split(",")[1];
  });
  await page.locator('input[type="file"]').nth(1).setInputFiles({
    name: "invoice.png", mimeType: "image/png", buffer: Buffer.from(png, "base64"),
  });
  await expect(page.getByText(`${copy.label}: <script>window.__scannerXss = true</script>`, { exact: true })).toBeVisible();
  await expect(page.locator('img[alt="invoice.png"]')).toHaveAttribute("src", /^data:image\/png;base64,/);
  expect(await page.evaluate(() => (window as Window & { __scannerXss?: boolean }).__scannerXss)).toBeUndefined();
});
