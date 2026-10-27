"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { useLanguage } from "@/components/LanguageProvider";
import { Navigation } from "@/components/Navigation";
import { ApiError, workflowStore } from "@/lib/api";
import { topWorkflowsByCurrency } from "@/lib/revenueAnalytics";

const DAYS_OPTIONS = [
  { label: "7 days", value: 7 },
  { label: "30 days", value: 30 },
  { label: "90 days", value: 90 },
];

function BarChart({ data, label, maxValue }: { data: { label: string; value: number; color?: string }[]; label: string; maxValue: number }) {
  if (!data.length) return null;
  return (
    <div className="space-y-2">
      {data.map((item) => (
        <div key={item.label} className="flex items-center gap-3">
          <span className="text-xs w-24 text-right truncate">{item.label}</span>
          <div className="flex-1 bg-[var(--border)] rounded h-6 overflow-hidden">
            <div
              className="h-full rounded transition-all duration-300"
              style={{
                width: maxValue > 0 ? `${Math.max((item.value / maxValue) * 100, 1)}%` : "1%",
                backgroundColor: item.color || "var(--accent)",
              }}
            />
          </div>
          <span className="text-xs w-20 font-mono">{item.value.toLocaleString()}</span>
        </div>
      ))}
    </div>
  );
}
function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    captured: "bg-green-900/50 text-green-400 border-green-800",
    reserved: "bg-yellow-900/50 text-yellow-400 border-yellow-800",
    refunded: "bg-red-900/50 text-red-400 border-red-800",
    failed: "bg-red-900/50 text-red-400 border-red-800",
    requires_payment: "bg-blue-900/50 text-blue-400 border-blue-800",
    cancelled: "bg-gray-800/50 text-gray-400 border-gray-700",
  };
  const cls = colors[status] || "bg-gray-800/50 text-gray-400 border-gray-700";
  return <span className={`px-2 py-0.5 rounded text-xs border ${cls}`}>{status}</span>;
}

export default function AnalyticsPage() {
  const { t } = useLanguage();
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [days, setDays] = useState(30);
  const [revenue, setRevenue] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string>("");
  const [exportError, setExportError] = useState<string>("");

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, isLoading, router]);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await workflowStore.revenueSummary(days);
      setRevenue(data);
    } catch (e: any) {
      if (e instanceof ApiError && e.status === 403) {
        setError("Admin access required for workflow revenue analytics.");
      } else if (e instanceof ApiError && e.status === 503) {
        setError("Workflow revenue analytics are not configured for admin access yet.");
      } else {
        setError(e?.message || String(e));
      }
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    if (isAuthenticated) void loadData();
  }, [isAuthenticated, loadData]);

  const handleExportCsv = useCallback(async () => {
    setExporting(true);
    setExportError("");
    try {
      const blob = await workflowStore.revenueExportCsv(days);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `workflow-revenue-${days}d.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      if (e instanceof ApiError && e.status === 403) {
        setExportError("Admin access required to export workflow revenue.");
      } else if (e instanceof ApiError && e.status === 503) {
        setExportError("Platform admin access is not configured on the API server.");
      } else {
        setExportError(e?.message || String(e));
      }
    } finally {
      setExporting(false);
    }
  }, [days]);

  if (isLoading || !isAuthenticated) return null;

  const capturedTotals = (revenue?.totals || []).filter((t: any) => t.status === "captured");
  const grossByCurrency: Record<string, number> = {};
  for (const ct of capturedTotals) {
    grossByCurrency[ct.currency] = (grossByCurrency[ct.currency] || 0) + parseFloat(ct.amount);
  }

  const marginTotals: Record<string, number> = {};
  for (const m of revenue?.estimated_margin_totals || []) {
    marginTotals[m.currency] = parseFloat(m.amount);
  }

  const costTotals: Record<string, number> = {};
  for (const c of revenue?.estimated_cost_totals || []) {
    costTotals[c.currency] = parseFloat(c.amount);
  }

  const referralTotals: Record<string, number> = {};
  for (const r of revenue?.referral_commission_totals || []) {
    referralTotals[r.currency] = parseFloat(r.amount);
  }

  const runStatusCounts: Record<string, number> = (revenue?.run_status_counts as Record<string, number> | undefined) || {};
  const paymentStatusCounts: Record<string, number> = (revenue?.payment_status_counts as Record<string, number> | undefined) || {};
  const totalRuns = Object.values(runStatusCounts).reduce((a: number, b: number) => a + b, 0);
  const completedRuns = runStatusCounts["completed"] || 0;

  const skuGroups = topWorkflowsByCurrency(revenue?.skus || []);
  const topSkus = skuGroups.flatMap((group) => group.items);

  const currencyList = Array.from(new Set([
    ...Object.keys(grossByCurrency), ...Object.keys(marginTotals),
    ...Object.keys(costTotals), ...Object.keys(referralTotals),
  ])).sort();

  const runStatusData = Object.entries(runStatusCounts).map(([status, count]) => ({
    label: status,
    value: count as number,
    color: status === "completed" ? "#00d4aa" : status === "failed" ? "#ef4444" : "#6b7280",
  }));

  const paymentStatusData = Object.entries(paymentStatusCounts).map(([status, count]) => ({
    label: status,
    value: count as number,
  }));


  return (
    <>
      <Navigation />
      <main className="relative z-10 max-w-6xl mx-auto px-4 py-8 space-y-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <h1 className="text-2xl font-bold">Analytics</h1>
            <p className="text-sm opacity-60 mt-1">
              Workflow revenue · {revenue?.window_days || days}d window
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {DAYS_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setDays(opt.value)}
                className={`px-3 py-1.5 rounded text-sm border transition ${
                  days === opt.value
                    ? "border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)]"
                    : "border-[var(--border)] hover:border-[var(--accent)]"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {loading && (
          <div className="text-center py-16 opacity-60">Loading analytics...</div>
        )}

        {error && (
          <div className="rounded-lg border border-red-800 bg-red-900/20 p-4 text-red-400 text-sm">
            {error}
          </div>
        )}

        {!loading && !error && revenue && (
          <>
            <p className="text-sm opacity-60" role="note">
              Internal ledger captures and estimated costs. Test or internal credits may be included;
              these figures do not establish external customer revenue. Currencies are shown separately.
            </p>
            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {currencyList.length === 0 ? (
                <div className="col-span-4 text-center py-8 opacity-50">
                  No revenue data in this window
                </div>
              ) : (
                currencyList.map((curr) => (
                  <div key={curr} className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4 space-y-1">
                    <div className="text-xs opacity-60 uppercase tracking-wider">Gross Captured</div>
                    <div className="text-2xl font-mono font-bold text-[var(--accent)]">
                      {(grossByCurrency[curr] || 0).toFixed(2)}
                    </div>
                    <div className="text-xs opacity-60">{curr}</div>
                  </div>
                ))
              )}
              <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4 space-y-1">
                <div className="text-xs opacity-60 uppercase tracking-wider">Est. Margin</div>
                <div className="text-2xl font-mono font-bold">
                  {Object.entries(marginTotals).map(([currency, amount]) => (
                    <div key={currency}>{amount.toFixed(2)} <span className="text-xs opacity-60">{currency}</span></div>
                  ))}
                  {Object.keys(marginTotals).length === 0 && <span>—</span>}
                </div>
              </div>
              <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4 space-y-1">
                <div className="text-xs opacity-60 uppercase tracking-wider">Est. LLM Cost</div>
                <div className="text-2xl font-mono font-bold text-orange-400">
                  {Object.entries(costTotals).map(([currency, amount]) => (
                    <div key={currency}>{amount.toFixed(2)} <span className="text-xs opacity-60">{currency}</span></div>
                  ))}
                  {Object.keys(costTotals).length === 0 && <span>—</span>}
                </div>
              </div>
              <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4 space-y-1">
                <div className="text-xs opacity-60 uppercase tracking-wider">Referral Paid</div>
                <div className="text-2xl font-mono font-bold text-blue-400">
                  {Object.entries(referralTotals).map(([currency, amount]) => (
                    <div key={currency}>{amount.toFixed(2)} <span className="text-xs opacity-60">{currency}</span></div>
                  ))}
                  {Object.keys(referralTotals).length === 0 && <span>—</span>}
                </div>
              </div>
            </div>

            {/* Run & Payment Status */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-5">
                <h3 className="font-semibold mb-4">Run Status ({totalRuns} total)</h3>
                {totalRuns > 0 ? (
                  <BarChart
                    data={runStatusData}
                    label="Runs"
                    maxValue={Math.max(...runStatusData.map((d) => d.value), 1)}
                  />
                ) : (
                  <p className="text-sm opacity-50">No runs in this window</p>
                )}
              </div>

              <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-5">
                <h3 className="font-semibold mb-4">
                  Payment Intents ({Object.values(paymentStatusCounts).reduce((a: number, b: number) => a + b, 0)} total)
                </h3>
                {Object.keys(paymentStatusCounts).length > 0 ? (
                  <BarChart
                    data={paymentStatusData}
                    label="Intents"
                    maxValue={Math.max(...paymentStatusData.map((d) => d.value), 1)}
                  />
                ) : (
                  <p className="text-sm opacity-50">No payment intents in this window</p>
                )}
              </div>
            </div>

            {/* Top SKUs */}
            <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-5">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-4">
                <h3 className="font-semibold">Top Workflows by Captured Amount</h3>
                <button
                  type="button"
                  onClick={handleExportCsv}
                  disabled={exporting}
                  className="w-fit rounded-full border border-[var(--accent)]/30 px-3 py-1.5 text-xs font-semibold text-[var(--accent)] transition hover:bg-[var(--accent)]/10 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {exporting ? "Exporting..." : "Export CSV"}
                </button>
              </div>
              {exportError && (
                <div className="mb-4 rounded-lg border border-red-800 bg-red-900/20 p-3 text-sm text-red-300">
                  {exportError}
                </div>
              )}
              {skuGroups.length > 0 ? (
                skuGroups.map(({ currency, items }) => (
                  <section key={currency} className="mb-6" aria-label={`Captured ${currency}`}>
                    <h4 className="text-sm mb-2">{currency}</h4>
                    <BarChart
                      data={items.map((s) => ({ label: s.workflow_slug, value: Number(s.captured_amount || "0"), color: "#00d4aa" }))}
                      label={`Captured ${currency}`}
                      maxValue={Math.max(...items.map((s) => Number(s.captured_amount || "0")), 1)}
                    />
                  </section>
                ))
              ) : (
                <p className="text-sm opacity-50">No workflow revenue in this window</p>
              )}
            </div>

            {/* SKU Detail Table */}
            {topSkus.length > 0 && (
              <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-[var(--border)] text-left">
                        <th className="px-4 py-3 font-medium opacity-60">Workflow</th>
                        <th className="px-4 py-3 font-medium opacity-60">Category</th>
                        <th className="px-4 py-3 font-medium opacity-60">Currency</th>
                        <th className="px-4 py-3 font-medium opacity-60 text-right">Quotes</th>
                        <th className="px-4 py-3 font-medium opacity-60 text-right">Paid</th>
                        <th className="px-4 py-3 font-medium opacity-60 text-right">Captured</th>
                        <th className="px-4 py-3 font-medium opacity-60 text-right">Refunded</th>
                        <th className="px-4 py-3 font-medium opacity-60 text-right">Margin</th>
                        <th className="px-4 py-3 font-medium opacity-60 text-right">Referral</th>
                      </tr>
                    </thead>
                    <tbody>
                      {topSkus.map((sku: any) => (
                        <tr key={`${sku.currency}:${sku.workflow_slug}`} className="border-b border-[var(--border)]/50 hover:bg-white/5">
                          <td className="px-4 py-3">
                            <span className="font-mono text-xs">{sku.workflow_slug}</span>
                          </td>
                          <td className="px-4 py-3 text-xs opacity-60">{sku.category || "—"}</td>
                          <td className="px-4 py-3 font-mono text-xs">{sku.currency}</td>
                          <td className="px-4 py-3 text-right font-mono">{sku.quote_count}</td>
                          <td className="px-4 py-3 text-right font-mono text-green-400">{sku.captured_count}</td>
                          <td className="px-4 py-3 text-right font-mono font-bold text-[var(--accent)]">
                            {parseFloat(sku.captured_amount || "0").toFixed(2)}
                          </td>
                          <td className="px-4 py-3 text-right font-mono text-red-400">
                            {parseFloat(sku.refunded_amount || "0").toFixed(2)}
                          </td>
                          <td className="px-4 py-3 text-right font-mono text-orange-400">
                            {parseFloat(sku.estimated_margin_amount || "0").toFixed(2)}
                          </td>
                          <td className="px-4 py-3 text-right font-mono text-blue-400">
                            {parseFloat(sku.referral_commission_amount || "0").toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Margin Breakdown */}
            {currencyList.length > 0 && (
              <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-5">
                <h3 className="font-semibold mb-3">Margin Breakdown</h3>
                <div className="space-y-2">
                  {currencyList.map((curr) => {
                    const gross = grossByCurrency[curr] || 0;
                    const margin = marginTotals[curr] || 0;
                    const cost = costTotals[curr] || 0;
                    const referral = referralTotals[curr] || 0;
                    const marginPct = gross > 0 ? (margin / gross) * 100 : null;
                    return (
                      <div key={curr} className="space-y-1">
                        <div className="flex flex-col gap-1 text-xs opacity-60 sm:flex-row sm:justify-between">
                          <span>{curr}</span>
                          <span className="break-words sm:text-right">Gross {gross.toFixed(2)} · Margin {margin.toFixed(2)} · Cost {cost.toFixed(2)} · Referral {referral.toFixed(2)}</span>
                        </div>
                        <div className="h-3 bg-[var(--border)] rounded overflow-hidden flex">
                          {gross > 0 && (
                            <>
                              <div
                                className="h-full bg-[var(--accent)]"
                                style={{ width: `${Math.max((margin / gross) * 100, 0.5)}%` }}
                                title={`Margin ${margin.toFixed(2)}`}
                              />
                              <div
                                className="h-full bg-orange-500"
                                style={{ width: `${Math.max((cost / gross) * 100, 0.5)}%` }}
                                title={`LLM Cost ${cost.toFixed(2)}`}
                              />
                              <div
                                className="h-full bg-blue-500"
                                style={{ width: `${Math.max((referral / gross) * 100, 0.5)}%` }}
                                title={`Referral ${referral.toFixed(2)}`}
                              />
                            </>
                          )}
                        </div>
                        <div className="text-xs font-mono text-right">{marginPct === null ? "—" : `${marginPct.toFixed(1)}%`} margin</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </>
  );
}
