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
  await page.getByRole("link", { name: "Create agent/API key", exact: true }).click();
  await expect(page).toHaveURL(/\/developers\/connect$/, { timeout: 30_000 });
  await expect(page.getByRole("link", { name: "Sign in to create an API key" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Create API key", exact: true })).toHaveCount(0);
});

test("creates a key for the selected owned agent without persisting it", async ({ page }) => {
  let posts = 0;
  await page.route("**/v1/**", async route => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith("/users/me")) return route.fulfill({ json: { id: "owner", email: "owner@example.test", display_name: "Owner" } });
    if (url.pathname.endsWith("/agents")) {
      expect(url.searchParams.get("mine")).toBe("true");
      return route.fulfill({ json: { items: [{ id: "agent-owned", display_name: "My API agent" }] } });
    }
    if (url.pathname.endsWith("/keys")) {
      expect(route.request().method()).toBe("POST");
      expect(route.request().postDataJSON()).toEqual({ agent_id: "agent-owned" });
      posts++;
      return route.fulfill({ status: 201, json: { key: "ancap_test_only_not_a_real_key" } });
    }
    return route.fulfill({ json: {} });
  });
  await page.goto("/developers/connect");
  const create = page.getByRole("button", { name: "Create API key", exact: true });
  await expect(create).toBeDisabled();
  await page.getByLabel("Choose your agent").selectOption("agent-owned");
  await create.click();
  await expect(page.getByText("ancap_test_only_not_a_real_key", { exact: true })).toBeVisible();
  await expect(create).toBeDisabled();
  expect(posts).toBe(1);
  const saved = await page.evaluate(() => JSON.stringify({ ...localStorage, ...sessionStorage }));
  expect(saved).not.toContain("ancap_test_only_not_a_real_key");
  await page.getByRole("button", { name: "Hide key" }).click();
  await expect(page.getByText("ancap_test_only_not_a_real_key", { exact: true })).toHaveCount(0);
});

test("key creation failures allow retry without reporting success", async ({ page }) => {
  await page.route("**/v1/**", route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/users/me")) return route.fulfill({ json: { id: "owner", email: "owner@example.test" } });
    if (path.endsWith("/agents")) return route.fulfill({ json: { items: [{ id: "agent-owned", display_name: "My API agent" }] } });
    if (path.endsWith("/keys")) return route.fulfill({ status: 403, json: { detail: "Forbidden agent" } });
    return route.fulfill({ json: {} });
  });
  await page.goto("/developers/connect");
  await page.getByLabel("Choose your agent").selectOption("agent-owned");
  await page.getByRole("button", { name: "Create API key", exact: true }).click();
  await expect(page.locator('p[role="alert"]')).toBeVisible();
  await expect(page.getByRole("button", { name: "Create API key", exact: true })).toBeEnabled();
  await expect(page.getByRole("button", { name: "Copy key" })).toHaveCount(0);
});
