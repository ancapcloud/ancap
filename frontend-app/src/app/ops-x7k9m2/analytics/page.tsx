"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useLanguage } from "@/components/LanguageProvider";
import QrCampaignStats from "@/components/QrCampaignStats";
import { platformAdmin } from "@/lib/api";

const METRICS = [
  { id: "signups", labelKey: "metricSignups" },
  { id: "workflow_runs", labelKey: "metricRuns" },
  { id: "captured_payments", labelKey: "metricPayments" },
] as const;

export default function OpsAnalyticsPage() {
  const { t } = useLanguage();
  const [metric, setMetric] = useState<string>("signups");
  const [days, setDays] = useState(30);
  const [horizon, setHorizon] = useState(7);
  const [points, setPoints] = useState<any[]>([]);
  const [slope, setSlope] = useState(0);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setError("");
      const res = await platformAdmin.forecast(metric, days, horizon);
      setPoints(res.points || []);
      setSlope(res.slope_per_day || 0);
    } catch (e: any) {
      setError(e?.message || String(e));
    }
  }, [metric, days, horizon]);

  useEffect(() => {
    void load();
  }, [load]);

  const chartData = useMemo(
    () =>
      points.map((p) => ({
        date: p.date.slice(5),
        history: p.kind === "history" ? p.value : null,
        forecast: p.kind === "forecast" ? p.value : null,
        value: p.value,
      })),
    [points],
  );

  return (
    <div className="space-y-6">
      <QrCampaignStats />
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-lg font-medium">{t("opsConsole.analyticsTitle")}</h2>
          <p className="mt-1 text-xs text-white/40">
            {t("opsConsole.slope")}: <span className="tabular-nums text-emerald-300">{slope}</span>
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <select
            value={metric}
            onChange={(e) => setMetric(e.target.value)}
            className="rounded-lg border border-white/10 bg-[#0a1218] px-3 py-1.5 text-xs"
          >
            {METRICS.map((m) => (
              <option key={m.id} value={m.id}>
                {t(`opsConsole.${m.labelKey}`)}
              </option>
            ))}
          </select>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="rounded-lg border border-white/10 bg-[#0a1218] px-3 py-1.5 text-xs"
            aria-label={t("opsConsole.days")}
          >
            {[14, 30, 60, 90].map((d) => (
              <option key={d} value={d}>
                {d}d
              </option>
            ))}
          </select>
          <select
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
            className="rounded-lg border border-white/10 bg-[#0a1218] px-3 py-1.5 text-xs"
            aria-label={t("opsConsole.horizon")}
          >
            {[3, 7, 14].map((d) => (
              <option key={d} value={d}>
                +{d}d
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => void load()}
            className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-white/70 hover:bg-white/5"
          >
            {t("opsConsole.refresh")}
          </button>
        </div>
      </div>

      {error && <p className="text-sm text-rose-300">{error}</p>}

      <div className="h-80 rounded-2xl border border-white/8 bg-gradient-to-b from-emerald-950/20 to-transparent p-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="histFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#34d399" stopOpacity={0.45} />
                <stop offset="100%" stopColor="#34d399" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="fcFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#fbbf24" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#fbbf24" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
            <XAxis dataKey="date" tick={{ fill: "rgba(255,255,255,0.35)", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "rgba(255,255,255,0.35)", fontSize: 11 }} axisLine={false} tickLine={false} width={36} />
            <Tooltip
              contentStyle={{
                background: "#0a1218",
                border: "1px solid rgba(52,211,153,0.25)",
                borderRadius: 12,
                fontSize: 12,
              }}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="history"
              name={t("opsConsole.history")}
              stroke="#34d399"
              fill="url(#histFill)"
              strokeWidth={2}
              connectNulls={false}
            />
            <Area
              type="monotone"
              dataKey="forecast"
              name={t("opsConsole.forecast")}
              stroke="#fbbf24"
              fill="url(#fcFill)"
              strokeWidth={2}
              strokeDasharray="4 4"
              connectNulls={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
