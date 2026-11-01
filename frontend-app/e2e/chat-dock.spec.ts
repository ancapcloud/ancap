import { expect, test } from "@playwright/test";

test.setTimeout(60_000);

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem("ancap_cookie_consent_v1", JSON.stringify({ necessary: true, analytics: false, marketing: false })));
  await page.route("**/v1/**", route => route.fulfill({ status: 401, json: { detail: "Sign in" } }));
  await page.route("**/home-chat/status", route => route.fulfill({ json: { configured: true } }));
  await page.route("**/home-chat/messages", route => route.fulfill({ json: { reply: "Fixture reply shared between chat surfaces.", model: "test/fixture:free", label: "Fixture model" } }));
});

test("dock is available away from home and loads status only on open", async ({ page }) => {
  let statusCalls = 0;
  await page.route("**/home-chat/status", route => { statusCalls += 1; return route.fulfill({ json: { configured: true } }); });
  await page.goto("/projects");
  const launcher = page.getByRole("button", { name: "Ask ANCAP", exact: true });
  await expect(launcher).toHaveAttribute("aria-expanded", "false");
  expect(statusCalls).toBe(0);
  await launcher.click();
  await expect(page.getByTestId("dock-chat-input")).toBeEnabled();
  expect(statusCalls).toBe(1);
  await page.getByTestId("dock-chat-input").fill("A draft to keep");
  await page.getByRole("button", { name: "Minimize chat", exact: true }).click();
  await expect(launcher).toBeFocused();
  await launcher.click();
  await expect(page.getByTestId("dock-chat-input")).toHaveValue("A draft to keep");
  await page.keyboard.press("Escape");
  await expect(page.getByTestId("dock-chat")).toHaveCount(0);
  expect(statusCalls).toBe(1);
});

test("inline and floating chat share a conversation across navigation", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("home-chat-input").fill("Help me choose a workflow");
  await page.getByTestId("home-chat-send").click();
  await expect(page.locator("#ask")).toContainText("Fixture reply shared between chat surfaces.");
  await page.getByRole("button", { name: "Ask ANCAP", exact: true }).click();
  const dock = page.getByTestId("dock-chat");
  await expect(dock).toContainText("Help me choose a workflow");
  await expect(dock).toContainText("Fixture reply shared between chat surfaces.");
  await dock.getByRole("link", { name: "Workflows", exact: true }).click();
  await expect(page).toHaveURL(/\/ai\/workflows$/);
  await expect(dock).toContainText("Fixture reply shared between chat surfaces.");
  await dock.getByRole("button", { name: "New chat", exact: true }).click();
  await expect(dock).not.toContainText("Fixture reply shared between chat surfaces.");
});

test("dock fits mobile and supports fullscreen", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/login");
  await page.getByRole("button", { name: "Ask ANCAP", exact: true }).click();
  const dock = page.getByTestId("dock-chat");
  await expect(dock).toBeVisible();
  const rect = await dock.boundingBox();
  expect(rect && rect.x >= 0 && rect.x + rect.width <= 390 && rect.y >= 0 && rect.y + rect.height <= 844).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  await page.screenshot({ path: test.info().outputPath("chat-dock-mobile.png") });
  await page.getByTestId("dock-chat-fullscreen").click();
  await expect(dock).toHaveAttribute("aria-modal", "true");
  await page.keyboard.press("Escape");
  await expect(dock).toHaveAttribute("data-fullscreen", "false");
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({ path: test.info().outputPath("chat-dock-desktop.png") });
});
