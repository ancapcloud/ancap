"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { Navigation } from "@/components/Navigation";
import { useLanguage } from "@/components/LanguageProvider";
import { WalletConnectCard } from "@/components/WalletConnectCard";
import { TurnstileWidget } from "@/components/TurnstileWidget";
import { TURNSTILE_ENABLED } from "@/lib/turnstile";
import { safeAuthReturn } from "@/lib/authReturn";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [walletMnemonic, setWalletMnemonic] = useState<string>("");
  const [turnstileToken, setTurnstileToken] = useState("");
  const [turnstileResetKey, setTurnstileResetKey] = useState(0);
  const [agreedLegal, setAgreedLegal] = useState(false);
  const { register } = useAuth();
  const { t } = useLanguage();
  const router = useRouter();
  const [nextHref, setNextHref] = useState("/dashboard");
  useEffect(() => {
    setNextHref(safeAuthReturn(new URLSearchParams(window.location.search).get("next")));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const referralCode =
        typeof window !== "undefined"
          ? new URLSearchParams(window.location.search).get("ref")?.trim() || ""
          : "";
      if (TURNSTILE_ENABLED && !turnstileToken) {
        throw new Error("Complete the captcha first");
      }
      if (!agreedLegal) {
        throw new Error("Please accept the User Agreement and Privacy Notice");
      }
      const mnemonic = await register(email, password, displayName, referralCode || undefined, turnstileToken);
      if (mnemonic) {
        setWalletMnemonic(mnemonic);
      } else {
        router.push(nextHref);
      }
    } catch (err: any) {
      setError(err.message || "Registration failed");
      setTurnstileToken("");
      setTurnstileResetKey((v) => v + 1);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navigation />
      <div
        className="relative z-10 flex min-h-[calc(100vh-80px)] items-center justify-center"
        style={{ padding: "24px" }}
      >
        <div className="card" style={{ maxWidth: "400px", width: "100%" }}>
          <div style={{ textAlign: "center", marginBottom: "32px" }}>
            <a href="/" style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text)", textDecoration: "none" }}>
              ANCAP
            </a>
            <h1 style={{ fontSize: "1.5rem", fontWeight: 600, marginTop: "16px", color: "var(--text)" }}>
              {t("nav.register")}
            </h1>
            <p style={{ marginTop: "12px", fontSize: "0.85rem", lineHeight: 1.5, color: "var(--text-muted)" }}>
              {t("auth.welcomeGrantNote")}{" "}
              <a href="/legal/welcome-grant" style={{ color: "var(--accent)" }}>
                {t("legal.welcomeGrantLink")}
              </a>
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: "20px" }}>
              <label
                htmlFor="display_name"
                style={{ display: "block", marginBottom: "8px", fontSize: "0.9rem", fontWeight: 500, color: "var(--text)" }}
              >
                {t("auth.displayName")}
              </label>
              <input
                id="display_name"
                type="text"
                autoComplete="nickname"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                required
                style={{
                  width: "100%",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid var(--border)",
                  background: "var(--bg)",
                  color: "var(--text)",
                  fontSize: "0.95rem",
                }}
              />
            </div>

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
                  background: "var(--bg)",
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
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                style={{
                  width: "100%",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid var(--border)",
                  background: "var(--bg)",
                  color: "var(--text)",
                  fontSize: "0.95rem",
                }}
              />
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "4px" }}>
                {t("auth.minPassword")}
              </div>
            </div>

            <TurnstileWidget
              siteKey={process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || ""}
              action="register"
              onTokenChange={setTurnstileToken}
              resetSignal={turnstileResetKey}
            />

            <label
              style={{
                display: "flex",
                gap: "10px",
                alignItems: "flex-start",
                marginBottom: "20px",
                fontSize: "0.85rem",
                lineHeight: 1.5,
                color: "var(--text-muted)",
              }}
            >
              <input
                type="checkbox"
                checked={agreedLegal}
                onChange={(e) => setAgreedLegal(e.target.checked)}
                required
                style={{ marginTop: 3 }}
              />
              <span>
                {t("legal.authAgreePrefix")}{" "}
                <a href="/legal/terms" style={{ color: "var(--accent)" }}>
                  {t("legal.termsLink")}
                </a>{" "}
                {t("legal.authAgreeAnd")}{" "}
                <a href="/legal/privacy" style={{ color: "var(--accent)" }}>
                  {t("legal.privacyLink")}
                </a>
                {t("legal.authAgreeSuffix")}{" "}
                <a href="/legal/risk" style={{ color: "var(--accent)" }}>
                  ({t("legal.riskLink")})
                </a>
              </span>
            </label>

            {error && (
              <div style={{
                padding: "12px",
                borderRadius: "8px",
                background: "rgba(239, 68, 68, 0.1)",
                color: "#ef4444",
                fontSize: "0.9rem",
                marginBottom: "20px",
              }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !agreedLegal}
              className="btn btn-primary"
              style={{ width: "100%", marginBottom: "16px" }}
            >
              {loading ? t("auth.creatingAccount") : t("nav.register")}
            </button>

            <div style={{ textAlign: "center", fontSize: "0.9rem", color: "var(--text-muted)" }}>
              {t("auth.haveAccount")}{" "}
              <a href={`/login?next=${encodeURIComponent(nextHref)}`} style={{ color: "var(--accent)", textDecoration: "none", fontWeight: 500 }}>
                {t("nav.login")}
              </a>
            </div>
          </form>

          <WalletConnectCard showContinue={false} />
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
    </>
  );
}
