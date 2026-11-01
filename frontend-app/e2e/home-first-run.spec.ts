import { expect, test } from "@playwright/test";
import { homeFirstRunByLang } from "../src/locales/homeFirstRun";

test.setTimeout(90_000);

test.beforeEach(async ({ page }) => {
  await page.route("**/v1/**", route => route.fulfill({ status: 401, json: { detail: "Sign in" } }));
});

for (const width of [1920, 1440, 768, 390]) {
  test(`homepage has one clear starting point at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Turn a task into a finished AI result.");
    const hero = page.locator("#product");
    const primary = hero.getByRole("link", { name: "Start your first workflow" });
    await expect(primary).toHaveAttribute("href", "/ai/run/token-risk-report");
    await expect(hero.getByRole("link", { name: "Explore workflows", exact: true })).toHaveAttribute("href", "/ai/workflows");
    await expect(hero.locator("figure")).toHaveCount(0);
    await expect(page.locator("#workflow-discovery article")).toHaveCount(3);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    expect(overflow).toBe(false);
    const cookies = page.getByRole("button", { name: "Necessary only", exact: true });
    if (await cookies.isVisible()) await cookies.click();
    await primary.evaluate(el => (el as HTMLElement).focus());
    await page.keyboard.press("Shift+Tab");
    await page.keyboard.press("Tab");
    await expect(primary).toBeFocused();
    expect(await primary.evaluate(el => getComputedStyle(el).outlineStyle)).toBe("solid");
    await page.locator("#homepage-title").click();
    await page.screenshot({ path: test.info().outputPath(`homepage-${width}.png`), fullPage: true });
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: test.info().outputPath(`hero-${width}.png`) });
    await page.locator("#first-workflow").screenshot({ path: test.info().outputPath(`recommended-${width}.png`) });
  });
}

test("homepage copy follows the selected language on mobile", async ({ page, context }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  for (const lang of ["en", "ru", "uk", "de", "zh-Hant"] as const) {
    await context.addCookies([{ name: "ancap-lang", value: lang, url: test.info().project.use.baseURL as string }]);
    await page.addInitScript(language => localStorage.setItem("ancap-lang-v3", language), lang);
    await page.goto("/");
    const c = homeFirstRunByLang[lang];
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(`${c.title} ${c.accent}`);
    await expect(page.locator("#first-workflow").getByRole("link", { name: c.startWorkflow })).toHaveAttribute("href", "/ai/run/token-risk-report");
    expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), lang).toBe(false);
  }
});

test("CTA uses existing analytics and reaches the guided workflow before auth", async ({ page }) => {
  await page.addInitScript(() => {
    (window as any).homeEvents = JSON.parse(sessionStorage.getItem("home-test-events") || "[]");
    window.addEventListener("ancap:analytics", event => {
      (window as any).homeEvents.push((event as CustomEvent).detail);
      sessionStorage.setItem("home-test-events", JSON.stringify((window as any).homeEvents));
    });
  });
  await page.goto("/");
  const cookies = page.getByRole("button", { name: "Necessary only", exact: true });
  await cookies.click();
  await page.locator("#product").getByRole("link", { name: "Start your first workflow" }).click();
  await expect(page).toHaveURL(/\/ai\/run\/token-risk-report$/, { timeout: 30_000 });
  expect(await page.evaluate(() => (window as any).homeEvents)).toEqual(expect.arrayContaining([
    expect.objectContaining({ name: "homepage_primary_cta_click", slug: "token-risk-report", placement: "hero" }),
  ]));
  await expect(page.getByText("Project name", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Sign in to run workflow", exact: true }).click();
  await expect(page).toHaveURL(/\/login\?next=%2Fai%2Frun%2Ftoken-risk-report$/);
  await page.locator("form").getByRole("link", { name: "Register", exact: true }).click();
  await expect(page).toHaveURL(/\/register\?next=%2Fai%2Frun%2Ftoken-risk-report$/);
  await expect(page.locator("form").getByRole("link", { name: "Login", exact: true })).toHaveAttribute("href", "/login?next=%2Fai%2Frun%2Ftoken-risk-report");
});

for (const mode of ["login", "register"] as const) {
  for (const backup of [false, true]) {
    test(`${mode} returns to the selected offer${backup ? " after backup acknowledgement" : ""}`, async ({ page }) => {
      let authenticated = false;
      await page.route("**/v1/**", route => {
        const path = new URL(route.request().url()).pathname;
        if (path.endsWith(mode === "register" ? "/auth/users" : "/auth/login")) {
          authenticated = true;
          return route.fulfill({ json: { access_token: "local-test-fixture", ...(backup ? { wallet_backup_mnemonic: "TEST FIXTURE — NOT A WALLET" } : {}) } });
        }
        if (path.endsWith("/users/me") && authenticated) return route.fulfill({ json: { id: "home-test", email: "home-test@example.com", display_name: "Homepage test" } });
        return route.fulfill({ status: 401, json: { detail: "Sign in" } });
      });
      await page.goto(`/${mode}?next=%2Fai%2Frun%2Ftoken-risk-report`);
      await page.getByLabel("Email", { exact: true }).fill("home-test@example.com");
      await page.getByLabel("Password", { exact: true }).fill("test-password-only");
      if (mode === "register") {
        await page.getByLabel("Display Name").fill("Homepage test");
        await page.locator('input[type="checkbox"]').first().check();
      }
      await page.getByRole("button", { name: mode === "register" ? "Register" : "Login", exact: true }).click();
      if (backup) await page.getByRole("button", { name: "I saved it", exact: true }).click();
      await expect(page).toHaveURL(/\/ai\/run\/token-risk-report$/);
      await expect(page.getByRole("button", { name: "Run workflow", exact: true })).toBeVisible();
    });
  }
}
