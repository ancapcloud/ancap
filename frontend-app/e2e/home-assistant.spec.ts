import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.route("**/v1/**", route => route.fulfill({ status: 401, json: { detail: "Sign in" } }));
});

test("AI connection and assistant follow the hero, with useful offline navigation", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/home-chat/status", route => route.fulfill({ json: { configured: false } }));
  await page.goto("/");
  await expect(page.locator("#ask textarea")).toBeDisabled();
  const ids = await page.locator("main section[id]").evaluateAll(nodes => nodes.map(node => node.id));
  expect(ids.slice(0, 3)).toEqual(["product", "connect-ai", "ask"]);
  await expect(page.locator("#ask").getByRole("link", { name: /Find a workflow/ })).toHaveAttribute("href", "/ai/workflows");
  await expect(page.locator("#ask").getByRole("link", { name: /How to earn/ })).toHaveAttribute("href", "/creators");
  await expect(page.locator("#ask").getByRole("status")).toContainText("Chat is currently unavailable");
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  await page.locator("#ask").screenshot({ path: test.info().outputPath("assistant-mobile.png") });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.locator("#ask").screenshot({ path: test.info().outputPath("assistant-desktop.png") });
});

test("assistant sends a message, pins the model, and supports accessible fullscreen", async ({ page }) => {
  await page.route("**/home-chat/status", route => route.fulfill({ json: { configured: true } }));
  await page.route("**/home-chat/messages", route => route.fulfill({ json: { reply: "Fixture response for UI verification.", model: "test/fixture:free", label: "Fixture model" } }));
  await page.goto("/");
  await page.getByRole("button", { name: "Necessary only", exact: true }).click();
  const input = page.getByTestId("home-chat-input");
  await input.fill("Help me find a workflow");
  await page.getByTestId("home-chat-send").click();
  await expect(page.locator("#ask")).toContainText("Fixture response for UI verification.");
  await expect(page.getByTestId("home-chat-model")).toHaveText("Fixture model");
  const expand = page.getByTestId("home-chat-fullscreen");
  await expand.click();
  await expect(page.getByRole("dialog", { name: "Ask ANCAP" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByTestId("home-chat")).toHaveAttribute("data-fullscreen", "false");
  await expect(expand).toBeFocused();
});

test("starter prompt copies successfully and resets confirmation on language change", async ({ page }) => {
  await page.addInitScript(() => Object.defineProperty(navigator, "clipboard", { value: { writeText: async (value: string) => { (window as any).copiedStarter = value; } } }));
  await page.goto("/");
  await page.getByRole("button", { name: "Necessary only", exact: true }).click();
  const connect = page.locator("#connect-ai");
  await connect.getByRole("button", { name: "Copy starter prompt", exact: true }).click();
  await expect(connect.getByRole("status")).toHaveText("Copied");
  expect(await page.evaluate(() => (window as any).copiedStarter)).toContain("https://ancap.cloud/connect.md");
  await page.getByRole("radio", { name: "DE", exact: true }).click();
  await expect(connect.getByRole("status")).toBeEmpty();
  await expect(connect.getByRole("button", { name: "Startanweisung kopieren", exact: true })).toBeVisible();
});
