import { test, expect, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { workflowValueCopy } from "../src/locales/workflowValue";
const hash = "a".repeat(64), runId = "11111111-1111-4111-8111-111111111111";
const summary = {
  days: 30, limit: 200, truncated: false, window_start: "2026-09-27T00:00:00Z", window_end: "2026-10-27T00:00:00Z",
  completed_count: 3, assessed_count: 2, accepted_count: 1, revision_requested_count: 1, rejected_count: 0,
  timed_assessment_count: 2, labor_valued_count: 2, estimated_minutes_saved: "-30",
  estimated_labor_value: [{ amount: "-15", currency: "USD" }, { amount: "10", currency: "ACP" }],
  ledger_charges: [{ amount: "4", currency: "ACP" }, { amount: "2", currency: "EUR" }], estimates_are_self_reported: true, ledger_charges_are_verified_external_payments: false, scope_basis: "completed_runs_created_in_window",
};
async function fixtures(page: Page, options: { stale?: boolean; conflict?: boolean; guest?: boolean } = {}) {
  let assessment: unknown = null;
  const writes: { path: string; body: Record<string, unknown> }[] = [];
  await page.addInitScript(() => localStorage.setItem("ancap_cookie_consent_v1", JSON.stringify({ necessary: true, analytics: false, marketing: false })));
  await page.route("**/v1/**", route => {
    const request = route.request(), path = new URL(request.url()).pathname;
    if (path.endsWith("/users/me")) return route.fulfill({ status: options.guest ? 401 : 200, json: options.guest ? { detail: "Login" } : { id: "value-fixture", email: "private@example.test", display_name: "Private fixture" } });
    if (request.method() === "POST") {
      const body = request.postDataJSON(); writes.push({ path, body });
      if (!path.endsWith("/assessment")) return route.fulfill({ status: 400, json: { detail: "No payment writes in value tests" } });
      if (options.conflict) return route.fulfill({ status: 409, json: { detail: "Result changed" } });
      assessment = { id: "assessment-fixture", workflow_run_id: runId, created_at: "2026-10-27T00:00:00Z", ...body };
      return route.fulfill({ status: 201, json: assessment });
    }
    if (path.endsWith("/assessments")) return route.fulfill({ json: { items: [{ id: "archived-fixture", workflow_run_id: runId, result_hash: hash, verdict: "accepted", baseline_minutes: null, assisted_minutes: null, hourly_rate: null, hourly_currency: null, note: null, created_at: "2026-10-27T00:00:00Z" }], has_more: false } });
    if (path.endsWith("/assessments/archived-fixture/result")) return route.fulfill({ json: { assessment_id: "archived-fixture", result_hash: hash, result: { output: "Archived reviewed version fixture" } } });
    if (path.endsWith("/workflow-store/value")) return route.fulfill({ json: summary });
    if (path.endsWith("/assessment")) return route.fulfill({ json: { result_hash: options.stale ? "b".repeat(64) : hash, assessment, has_stale_assessment: !!options.stale } });
    if (path.endsWith(`/runs/${runId}`)) return route.fulfill({ json: {
      id: runId, result_hash: hash, workflow_slug: "token-risk-report", title: "Reviewed result fixture", category: "test", status: "completed",
      price: { amount: "5", currency: "ACP" }, payment_currency: "ACP", unlock_full_result: true, inputs: {}, preview: {}, result: { output: "Review this delivered result" },
      receipt: { workflow_slug: "token-risk-report", payment_currency: "ACP", quoted_price: { amount: "5", currency: "ACP" }, status: "completed", receipt_items: [], proof: {} }, created_at: "2026-10-27T00:00:00Z",
    } });
    if (path.endsWith("/receipt-trail")) return route.fulfill({ json: { workflow_run_id: runId, settlement_intent: null, chain_receipts: [] } });
    if (path.endsWith("/proof-bundle")) return route.fulfill({ json: { bundle_version: "1", generated_at: "2026-10-27T00:00:00Z", workflow_run_id: runId, proof_hash: hash, receipt_items: [], payment_confirmation: null, execution: {}, settlement_intent: null, chain_receipts: [], summary: { payment_confirmed: false, settlement_status: null, chain_receipt_count: 0, finalized_receipt_count: 0, failed_receipt_count: 0, submitted_receipt_count: 0 } } });
    return route.fulfill({ json: { items: [] } });
  });
  return writes;
}
for (const lang of ["en", "ru", "uk", "de", "zh-Hant"] as const) {
  test(`private value dashboard keeps estimates and units separate in ${lang}`, async ({ page }, testInfo) => {
    const errors: string[] = []; page.on("pageerror", e => errors.push(e.message));
    await fixtures(page);
    await page.addInitScript(language => localStorage.setItem("ancap-lang-v3", language), lang);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/ai/value");
    const copy = workflowValueCopy[lang];
    await expect(page.getByRole("heading", { name: copy.title, exact: true })).toBeVisible();
    await expect(page.getByRole("region", { name: copy.timeSaved })).toContainText("-30");
    await expect(page.getByRole("region", { name: copy.laborValue })).toContainText("-15 USD");
    await expect(page.getByRole("region", { name: copy.laborValue })).toContainText("10 ACP");
    const downloading = page.waitForEvent("download");
    await page.getByRole("button", { name: copy.export, exact: true }).click();
    const download = await downloading, path = await download.path();
    const exported = await readFile(path!, "utf8");
    expect(JSON.parse(exported).estimates_are_self_reported).toBe(true);
    expect(JSON.parse(exported).ledger_charges_are_verified_external_payments).toBe(false);
    expect(exported).not.toContain("private@example.test"); expect(exported).not.toContain("output");
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    expect(errors).toEqual([]);
    await page.screenshot({ path: testInfo.outputPath(`private-value-${lang}.png`), fullPage: true });
  });
}
test("assessment saves once for the reviewed hash and exposes no edit control", async ({ page }) => {
  const writes = await fixtures(page), copy = workflowValueCopy.en;
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`/ai/runs/${runId}`);
  const form = page.getByRole("region", { name: copy.acceptanceTitle });
  await form.getByLabel(copy.baseline, { exact: true }).fill("30");
  await form.getByLabel(copy.assisted, { exact: true }).fill("60");
  await form.getByLabel(copy.rate, { exact: true }).fill("30");
  await form.getByLabel(copy.note, { exact: true }).fill("Private result review");
  await form.getByRole("button", { name: copy.submit, exact: true }).click();
  await expect(form).toContainText(`${copy.saved}: ${copy.accepted}`);
  await expect(form.getByRole("button", { name: copy.submit, exact: true })).toHaveCount(0);
  expect(writes).toHaveLength(1); expect(writes[0].body.result_hash).toBe(hash);
  expect(writes[0].body.assisted_minutes).toBe("60");
});
test("a result mismatch blocks submitting against unseen output", async ({ page }) => {
  await fixtures(page, { stale: true });
  await page.goto(`/ai/runs/${runId}`);
  const copy = workflowValueCopy.en, form = page.getByRole("region", { name: copy.acceptanceTitle });
  await expect(form).toContainText(copy.stale);
  await expect(form.getByRole("button", { name: copy.submit, exact: true })).toHaveCount(0);
});
test("a concurrent save conflict requires reloading rather than silently retrying", async ({ page }) => {
  const writes = await fixtures(page, { conflict: true });
  await page.goto(`/ai/runs/${runId}`);
  const copy = workflowValueCopy.en, form = page.getByRole("region", { name: copy.acceptanceTitle });
  await form.getByRole("button", { name: copy.submit, exact: true }).click();
  await expect(form.getByRole("alert")).toContainText(copy.reload);
  await expect(form.getByRole("button", { name: copy.reload, exact: true })).toBeVisible();
  expect(writes).toHaveLength(1);
});
test("private dashboard sends unauthenticated visitors to login", async ({ page }) => {
  await fixtures(page, { guest: true });
  await page.goto("/ai/value");
  await expect(page).toHaveURL(/\/login/);
});


test("reviewed result history opens a private archived version", async ({ page }) => {
  await fixtures(page);
  await page.goto(`/ai/runs/${runId}`);
  const copy = workflowValueCopy.en, section = page.getByRole("region", { name: copy.acceptanceTitle });
  await section.getByRole("button", { name: copy.history, exact: true }).click();
  await expect(section).toContainText(copy.historyHelp);
  await section.getByRole("button", { name: copy.viewVersion, exact: true }).click();
  await expect(section).toContainText("Archived reviewed version fixture");
  await section.getByRole("button", { name: copy.hideVersion, exact: true }).click();
  await expect(section).not.toContainText("Archived reviewed version fixture");
});
