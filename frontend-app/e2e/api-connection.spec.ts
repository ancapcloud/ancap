import { expect, test } from "@playwright/test";

test.setTimeout(90_000);

test("AI onboarding is the first homepage section and visible on mobile", async ({ page }) => {
  await page.route("**/v1/**", route => route.fulfill({ status: 401, json: { detail: "Sign in" } }));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  const creators = page.locator("#connect-ai");
  await expect(page.locator("main > section").first()).toHaveAttribute("id", "connect-ai");
  await expect(creators.getByRole("heading", { name: "Your expertise. Your AI. One workspace." })).toBeVisible();
  await expect(creators.getByText("ChatGPT", { exact: true })).toBeVisible();
  await expect(creators.getByText("Cursor", { exact: true })).toBeVisible();
  await expect(creators.getByText("OpenClaw", { exact: true })).toBeVisible();
  await expect(creators.getByRole("link", { name: "Connect via API" })).toHaveAttribute("href", "/developers/connect");
  await expect(page.locator("#creator-ai-title")).toHaveCount(1);
  const copyButton = await creators.getByRole("button", { name: "Copy starter prompt" }).boundingBox();
  expect(copyButton).not.toBeNull();
  expect(copyButton!.y + copyButton!.height).toBeLessThan(844);
  const cookies = page.getByRole("button", { name: "Necessary only", exact: true });
  if (await cookies.isVisible()) await cookies.click();
  await page.screenshot({ path: test.info().outputPath("creators-mobile.png"), fullPage: false });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: test.info().outputPath("creators-desktop.png"), fullPage: false });
});

test("developer CTA opens API setup and guests must sign in", async ({ page }) => {
  await page.route("**/v1/users/me", route => route.fulfill({ status: 401, json: { detail: "Sign in" } }));
  await page.goto("/developers");
  await page.getByRole("link", { name: "Manage API key", exact: true }).click();
  await expect(page).toHaveURL(/\/developers\/connect$/, { timeout: 30_000 });
  await expect(page.getByRole("link", { name: "Sign in to manage your API key" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Create API key", exact: true })).toHaveCount(0);
});

test("one account key can be created, replaced and deleted with statistics", async ({ page }) => {
  let active = false;
  let creates = 0;
  let rotations = 0;
  let deletes = 0;
  const status = () => ({ active, key_prefix: active ? "ancap_display" : null, requests: 12, successful_requests: 10, failed_requests: 2, created_at: null, last_used_at: null });
  await page.route("**/v1/**", route => {
    const path = new URL(route.request().url()).pathname;
    const method = route.request().method();
    if (path.endsWith("/users/me")) return route.fulfill({ json: { id: "owner", email: "owner@example.test" } });
    if (path.endsWith("/keys/account/rotate")) {
      rotations++; active = true;
      return route.fulfill({ json: { ...status(), key: "ancap_test_replacement_not_real" } });
    }
    if (path.endsWith("/keys/account")) {
      if (method === "POST") {
        expect(route.request().postData()).toBeNull();
        creates++; active = true;
        return route.fulfill({ status: 201, json: { ...status(), key: "ancap_test_only_not_a_real_key" } });
      }
      if (method === "DELETE") { deletes++; active = false; return route.fulfill({ status: 204 }); }
      return route.fulfill({ json: status() });
    }
    return route.fulfill({ json: {} });
  });
  await page.goto("/developers/connect");
  await expect(page.getByRole("combobox")).toHaveCount(0);
  await page.getByRole("button", { name: "Create API key", exact: true }).click();
  await expect(page.getByText("ancap_test_only_not_a_real_key", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Create API key", exact: true })).toHaveCount(0);
  expect(creates).toBe(1);
  expect(await page.evaluate(() => JSON.stringify({ ...localStorage, ...sessionStorage }))).not.toContain("ancap_test_only_not_a_real_key");
  await page.getByRole("button", { name: "Replace key", exact: true }).click();
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  expect(rotations).toBe(0);
  await page.getByRole("button", { name: "Replace key", exact: true }).click();
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await expect(page.getByText("ancap_test_replacement_not_real", { exact: true })).toBeVisible();
  expect(rotations).toBe(1);
  await page.getByRole("button", { name: "Delete key", exact: true }).click();
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await expect(page.getByRole("button", { name: "Create API key", exact: true })).toBeVisible();
  await expect(page.getByText("ancap_test_replacement_not_real", { exact: true })).toHaveCount(0);
  expect(deletes).toBe(1);
  await expect(page.getByLabel("API statistics")).toContainText("12");
  await page.getByRole("button", { name: "Refresh statistics", exact: true }).click();
  await expect(page.getByLabel("API statistics")).toContainText("12");
  await page.screenshot({ path: test.info().outputPath("account-api.png"), fullPage: true });
});

test("failed key creation can be retried without exposing a secret", async ({ page }) => {
  await page.route("**/v1/**", route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/users/me")) return route.fulfill({ json: { id: "owner", email: "owner@example.test" } });
    if (path.endsWith("/keys/account") && route.request().method() === "GET") return route.fulfill({ json: { active: false, requests: 0, successful_requests: 0, failed_requests: 0 } });
    if (path.endsWith("/keys/account")) return route.fulfill({ status: 503, json: { detail: "Unavailable" } });
    return route.fulfill({ json: {} });
  });
  await page.goto("/developers/connect");
  await page.getByRole("button", { name: "Create API key", exact: true }).click();
  await expect(page.locator('p[role="alert"]')).toBeVisible();
  await expect(page.getByRole("button", { name: "Create API key", exact: true })).toBeEnabled();
  await expect(page.getByRole("button", { name: "Copy key" })).toHaveCount(0);
});
