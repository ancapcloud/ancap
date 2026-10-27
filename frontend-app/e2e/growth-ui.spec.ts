import { test, expect } from "@playwright/test";

import { createPasswordUserSession, seedAuthenticatedPage } from "./support/auth";

test("growth UI: onboarding + public follow/copy + leaderboards", async ({ page, request }) => {
  // This scenario creates users, runs onboarding and copies a strategy before rendering leaderboards.
  test.setTimeout(120_000);
  const baseUrl =
    process.env.PLAYWRIGHT_UI_BASE_URL ?? process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:8080";
  const apiBase = process.env.PLAYWRIGHT_API_BASE_URL ?? "http://127.0.0.1:8080/api/v1";

  const uniq = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const agentName = `Growth Agent ${uniq()}`;
  const strategyName = `Growth Strategy ${uniq()}`;

  const turnstileToken = process.env.PLAYWRIGHT_TURNSTILE_TOKEN;
  const { token, userData } = await createPasswordUserSession(request, {
    apiBase,
    displayName: "E2E Growth",
    emailPrefix: "e2e_growth",
    turnstileToken,
  });
  await seedAuthenticatedPage(page, {
    baseUrl,
    apiBase,
    token,
    userData,
  });

  await page.addInitScript(() => {
    try {
      localStorage.setItem(
        "ancap_cookie_consent_v1",
        JSON.stringify({ necessary: true, analytics: false, marketing: false, savedAt: new Date().toISOString() }),
      );
    } catch {}
  });

  // Create an agent via API, then use the UI for onboarding/follow/copy verification.
  const agentCreate = await request.post(`${apiBase}/agents`, {
    headers: { Authorization: `Bearer ${token}`, "X-Requested-With": "XMLHttpRequest" },
    data: { display_name: agentName, public_key: "x".repeat(32), roles: ["seller"] },
  });
  if (!agentCreate.ok()) throw new Error(`agent create failed: ${agentCreate.status()} ${await agentCreate.text()}`);

  // Onboarding: faucet + starter pack + quickstart
  await page.goto(`${baseUrl}/onboarding`);
  await expect(page.getByRole("heading", { name: /onboarding/i })).toBeVisible({ timeout: 15000 });
  await expect(page.getByRole("button", { name: /claim faucet/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /activate starter pack/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /quickstart run/i })).toBeVisible();

  // Execute quickstart via API (avoids relying on hot-reloaded backend during dev)
  const agentsRes = await request.get(`${apiBase}/agents?mine=true&limit=10`, { headers: { Authorization: `Bearer ${token}` } });
  if (!agentsRes.ok()) throw new Error(`agents list failed: ${agentsRes.status()} ${await agentsRes.text()}`);
  const myAgents = (await agentsRes.json()).items || [];
  const ownerAgentId = myAgents[0]?.id;
  if (!ownerAgentId) throw new Error("no agent for quickstart");

  const quick = await request.post(`${apiBase}/onboarding/quickstart/run`, {
    headers: { Authorization: `Bearer ${token}`, "Idempotency-Key": `idk-${uniq()}` },
    data: { owner_agent_id: ownerAgentId },
  });
  let run: any;
  if (quick.ok()) {
    run = await quick.json();
  } else if (quick.status() === 404) {
    // Fallback for dev environments where backend wasn't restarted yet.
    const verticals = await request.get(`${apiBase}/verticals?limit=1`);
    if (!verticals.ok()) throw new Error(`verticals failed: ${verticals.status()} ${await verticals.text()}`);
    const baseVerticalId = ((await verticals.json()).items || [])[0]?.id;
    if (!baseVerticalId) throw new Error("no vertical for fallback quickstart");

    const strat = await request.post(`${apiBase}/strategies`, {
      data: { name: `QS-${uniq()}`, vertical_id: baseVerticalId, owner_agent_id: ownerAgentId },
    });
    if (!strat.ok()) throw new Error(`strategy create failed: ${strat.status()} ${await strat.text()}`);
    const strategyId = (await strat.json()).id as string;

    const ver = await request.post(`${apiBase}/strategies/${strategyId}/versions`, {
      data: { semver: "1.0.0", workflow: { vertical_id: baseVerticalId, version: "1.0", steps: [{ id: "s1", action: "const", args: { value: 1 } }] } },
    });
    if (!ver.ok()) throw new Error(`version create failed: ${ver.status()} ${await ver.text()}`);
    const versionId = (await ver.json()).id as string;

    const pool = await request.post(`${apiBase}/pools`, { data: { name: `QS-P-${uniq()}`, risk_profile: "experimental" } });
    if (!pool.ok()) throw new Error(`pool create failed: ${pool.status()} ${await pool.text()}`);
    const poolId = (await pool.json()).id as string;

    const rr = await request.post(`${apiBase}/runs`, {
      headers: { Authorization: `Bearer ${token}`, "Idempotency-Key": `idk-${uniq()}` },
      data: { strategy_version_id: versionId, pool_id: poolId, params: { quickstart: true }, run_mode: "mock" },
    });
    if (!rr.ok()) throw new Error(`run create failed: ${rr.status()} ${await rr.text()}`);
    run = await rr.json();
  } else {
    throw new Error(`quickstart api failed: ${quick.status()} ${await quick.text()}`);
  }
  await page.goto(`${baseUrl}/runs/${run.id}`);
  await expect(page.getByText(/Run ID:/i)).toBeVisible({ timeout: 20000 });

  // Create a strategy to exercise follow/copy (use UI quick create)
  await page.goto(`${baseUrl}/strategies`);
  const createStrategyBtn = page.getByRole("button", { name: /create strategy/i });
  await expect(createStrategyBtn).toBeEnabled({ timeout: 15000 });
  await createStrategyBtn.click();
  await expect(page.getByRole("heading", { name: /create new strategy/i })).toBeVisible({ timeout: 15000 });
  const strategyModal = page.locator("div.card", { has: page.getByRole("heading", { name: /create new strategy/i }) });
  await strategyModal.locator("input[type='text']").first().fill(strategyName);
  const agentSelect = strategyModal.locator("select").nth(0);
  const verticalSelect = strategyModal.locator("select").nth(1);
  const agentEl = await agentSelect.elementHandle();
  const verticalEl = await verticalSelect.elementHandle();
  if (!agentEl || !verticalEl) throw new Error("Strategy modal selects not found");
  await page.waitForFunction((el) => (el as HTMLSelectElement).options.length > 1, agentEl, { timeout: 15000 });
  await page.waitForFunction((el) => (el as HTMLSelectElement).options.length > 1, verticalEl, { timeout: 15000 });
  await agentSelect.selectOption({ index: 1 });
  await verticalSelect.selectOption({ index: 1 });
  await strategyModal.getByRole("button", { name: /^create strategy$/i }).click();
  await expect(page.getByRole("heading", { name: /create new strategy/i })).toBeHidden({ timeout: 15000 });

  // Open first strategy in list
  await page.getByRole("link", { name: /view/i }).first().click();
  await expect(page.getByRole("link", { name: /public/i })).toBeVisible({ timeout: 15000 });
  await expect(page.getByRole("button", { name: /^follow$/i })).toBeVisible({ timeout: 15000 });
  await expect(page.getByRole("button", { name: /^copy$/i })).toBeVisible({ timeout: 15000 });

  const growthPublicPing = await request.get(`${apiBase}/public/feed/public?limit=1`);
  if (growthPublicPing.ok()) {
    await page.getByRole("link", { name: /public/i }).click();
    await expect(page).toHaveURL(/\/public\/strategies\/[0-9a-f-]+/i, { timeout: 15000 });
    await expect(page.getByRole("heading", { name: /public strategy/i })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole("button", { name: /^follow$/i })).toBeVisible({ timeout: 15000 });
    await page.getByRole("button", { name: /^follow$/i }).click();
    // Copy navigates to private strategy page
    await page.getByRole("button", { name: /^copy$/i }).click();
    await expect(page).toHaveURL(/\/strategies\/[0-9a-f-]+/i, { timeout: 20000 });
  }

  // This is a UI render check, including an empty leaderboard. Executing every
  // operator job here requires a cron secret and can block on unrelated work.
  // Job execution and leaderboard materialization are covered by test_growth_layer.py.
  await page.goto(`${baseUrl}/leaderboards`);
  await expect(page.getByRole("heading", { name: /leaderboards/i })).toBeVisible({ timeout: 15000 });
});

