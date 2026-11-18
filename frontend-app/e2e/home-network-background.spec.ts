import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.route("**/v1/**", route => route.fulfill({ status: 401, json: { detail: "Sign in" } }));
});

for (const theme of ["dark", "light"] as const) {
for (const width of [1440, 390]) {
  test(`homepage network draws and animates at ${width}px in ${theme} mode`, async ({ page }) => {
    await page.addInitScript(value => localStorage.setItem("ancap-theme-v1", value), theme);
    await page.setViewportSize({ width, height: 900 });
    await page.emulateMedia({ reducedMotion: "no-preference" });
    await page.goto("/");
    await expect(page.locator("html")).toHaveClass(new RegExp(theme));
    const canvas = page.locator("canvas#network");
    await expect(canvas).toBeVisible();
    await expect(canvas.locator("..")).toHaveCSS("pointer-events", "none");
    await expect.poll(() => canvas.evaluate(el => {
      const image = (el as HTMLCanvasElement).getContext("2d")!.getImageData(0, 0, (el as HTMLCanvasElement).width, (el as HTMLCanvasElement).height);
      return image.data.some((value, index) => index % 4 === 3 && value > 0);
    })).toBe(true);
    const firstFrame = await canvas.evaluate(el => (el as HTMLCanvasElement).toDataURL());
    await expect.poll(() => canvas.evaluate(el => (el as HTMLCanvasElement).toDataURL())).not.toBe(firstFrame);
    const primary = page.locator("#product").getByRole("link", { name: "Start your first workflow" });
    await expect(primary).toHaveAttribute("href", "/ai/run/token-risk-report");
    await primary.click({ trial: true });
    const hero = page.locator("#product");
    const visibleHero = await hero.screenshot({ animations: "disabled" });
    await canvas.evaluate(el => { el.style.visibility = "hidden"; });
    const hiddenHero = await hero.screenshot({ animations: "disabled" });
    await canvas.evaluate(el => { el.style.visibility = ""; });
    expect(visibleHero.equals(hiddenHero), "network pixels must be visible above the homepage background").toBe(false);
    await page.screenshot({ path: test.info().outputPath(`network-home-${theme}-${width}.png`) });
  });
}
}

test("homepage network stays static with reduced motion and resumes when enabled", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const canvas = page.locator("canvas#network");
  await expect(canvas).toBeVisible();
  await expect.poll(() => canvas.evaluate(el => {
    const context = (el as HTMLCanvasElement).getContext("2d")!;
    return context.getImageData(0, 0, (el as HTMLCanvasElement).width, (el as HTMLCanvasElement).height).data.some((value, index) => index % 4 === 3 && value > 0);
  })).toBe(true);
  const firstFrame = await canvas.evaluate(el => (el as HTMLCanvasElement).toDataURL());
  await page.evaluate(() => new Promise<void>(resolve => {
    let remaining = 6;
    const next = () => --remaining ? requestAnimationFrame(next) : resolve();
    requestAnimationFrame(next);
  }));
  expect(await canvas.evaluate(el => (el as HTMLCanvasElement).toDataURL())).toBe(firstFrame);
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await expect.poll(() => canvas.evaluate(el => (el as HTMLCanvasElement).toDataURL())).not.toBe(firstFrame);
});
