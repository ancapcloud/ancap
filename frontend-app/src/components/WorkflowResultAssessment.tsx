"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ApiError, workflowValue } from "@/lib/api";
import type { AssessmentHistory, AssessedResult, AssessmentState, AssessmentVerdict } from "@/lib/workflowValue";
import { useLanguage } from "@/components/LanguageProvider";
import { workflowValueCopy } from "@/locales/workflowValue";

export function WorkflowResultAssessment({ runId, resultHash }: { runId: string; resultHash: string }) {
  const { lang } = useLanguage();
  const copy = workflowValueCopy[lang];
  const generation = useRef(0);
  const [history, setHistory] = useState<AssessmentHistory | null>(null);
  const [archived, setArchived] = useState<AssessedResult | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [versionLoading, setVersionLoading] = useState(false);
  const [state, setState] = useState<AssessmentState | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [conflict, setConflict] = useState(false);
  const [verdict, setVerdict] = useState<AssessmentVerdict>("accepted");
  const [baseline, setBaseline] = useState("");
  const [assisted, setAssisted] = useState("");
  const [rate, setRate] = useState("");
  const [unit, setUnit] = useState("USD");
  const [note, setNote] = useState("");
  useEffect(() => {
    let active = true;
    generation.current += 1;
    setState(null); setError(""); setConflict(false); setSaving(false);
    setHistory(null); setArchived(null); setHistoryLoading(false); setVersionLoading(false);
    void workflowValue.assessment(runId).then(data => { if (active) setState(data); })
      .catch(() => { if (active) setError(copy.loadError); });
    return () => { active = false; generation.current += 1; };
  }, [runId, resultHash, copy.loadError]);
  const mismatched = state !== null && state.result_hash !== resultHash;
  const blocked = conflict || mismatched;
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!state || blocked || state.assessment || saving) return;
    const submittedGeneration = generation.current;
    setSaving(true); setError("");
    try {
      const assessment = await workflowValue.assess(runId, {
        result_hash: resultHash, verdict, baseline_minutes: baseline.trim() || null, assisted_minutes: assisted.trim() || null,
        hourly_rate: rate.trim() || null, hourly_currency: rate.trim() ? unit.trim() : null, note: note.trim() || null,
      });
      if (generation.current === submittedGeneration) setState({ ...state, assessment });
    } catch (e) {
      if (generation.current !== submittedGeneration) return;
      if (e instanceof ApiError && e.status === 409) { setConflict(true); setError(copy.reload); }
      else setError(`${copy.saveError} ${copy.checkFields}`);
    } finally { if (generation.current === submittedGeneration) setSaving(false); }
  }
  async function loadHistory() {
    const version = generation.current; setHistoryLoading(true); setError("");
    try { const data = await workflowValue.history(runId); if (generation.current === version) setHistory(data); }
    catch { if (generation.current === version) setError(copy.loadError); }
    finally { if (generation.current === version) setHistoryLoading(false); }
  }
  async function viewVersion(id: string) {
    const version = generation.current; setVersionLoading(true); setError("");
    try { const data = await workflowValue.assessedResult(id); if (generation.current === version) setArchived(data); }
    catch { if (generation.current === version) setError(copy.loadError); }
    finally { if (generation.current === version) setVersionLoading(false); }
  }
  return <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-5 sm:p-6" aria-label={copy.acceptanceTitle}>
    <h2 className="text-xl font-semibold">{copy.acceptanceTitle}</h2>
    <p className="mt-2 text-sm opacity-70">{copy.acceptanceHelp}</p>
    <p className="mt-2 text-xs break-all opacity-50">SHA-256: {resultHash}</p>
    {error && <p role="alert" className="mt-3 text-sm text-red-300">{error}</p>}
    {(blocked || state?.has_stale_assessment) && <p className="mt-3 text-sm text-amber-300">{copy.stale}</p>}
    {blocked && <button type="button" className="btn btn-ghost mt-3" onClick={() => window.location.reload()}>{copy.reload}</button>}
    {state?.assessment && !mismatched ? <div className="mt-4 space-y-2">
      <h3 className="font-semibold">{copy.saved}: {copy[state.assessment.verdict]}</h3>
      <p className="text-sm opacity-70">{copy.immutable}</p>
      {state.assessment.baseline_minutes !== null && <p>{copy.baseline}: {state.assessment.baseline_minutes}; {copy.assisted}: {state.assessment.assisted_minutes}</p>}
      {state.assessment.hourly_rate !== null && <p>{copy.rate}: {state.assessment.hourly_rate} {state.assessment.hourly_currency}</p>}
      {state.assessment.note && <p className="whitespace-pre-wrap break-words text-sm">{state.assessment.note}</p>}
    </div> : state && !blocked ? <form onSubmit={submit} className="mt-4 space-y-4">
      <fieldset disabled={saving} className="space-y-4">
        <label className="block text-sm">{copy.verdict}<select className="input mt-1" value={verdict} onChange={e => setVerdict(e.target.value as AssessmentVerdict)}>
          {(["accepted", "revision_requested", "rejected"] as const).map(v => <option key={v} value={v}>{copy[v]}</option>)}
        </select></label>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">{copy.baseline}<input className="input mt-1" type="number" min="0" max="1000000" step="0.01" value={baseline} onChange={e => setBaseline(e.target.value)} /></label>
          <label className="block text-sm">{copy.assisted}<input className="input mt-1" type="number" min="0" max="1000000" step="0.01" value={assisted} onChange={e => setAssisted(e.target.value)} /></label>
          <label className="block text-sm">{copy.rate}<input className="input mt-1" type="number" min="0" max="1000000000" step="0.000001" value={rate} onChange={e => setRate(e.target.value)} /></label>
          <label className="block text-sm">{copy.unit}<input className="input mt-1" maxLength={10} value={unit} onChange={e => setUnit(e.target.value)} /></label>
        </div>
        <label className="block text-sm">{copy.note}<textarea className="input mt-1" maxLength={2000} value={note} onChange={e => setNote(e.target.value)} /></label>
        <p className="text-sm opacity-60">{copy.estimatesWarning}</p>
        <p className="text-sm opacity-70">{copy.immutable}</p>
        <button className="btn btn-primary" type="submit">{saving ? copy.saving : copy.submit}</button>
      </fieldset>
    </form> : null}
    <div className="mt-5 space-y-3">
      <button type="button" className="btn btn-ghost" onClick={() => void loadHistory()} disabled={historyLoading}>{copy.history}</button>
      {history && <div className="space-y-3">
        <p className="text-sm opacity-60">{copy.historyHelp}</p>
        {history.has_more && <p className="text-sm">{copy.historyLimited}</p>}
        {history.items.length === 0 && <p>{copy.historyEmpty}</p>}
        <ul className="space-y-3">{history.items.map(item => <li key={item.id} className="rounded-xl border border-white/10 p-3 space-y-2">
          <p>{copy[item.verdict]} · {new Date(item.created_at).toLocaleString(lang)}</p>
          <code className="block break-all text-xs opacity-60">{item.result_hash}</code>
          <button type="button" className="btn btn-ghost" onClick={() => void viewVersion(item.id)} disabled={versionLoading}>{copy.viewVersion}</button>
        </li>)}</ul>
      </div>}
      {archived && <div className="space-y-3">
        <h3 className="font-semibold">{copy.viewVersion}</h3>
        <code className="block break-all text-xs">{archived.result_hash}</code>
        <pre className="max-h-96 overflow-auto rounded-xl bg-black/20 p-3 text-xs">{JSON.stringify(archived.result, null, 2)}</pre>
        <button type="button" className="btn btn-ghost" onClick={() => setArchived(null)}>{copy.hideVersion}</button>
      </div>}
    </div>
    <Link className="mt-4 inline-block text-sm underline" href="/ai/value">{copy.view}</Link>
  </section>;
}
