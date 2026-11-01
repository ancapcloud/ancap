import { expect, test } from "@playwright/test";

test.setTimeout(90_000);

for (const theme of ["dark", "light"] as const) {
  test(`shared surfaces, forms and navigation remain usable in ${theme} theme`, async ({ page }) => {
    await page.addInitScript(value => {
      localStorage.setItem("ancap-theme-v1", value);
      localStorage.setItem("ancap_cookie_consent_v1", JSON.stringify({ necessary: true, analytics: false, marketing: false }));
    }, theme);
    await page.route("**/v1/**", route => route.fulfill({ status: 401, json: { detail: "Sign in" } }));
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto("/projects");
    await expect(page.locator("html")).toHaveClass(new RegExp(theme));
    await expect(page.locator("#solution-areas article")).toHaveCount(6);
    expect(await page.locator("#solution-areas article").first().evaluate(el => getComputedStyle(el).backgroundImage)).toContain("linear-gradient");
    expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
    await page.screenshot({ path: test.info().outputPath(`projects-${theme}.png`) });

    await page.goto("/ai/workflows");
    await expect(page.getByRole("searchbox", { name: "Search workflows" })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/register");
    await expect(page.getByLabel("Email", { exact: true })).toBeVisible();
    const checkbox = await page.locator('input[type="checkbox"]').first().boundingBox();
    expect(checkbox?.width).toBe(17);
    expect(checkbox?.height).toBe(17);
    expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
    const brand = await page.locator('header a[href="/"]').first().boundingBox();
    const languages = await page.getByRole("radiogroup", { name: "Language" }).boundingBox();
    expect(brand && languages && brand.x + brand.width <= languages.x).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`registration-${theme}.png`) });

    await page.goto("/login");
    await expect(page.getByLabel("Password", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Open menu", exact: true }).click();
    await expect(page.getByRole("link", { name: "Workflows", exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  });
}
