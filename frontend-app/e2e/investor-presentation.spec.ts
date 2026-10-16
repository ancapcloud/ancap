import { test, expect, type BrowserContext } from "@playwright/test";
import { positioningByLang } from "../src/locales/positioning";
import { investorDocsByLang } from "../src/locales/investorDocs";
import { economyByLang } from "../src/locales/economy";
import { testProjectsByLang } from "../src/locales/testProjects";
import { testProjects } from "../src/lib/testProjects";
import { reviewTrustByLang } from "../src/locales/reviewTrust";
import type { Language } from "../src/locales/translations";

const supportedLanguages = ["en", "ru", "uk", "de", "zh-Hant"] as const;

async function setLanguage(context: BrowserContext, lang: Language) {
  await context.addCookies([{ name: "ancap-lang", value: lang, url: test.info().project.use.baseURL as string }]);
}

test.beforeEach(async ({ page }) => {
  // Read the current cookie on every navigation so looped locale checks cannot
  // race multiple initializers that captured different languages.
  await page.addInitScript(() => {
    const cookie = document.cookie.split("; ").find(value => value.startsWith("ancap-lang="));
    if (cookie) localStorage.setItem("ancap-lang-v3", decodeURIComponent(cookie.slice("ancap-lang=".length)));
  });
});

test("public presentation explains the workflow product in five languages", async ({ page, context }) => {
  for (const lang of supportedLanguages) {
    await setLanguage(context, lang);
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(positioningByLang[lang].title);
    await expect(page.getByLabel("Локальное время, погода AccuWeather и поддержка")).toHaveCount(0);
    await expect(page.locator("#people-ai-economy")).toBeVisible();
    await expect(page.locator("#smart-pay")).toBeVisible();
    await expect(page.getByRole("link", { name: `${positioningByLang[lang].smartPayCta} →`, exact: true }).first()).toHaveAttribute("href", "/payment-scanner");
    await expect(page.getByRole("link", { name: `${positioningByLang[lang].economyLink} →`, exact: true }).first()).toHaveAttribute("href", "/economy");
  }
});

test("investor and portfolio pages avoid the old completion claim", async ({ page, context }) => {
  await setLanguage(context, "en");
  await page.goto("/projects");
  await expect(page.locator("#solution-areas article")).toHaveCount(6);
  await expect(page.getByText("Final delivery complete — all roadmap waves shipped")).toHaveCount(0);
  await expect(page.locator('#test-projects a[href="/aeterna"]')).toBeVisible();
  await page.goto("/investors");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("A focused platform for AI workflow commerce");
  await expect(page.getByText(/metrics have not been supplied/)).toBeVisible();
  await expect(page.locator('main a[href="/proof-center"]')).toBeVisible();
});

test("catalog filters offers and has a usable empty state", async ({ page, context }) => {
  await setLanguage(context, "en");
  await page.goto("/ai/workflows");
  const search = page.getByRole("searchbox", { name: "Search workflows" });
  await search.fill("no-such-workflow-6d90");
  await expect(page.getByText("No matching workflows. Try another search.")).toBeVisible();
  await expect(page.locator("main article")).toHaveCount(0);
  await search.fill("");
  await page.getByRole("combobox", { name: "Solutions", exact: true }).selectOption("life");
  await expect(page.locator("#catalog-life")).toBeVisible();
  await expect(page.locator("#catalog-crypto")).toHaveCount(0);
});

test("People + AI and earnings stay localized and usable on mobile in five languages", async ({ page, context }) => {
  test.setTimeout(120_000);
  await page.setViewportSize({ width: 390, height: 844 });
  for (const lang of supportedLanguages) {
    await setLanguage(context, lang);
    const c = economyByLang[lang];
    for (const route of ["/", "/projects", "/investors"]) {
      await page.goto(route);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      const model = page.locator("#people-ai-economy");
      await expect(model.getByRole("heading", { level: 2, name: c.title, exact: true })).toBeVisible();
      await expect(model.getByText(c.limits, { exact: true })).toBeVisible();
      await expect(model.getByRole("link", { name: `${c.tests} →`, exact: true })).toHaveAttribute("href", "/economy");
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      expect(overflow, `${lang} ${route}`).toBe(false);
      const brand = await page.locator("header").first().locator('a[href="/"]').first().boundingBox();
      const languages = await page.getByRole("radiogroup", { name: "Language" }).boundingBox();
      expect(brand && languages && brand.x + brand.width <= languages.x, `${lang} ${route}: brand and language controls should not overlap`).toBe(true);

      if (route === "/projects") {
        const earnings = page.locator("#creator-earnings");
        await expect(earnings.getByRole("heading", { name: c.earnings, exact: true })).toBeVisible();
        await expect(earnings.getByText(c.assumptions, { exact: true })).toBeVisible();
        await expect(earnings.getByText(c.disclaimer, { exact: true })).toBeVisible();
        for (const field of ["price", "orders", "feePercent", "variableCost", "fixedCost"] as const) {
          await expect(earnings.getByLabel(c[field], { exact: true })).toBeVisible();
        }
        await expect(earnings.getByTestId("earnings-net")).toHaveText("700 ACP");
        const orders = earnings.getByLabel(c.orders, { exact: true });
        await orders.fill("0");
        await expect(earnings.getByTestId("earnings-net")).toHaveText("−50 ACP");
        await expect(earnings.getByText(c.loss, { exact: true })).toBeVisible();
        await orders.fill("-1");
        await expect(earnings.getByRole("status")).toHaveText(c.invalid);
        await expect(earnings.getByTestId("earnings-net")).toHaveCount(0);
        const tests = page.locator("#test-projects");
        await expect(tests.getByRole("heading", { name: testProjectsByLang[lang].title, exact: true })).toBeVisible();
        await expect(tests.getByText(testProjectsByLang[lang].disclosure, { exact: true })).toBeVisible();
      }
    }
  }
});

test("test projects present five AI scenarios and sample outputs with preserved source links", async ({ page, context }) => {
  await setLanguage(context, "en");
  await page.goto("/projects");
  const section = page.locator("#test-projects");
  const c = testProjectsByLang.en;
  await expect(section.locator("article")).toHaveCount(5);
  await expect(section.getByText(c.badge, { exact: true })).toHaveCount(5);
  await expect(section.getByText(c.disclosure, { exact: true })).toBeVisible();
  for (const project of testProjects) {
    const card = section.locator(`#test-project-${project.id}`);
    const copy = c.projects[project.id];
    await expect(card.getByRole("heading", { name: project.title, exact: true })).toBeVisible();
    for (const field of ["goal", "people", "ai", "deliverable"] as const) {
      await expect(card.getByText(c[field], { exact: true })).toBeVisible();
      await expect(card.getByText(copy[field], { exact: true })).toBeVisible();
    }
    await card.locator("summary").click();
    await expect(card.getByText(copy.sample, { exact: true })).toBeVisible();
    await expect(card.getByRole("link", { name: `${c.open} →`, exact: true })).toHaveAttribute("href", project.href);
  }
  for (const project of testProjects) {
    await expect(page.locator(`#solution-areas a[href="${project.href}"]`)).toHaveCount(0);
  }
});

test("test feedback saves locally, survives reload and stays isolated by project", async ({ page, context }) => {
  await setLanguage(context, "en");
  await page.goto("/projects");
  const c = reviewTrustByLang.en;
  const aeterna = page.getByTestId("test-feedback-aeterna");
  const galaxy = page.getByTestId("test-feedback-galaxy");
  const aeternaKey = "ancap:test-project-feedback:v1:aeterna";
  const galaxyKey = "ancap:test-project-feedback:v1:galaxy";
  const firstText = "Local test note: clarify the research evidence checklist.";
  const otherText = "Local test note: explain the infrastructure trust boundaries.";
  const revisedText = "Local test note revised after reading the sample outline.";
  const ratingLabel = (rating: number) => c.ratingChoice.replace("{rating}", String(rating));

  await expect(aeterna.getByText(c.localBadge, { exact: true })).toBeVisible();
  await expect(aeterna.getByText(c.localNote, { exact: true })).toBeVisible();
  await aeterna.getByRole("radio", { name: ratingLabel(4), exact: true }).check();
  await aeterna.getByLabel(c.comment, { exact: true }).fill(firstText);
  await aeterna.getByRole("button", { name: c.save, exact: true }).click();
  await expect(aeterna.getByText(c.savedTitle, { exact: true })).toBeVisible();
  await expect(aeterna.getByText(firstText, { exact: true })).toBeVisible();
  expect(await page.evaluate(key => JSON.parse(localStorage.getItem(key) ?? "null"), aeternaKey))
    .toMatchObject({ version: 1, rating: 4, text: firstText });

  await expect(galaxy.getByText(firstText, { exact: true })).toHaveCount(0);
  await expect(galaxy.getByLabel(c.comment, { exact: true })).toHaveValue("");
  await galaxy.getByRole("radio", { name: ratingLabel(2), exact: true }).check();
  await galaxy.getByLabel(c.comment, { exact: true }).fill(otherText);
  await galaxy.getByRole("button", { name: c.save, exact: true }).click();
  await expect(galaxy.getByText(otherText, { exact: true })).toBeVisible();
  await page.reload();
  await expect(aeterna.getByText(firstText, { exact: true })).toBeVisible();
  await expect(galaxy.getByText(otherText, { exact: true })).toBeVisible();

  await aeterna.getByRole("button", { name: c.edit, exact: true }).click();
  await expect(aeterna.getByLabel(c.comment, { exact: true })).toHaveValue(firstText);
  await aeterna.getByRole("radio", { name: ratingLabel(5), exact: true }).check();
  await aeterna.getByLabel(c.comment, { exact: true }).fill(revisedText);
  await aeterna.getByRole("button", { name: c.save, exact: true }).click();
  await expect(aeterna.getByText(revisedText, { exact: true })).toBeVisible();
  await expect(aeterna.getByText(firstText, { exact: true })).toHaveCount(0);
  expect(await page.evaluate(key => JSON.parse(localStorage.getItem(key) ?? "null"), aeternaKey))
    .toMatchObject({ version: 1, rating: 5, text: revisedText });

  await aeterna.getByRole("button", { name: c.remove, exact: true }).click();
  await expect(aeterna.getByText(c.deleted, { exact: true })).toBeVisible();
  expect(await page.evaluate(key => localStorage.getItem(key), aeternaKey)).toBeNull();
  expect(await page.evaluate(key => JSON.parse(localStorage.getItem(key) ?? "null"), galaxyKey))
    .toMatchObject({ version: 1, rating: 2, text: otherText });
  await page.reload();
  await expect(aeterna.getByLabel(c.comment, { exact: true })).toHaveValue("");
  await expect(aeterna.getByText(revisedText, { exact: true })).toHaveCount(0);
  await expect(galaxy.getByText(otherText, { exact: true })).toBeVisible();
});

test("research project heroes describe briefs instead of physical capabilities", async ({ page, context }) => {
  await setLanguage(context, "en");
  for (const route of ["/aeterna", "/cryo", "/saliva-rx", "/galaxy", "/lunar", "/stardust"]) {
    await page.goto(route);
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Research briefs");
    const offerChain = page.getByRole("complementary", { name: "Solutions" });
    await expect(offerChain.getByText("Buyer", { exact: true })).toBeVisible();
    await expect(offerChain.getByText("Receipt", { exact: true })).toBeVisible();
  }
});

test("investors page links budget and demo without inventing metrics", async ({ page, context }) => {
  await setLanguage(context, "en");
  await page.goto("/investors");
  await expect(page.getByRole("link", { name: /12-month budget/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /5-minute demo/i })).toBeVisible();
  await page.getByRole("link", { name: /12-month budget/i }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("12-month budget");
  await expect(page.getByText(/not a revenue forecast/i)).toBeVisible();
});

test("investor and test-project overviews support the light theme", async ({ page, context }) => {
  await setLanguage(context, "en");
  await page.addInitScript(() => localStorage.setItem("ancap-theme-v1", "light"));
  for (const route of ["/investors", "/projects"]) {
    await page.goto(route);
    await expect(page.locator("html")).toHaveClass(/light/);
    await expect(page.getByRole("heading", { level: 1 })).toHaveCSS("color", "rgb(15, 23, 42)");
    await expect(page.locator("#people-ai-economy").getByRole("heading", { name: economyByLang.en.title, exact: true })).toBeVisible();
    if (route === "/projects") await expect(page.locator("#test-project-aeterna")).toBeVisible();
  }
});

test("project offers link directly to the correct workflow or bundle", async ({ page }) => {
  await page.goto("/agency");
  await expect(page.locator('aside a[href="/ai/bundles/launch-pack"]')).toBeVisible();
  await page.goto("/markets");
  await expect(page.locator('aside a[href="/ai/run/market-direction-brief"]')).toBeVisible();
});

test("planned entities disclaimer is localized on investor and budget pages", async ({ page, context }) => {
  for (const lang of supportedLanguages) {
    await setLanguage(context, lang);
    await page.goto("/investors");
    await expect(page.locator("main").getByText(positioningByLang[lang].entitiesBody, { exact: true })).toBeVisible();
    await page.goto("/docs/investors/budget-12m");
    await expect(page.locator("article").getByText(investorDocsByLang[lang].budgetEntitiesBody, { exact: true })).toBeVisible();
  }
});
