"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Navigation } from "@/components/Navigation";
import { useAuth } from "@/components/AuthProvider";
import { useLanguage } from "@/components/LanguageProvider";
import { ApiError, flows } from "@/lib/api";

type FlowId = "flow1" | "flow2" | "flow3" | "simulation";

export default function FlowsPage() {
  const { t } = useLanguage();
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  const [running, setRunning] = useState<FlowId | null>(null);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, isLoading, router]);

  const quickLinks = useMemo(() => ([
    { href: "/agents", label: t("nav.agents") || "Agents" },
    { href: "/strategies", label: t("nav.strategies") || "Strategies" },
    { href: "/marketplace", label: t("nav.marketplace") || "Marketplace" },
    { href: "/orders", label: t("nav.orders") || "Orders" },
    { href: "/access", label: t("nav.access") || "Access" },
    { href: "/runs", label: "Runs" },
    { href: "/ledger", label: t("nav.ledger") || "Ledger" },
    { href: "/reputation", label: t("nav.reputation") || "Reputation" },
  ]), [t]);

  async function run(flowId: FlowId) {
    setRunning(flowId);
    setError(null);
    setResult(null);
    try {
      const payload =
        flowId === "simulation"
          ? { agents: 200, strategies_per_agent: 1, orders: 200, runs_per_order: 1, tick_every: 50 }
          : {};
      const r = await flows.run(flowId, payload, Date.now() % 1_000_000);
      setResult(r);
    } catch (e: unknown) {
      if (e instanceof ApiError && e.status === 403) {
        setError(t("flows.forbidden"));
      } else if (e instanceof ApiError && e.status === 404) {
        setError(t("flows.disabledInProduction"));
      } else {
        setError(e instanceof Error ? e.message : String(e));
      }
    } finally {
      setRunning(null);
    }
  }

  if (isLoading || !isAuthenticated) return null;

  return (
    <>
      <div className="min-h-screen">
        <Navigation />
        <div className="container" style={{ padding: "48px 24px" }}>
          <h1 style={{ fontSize: "2rem", fontWeight: 700, marginBottom: "12px", color: "var(--text)" }}>
            {t("nav.flows") || "Flows"}
          </h1>
          <p style={{ color: "var(--text-muted)", marginBottom: "16px" }}>
            {t("flows.subtitle")}
          </p>
          <div
            role="note"
            className="card"
            data-testid="flows-operator-notice"
            style={{ marginBottom: "28px", borderColor: "rgba(245, 158, 11, 0.45)", color: "var(--text-muted)", fontSize: "0.9rem" }}
          >
            {t("flows.operatorNotice")}
          </div>

          <div className="responsive-grid responsive-grid-3" style={{ marginBottom: "28px" }}>
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 12, color: "var(--text)" }}>Flow 1</div>
              <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: 16 }}>
                builder → strategy → listing → order → access → run → ledger
              </div>
              <button className="btn btn-primary" disabled={!!running} onClick={() => run("flow1")}>
                {running === "flow1" ? "Running..." : "Run Flow 1"}
              </button>
            </div>
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 12, color: "var(--text)" }}>Flow 2</div>
              <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: 16 }}>
                audit/review → reputation tick → risk gate blocks new runs
              </div>
              <button className="btn btn-primary" disabled={!!running} onClick={() => run("flow2")}>
                {running === "flow2" ? "Running..." : "Run Flow 2"}
              </button>
            </div>
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 12, color: "var(--text)" }}>Flow 3</div>
              <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: 16 }}>
                employer hires worker → deliverable version → run → reputation tick
              </div>
              <button className="btn btn-primary" disabled={!!running} onClick={() => run("flow3")}>
                {running === "flow3" ? "Running..." : "Run Flow 3"}
              </button>
            </div>
          </div>

          <div className="card" style={{ marginBottom: 28 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
              <div>
                <div style={{ fontWeight: 600, color: "var(--text)" }}>Simulation</div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
                  Generate 100–1000 agents worth of activity (configurable in backend runner).
                </div>
              </div>
              <button className="btn btn-ghost" disabled={!!running} onClick={() => run("simulation")}>
                {running === "simulation" ? "Running..." : "Run Simulation"}
              </button>
            </div>
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 20 }}>
            {quickLinks.map((l) => (
              <a key={l.href} href={l.href} className="btn btn-ghost" style={{ padding: "8px 12px" }}>
                {l.label}
              </a>
            ))}
          </div>

          {error && (
            <div className="card" style={{ borderColor: "rgba(255,0,0,0.35)" }}>
              <div style={{ fontWeight: 600, marginBottom: 8, color: "var(--text)" }}>Error</div>
              <pre style={{ margin: 0, whiteSpace: "pre-wrap", color: "var(--text-muted)" }}>{error}</pre>
            </div>
          )}

          {result && (
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 8, color: "var(--text)" }}>Result</div>
              <pre style={{ margin: 0, whiteSpace: "pre-wrap", color: "var(--text-muted)" }}>
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

