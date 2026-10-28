import type { APIRequestContext, Page } from "@playwright/test";
import { randomUUID } from "node:crypto";

type UserData = {
  id: string;
  email: string;
  display_name: string;
};

type PasswordSessionOptions = {
  apiBase: string;
  displayName: string;
  emailPrefix: string;
  turnstileToken?: string;
  maxAttempts?: number;
};

type PasswordSessionResult = {
  token: string;
  userData: UserData;
};

function uniqueSuffix() {
  return randomUUID();
}

export async function createPasswordUserSession(
  request: APIRequestContext,
  { apiBase, displayName, emailPrefix, turnstileToken, maxAttempts = 3 }: PasswordSessionOptions,
): Promise<PasswordSessionResult> {
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const suffix = uniqueSuffix();
    const email = `${emailPrefix}_${suffix}@example.com`;
    const password = `pw_${suffix}`;
    const regPayload: Record<string, unknown> = { email, password, display_name: displayName };
    if (turnstileToken) regPayload.turnstile_token = turnstileToken;

    const reg = await request.post(`${apiBase}/auth/users`, { data: regPayload });
    if (!reg.ok()) {
      const regText = await reg.text();
      if (reg.status() === 400 && /email already registered/i.test(regText)) {
        continue;
      }
      throw new Error(`register failed: ${reg.status()} ${regText}`);
    }

    const created = await reg.json();
    const token = created.access_token as string | undefined;
    if (!token) {
      throw new Error("register succeeded without access token");
    }

    const me = await request.get(`${apiBase}/users/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!me.ok()) throw new Error(`me failed: ${me.status()} ${await me.text()}`);
    const meJson = await me.json();
    return {
      token,
      userData: {
        id: meJson.id,
        email: meJson.email,
        display_name: meJson.display_name || (meJson.email || "user").split("@")[0],
      },
    };
  }

  throw new Error(`register kept colliding on duplicate emails after ${maxAttempts} attempts`);
}

export async function seedAuthenticatedPage(
  page: Page,
  {
    baseUrl,
    apiBase,
    token,
    userData,
  }: {
    baseUrl: string;
    apiBase: string;
    token: string;
    userData: UserData;
  },
) {
  await page.addInitScript(
    ({ u }) => {
      localStorage.setItem("ancap_user", JSON.stringify(u));
    },
    { u: userData },
  );

  const authCookieTargets = Array.from(new Set([baseUrl, new URL(apiBase).origin]));
  await page.context().addCookies(
    authCookieTargets.map((url) => ({
      name: "ancap_token",
      value: token,
      url,
      httpOnly: true,
      secure: false,
      sameSite: "Strict" as const,
    })),
  );

  await page.route("**/users/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(userData),
    });
  });
}
