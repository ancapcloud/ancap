"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { Navigation } from "@/components/Navigation";
import { useLanguage } from "@/components/LanguageProvider";
import { WalletConnectCard } from "@/components/WalletConnectCard";
import { TurnstileWidget } from "@/components/TurnstileWidget";
import { TURNSTILE_ENABLED } from "@/lib/turnstile";
import { safeAuthReturn } from "@/lib/authReturn";

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [recoveryHint, setRecoveryHint] = useState<"forgot-password" | "">("");
  const [loading, setLoading] = useState(false);
  const [forgotLoading, setForgotLoading] = useState(false);
  const [walletMnemonic, setWalletMnemonic] = useState<string>("");
  const [turnstileToken, setTurnstileToken] = useState("");
  const [turnstileResetKey, setTurnstileResetKey] = useState(0);
  const { login, requestPasswordReset } = useAuth();
  const { t } = useLanguage();
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextHref = useMemo(() => {
    const raw = searchParams?.get("next")?.trim() || "";
    return safeAuthReturn(raw);
  }, [searchParams]);
  const recoveryTarget = useMemo(
    () => nextHref.startsWith("/wallet/acp") && nextHref.includes("#password-security"),
    [nextHref],
  );
  const submitLabel = recoveryTarget ? t("auth.continueToWalletRecovery") : t("nav.login");
  const submitLoadingLabel = recoveryTarget ? t("auth.openingWalletRecovery") : t("auth.loggingIn");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setInfo("");
    setRecoveryHint("");
    setLoading(true);

    try {
      if (TURNSTILE_ENABLED && !turnstileToken) {
        throw new Error(t("auth.completeCaptcha"));
      }
      const mnemonic = await login(email, password, turnstileToken);
      if (mnemonic) {
        setWalletMnemonic(mnemonic);
      } else {
        router.push(nextHref);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Login failed";
      const lower = message.toLowerCase();
      setError(
        lower.includes("failed to fetch") || lower.includes("could not reach the ancap api")
          ? "Could not reach the ANCAP API. Check your connection or try again shortly."
          : message,
      );
      setTurnstileToken("");
      setTurnstileResetKey((v) => v + 1);
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    setError("");
    setInfo("");
    setRecoveryHint("");
    setForgotLoading(true);
    try {
      if (!email.trim()) {
        throw new Error(t("auth.enterEmailFirst"));
      }
      if (TURNSTILE_ENABLED && !turnstileToken) {
        throw new Error(t("auth.completeCaptcha"));
      }
      await requestPasswordReset(email.trim(), turnstileToken);
      setInfo(t("auth.resetLinkSent"));
      setRecoveryHint("forgot-password");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : t("auth.resetFailed");
      setError(message);
      setTurnstileToken("");
      setTurnstileResetKey((v) => v + 1);
    } finally {
      setForgotLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg)]">
      <Navigation />
      <div
        className="relative z-10 flex min-h-[calc(100vh-80px)] items-center justify-center"
        style={{ padding: "24px" }}
      >
        <div className="card" style={{ maxWidth: "400px", width: "100%" }}>
          <div style={{ textAlign: "center", marginBottom: "32px" }}>
            <Link href="/" style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text)", textDecoration: "none" }}>
              ANCAP
            </Link>
            <h1 style={{ fontSize: "1.5rem", fontWeight: 600, marginTop: "16px", color: "var(--text)" }}>{t("nav.login")}</h1>
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: "20px" }}>
              <label
                htmlFor="email"
                style={{ display: "block", marginBottom: "8px", fontSize: "0.9rem", fontWeight: 500, color: "var(--text)" }}
              >
                {t("auth.email")}
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                style={{
                  width: "100%",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid var(--border)",
                  background: "var(--bg-card)",
                  color: "var(--text)",
                  fontSize: "0.95rem",
                }}
              />
            </div>

            <div style={{ marginBottom: "24px" }}>
              <label
                htmlFor="password"
                style={{ display: "block", marginBottom: "8px", fontSize: "0.9rem", fontWeight: 500, color: "var(--text)" }}
              >
                {t("auth.password")}
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={{
                  width: "100%",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid var(--border)",
                  background: "var(--bg-card)",
                  color: "var(--text)",
                  fontSize: "0.95rem",
                }}
              />
            </div>

            <TurnstileWidget
              siteKey={process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || ""}
              action="login"
              onTokenChange={setTurnstileToken}
              resetSignal={turnstileResetKey}
            />

            {error && (
              <div
                style={{
                  padding: "12px",
                  borderRadius: "8px",
                  background: "rgba(239, 68, 68, 0.1)",
                  color: "#ef4444",
                  fontSize: "0.9rem",
                  marginBottom: "20px",
                }}
              >
                {error}
              </div>
            )}

            {info && (
              <div
                style={{
                  padding: "12px",
                  borderRadius: "8px",
                  background: "rgba(52, 211, 153, 0.1)",
                  color: "#86efac",
                  fontSize: "0.9rem",
                  marginBottom: "20px",
                }}
              >
                {info}
              </div>
            )}

            {recoveryTarget && (
              <div
                style={{
                  padding: "12px",
                  borderRadius: "8px",
                  background: "rgba(245,158,11,0.12)",
                  color: "#fbbf24",
                  fontSize: "0.9rem",
                  marginBottom: "20px",
                  lineHeight: 1.6,
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: "8px" }}>ACP wallet recovery login</div>
                <div>You are signing in to reach the safe password rotation section for an ACP-wallet account.</div>
                <div>After login, ANCAP will open the ACP wallet and focus the <strong>Password &amp; wallet secret</strong> block.</div>
                <div>Use your current password there to rotate it safely and re-encrypt the wallet secret.</div>
              </div>
            )}

            {recoveryHint === "forgot-password" && (
              <div
                style={{
                  padding: "12px",
                  borderRadius: "8px",
                  background: "rgba(245,158,11,0.12)",
                  color: "#fbbf24",
                  fontSize: "0.9rem",
                  marginBottom: "20px",
                  lineHeight: 1.6,
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: "8px" }}>ACP wallet recovery note</div>
                <div>If this account has an ACP wallet, email-only recovery may be unavailable.</div>
                <div>Use wallet sign-in below if your EVM wallet is already linked, or sign in with the current password.</div>
                <div>After login you will be sent straight to the ACP wallet password rotation section.</div>
                <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginTop: "12px" }}>
                  <Link href="/login?next=/wallet/acp%23password-security" className="btn btn-ghost">Open wallet recovery login</Link>
                  <Link href="/wallet/acp#password-security" className="btn btn-ghost">Open ACP wallet</Link>
                </div>
              </div>
            )}

            <button type="submit" disabled={loading} className="btn btn-primary" style={{ width: "100%", marginBottom: "12px" }}>
              {loading ? submitLoadingLabel : submitLabel}
            </button>

            <button
              type="button"
              disabled={forgotLoading || loading}
              className="btn btn-ghost"
              style={{ width: "100%", marginBottom: "16px" }}
              onClick={() => void handleForgotPassword()}
            >
              {forgotLoading ? "Sending reset link..." : "Forgot password?"}
            </button>

            <div style={{ textAlign: "center", fontSize: "0.9rem", color: "var(--text-muted)" }}>
              {t("auth.noAccount")}{" "}
              <Link href={`/register?next=${encodeURIComponent(nextHref)}`} style={{ color: "var(--accent)", textDecoration: "none", fontWeight: 500 }}>
                {t("nav.register")}
              </Link>
              <div style={{ marginTop: 8, fontSize: "0.8rem" }}>
                {t("auth.welcomeGrantNote")}{" "}
                <Link href="/legal/welcome-grant" style={{ color: "var(--accent)", textDecoration: "none" }}>
                  {t("legal.welcomeGrantLink")}
                </Link>
              </div>
            </div>
          </form>

          <WalletConnectCard
            continueHref={nextHref}
            continueLabel={recoveryTarget ? "Continue to wallet recovery" : undefined}
            turnstileToken={turnstileToken}
            turnstileRequired={TURNSTILE_ENABLED}
            turnstileErrorMessage="Complete the captcha to continue."
            onConnected={() => {
              setError("");
              setInfo("");
            }}
            onAuthFailure={() => {
              setTurnstileToken("");
              setTurnstileResetKey((v) => v + 1);
            }}
          />
        </div>
      </div>

      {walletMnemonic && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.65)",
            display: "grid",
            placeItems: "center",
            zIndex: 200,
            padding: "16px",
          }}
        >
          <div className="card" style={{ maxWidth: "760px", width: "100%" }}>
            <h2 style={{ marginTop: 0, marginBottom: "10px", fontSize: "1.25rem", fontWeight: 700 }}>
              Save your ACP wallet seed phrase
            </h2>
            <p style={{ marginTop: 0, color: "var(--text-muted)", lineHeight: 1.6 }}>
              This phrase is shown only once. Write it down offline. If you lose it, wallet recovery is impossible.
            </p>
            <div
              style={{
                marginTop: "12px",
                border: "1px solid var(--border)",
                borderRadius: "10px",
                padding: "14px",
                background: "var(--bg)",
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
                lineHeight: 1.8,
                wordBreak: "break-word",
              }}
            >
              {walletMnemonic}
            </div>
            <div style={{ display: "flex", gap: "10px", marginTop: "14px", justifyContent: "flex-end" }}>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => navigator.clipboard?.writeText(walletMnemonic)}
              >
                Copy phrase
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => {
                  setWalletMnemonic("");
                  router.push(nextHref);
                }}
              >
                I saved it
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
