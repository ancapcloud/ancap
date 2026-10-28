"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Navigation } from "@/components/Navigation";
import { useAuth } from "@/components/AuthProvider";
import { useLanguage } from "@/components/LanguageProvider";
import { workflowValue } from "@/lib/api";
import { formatValueEstimate, type ValueSummary } from "@/lib/workflowValue";
import { workflowValueCopy } from "@/locales/workflowValue";

export default function WorkflowValuePage() {
  const { lang } = useLanguage(), copy = workflowValueCopy[lang];
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [days, setDays] = useState(30);
  const [data, setData] = useState<ValueSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  useEffect(() => { if (!isLoading && !isAuthenticated) router.push("/login"); }, [isAuthenticated, isLoading, router]);
  useEffect(() => {
    if (!isAuthenticated) return;
    let active = true;
    setLoading(true); setData(null); setError(false);
    void workflowValue.summary(days).then(result => { if (active) setData(result); })
      .catch(() => { if (active) setError(true); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [days, isAuthenticated]);
  if (isLoading || !isAuthenticated) return null;
  function download() {
    if (!data) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
    const link = document.createElement("a"); link.href = url; link.download = `ancap-private-value-${data.days}d.json`;
    document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const counts = data ? [
    [copy.completed, data.completed_count], [copy.assessed, data.assessed_count], [copy.accepted, data.accepted_count],
    [copy.revision_requested, data.revision_requested_count], [copy.rejected, data.rejected_count],
    [copy.timed, data.timed_assessment_count], [copy.valued, data.labor_valued_count],
  ] as const : [];
  return <><Navigation /><main className="mx-auto max-w-6xl px-4 py-8 space-y-6 sm:px-6">
    <div className="flex flex-wrap items-start justify-between gap-4"><div><h1 className="text-3xl font-semibold">{copy.title}</h1><p className="mt-2 opacity-70">{copy.subtitle}</p></div><Link href="/ai/runs" className="btn btn-ghost">{copy.back}</Link></div>
    <p className="text-sm opacity-70">{copy.privacy}</p>
    <div className="flex flex-wrap items-center gap-3"><label>{copy.days}<select className="input ml-2 w-auto" value={days} onChange={e => setDays(Number(e.target.value))}>{[7, 30, 90].map(d => <option key={d} value={d}>{d}</option>)}</select></label><button className="btn btn-ghost" onClick={download} disabled={!data || loading}>{copy.export}</button></div>
    {loading && <p role="status">…</p>}{error && <p role="alert">{copy.loadError}</p>}
    {data && <>
      <p className="text-sm opacity-60">{copy.scope.replace("{days}", String(data.days)).replace("{limit}", String(data.limit))}</p>
      {data.truncated && <p role="note" className="text-sm text-amber-300">{copy.limited}</p>}
      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">{counts.map(([label, count]) => <div key={label} className="card min-w-0 break-words"><dt className="text-sm leading-snug opacity-70">{label}</dt><dd className="mt-2 text-2xl font-semibold">{count}</dd></div>)}</dl>
      <section className="card space-y-3" aria-label={copy.timeSaved}><h2 className="text-xl font-semibold">{copy.timeSaved}</h2><p className="text-2xl">{formatValueEstimate(data.estimated_minutes_saved, lang) ?? copy.unknown}</p><p className="text-sm opacity-70">{copy.estimatesWarning}</p></section>
      <section className="card space-y-3" aria-label={copy.laborValue}><h2 className="text-xl font-semibold">{copy.laborValue}</h2>{data.estimated_labor_value.length ? <ul className="space-y-2">{data.estimated_labor_value.map(m => <li key={m.currency}>{formatValueEstimate(m.amount, lang)} {m.currency}</li>)}</ul> : <p>{copy.unknown}</p>}</section>
      <section className="card space-y-3" aria-label={copy.ledgerCharges}><h2 className="text-xl font-semibold">{copy.ledgerCharges}</h2>{data.ledger_charges.length ? <ul className="space-y-2">{data.ledger_charges.map(m => <li key={m.currency}>{formatValueEstimate(m.amount, lang)} {m.currency}</li>)}</ul> : <p>{copy.noData}</p>}<p className="text-sm opacity-70">{copy.ledgerWarning}</p></section>
    </>}
  </main></>;
}
