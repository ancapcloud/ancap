"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useLanguage } from "@/components/LanguageProvider";
import { researchOpsCopy, researchStatusCopy, researchDiffCopy, researchDeleteCopy, researchPacketCopy, researchChannelCopy } from "@/locales/researchOps";

type Source = {id: string; title: string; url: string; status: string; latest_hash: string | null; checked_at: string | null; expires_at: string};
type Snapshot = {hash: string; text: string; created_at?: string; change?: string};
type Claim = {id: string; statement: string; excerpt: string; status: string; source_hash: string; reviewer_verdict: string};
type Brief = {project_name?: string; sources: Source[]; claims: Claim[]; version_hash: string; state: string; delivery_enabled: false};
const field = "w-full rounded border border-[var(--border)] bg-[var(--bg)] p-2";
const button = "rounded border border-[var(--border)] px-3 py-2 disabled:opacity-40";

export function ResearchPanel({projectId, canEdit, reviewableRuns=[], onPacket}: {projectId: string; canEdit: boolean; reviewableRuns?: {id:string;review_hash:string}[]; onPacket?:()=>Promise<void>}) {
  const {lang} = useLanguage();
  const c = researchOpsCopy[lang] ?? researchOpsCopy.en;
  const diffCopy = researchDiffCopy[lang];
  const [changes, setChanges] = useState<{before:string;after:string}[]>([]);
  const [reportId, setReportId] = useState("");
  const packetCopy = researchPacketCopy[lang];
  const [brief, setBrief] = useState<Brief | null>(null);
  const [selected, setSelected] = useState<Source | null>(null);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [history, setHistory] = useState<Snapshot[]>([]);
  const [title, setTitle] = useState(""); const [url, setUrl] = useState(""); const [permission, setPermission] = useState("");
  const [statement, setStatement] = useState(""); const [excerpt, setExcerpt] = useState("");
  const [verdict, setVerdict] = useState("unconfirmed");
  const [error, setError] = useState(false); const [busy, setBusy] = useState(false);
  const alive = useRef(true);
  const base = `/workflow-ops/projects/${projectId}/research`;
  const load = useCallback(async () => {
    const value: Brief = await apiFetch(base);
    if (alive.current) setBrief(value);
  }, [base]);
  useEffect(() => {alive.current = true; void load().catch(() => setError(true)); return () => {alive.current = false;};}, [load]);
  async function act(work: () => Promise<void>) {
    setBusy(true); setError(false);
    try {await work(); await load();} catch {if (alive.current) setError(true);}
    finally {if (alive.current) setBusy(false);}
  }
  const status = (value: string) => {
    const index = ["unchecked", "baseline", "unchanged", "technical", "content_change_requires_review"].indexOf(value);
    if (index >= 0) return researchStatusCopy[lang][index];
    return value === "requires_update" ? c.stale : value === "unavailable" || value === "source_unavailable" ? c.unavailable : value === "supported_by_source" ? c.supported : value === "contradiction" ? c.contradiction : c.unconfirmed;
  };
  return <section className="mt-6 space-y-4 rounded border border-[var(--border)] p-5" aria-label={c.title}>
    <h2 className="text-xl font-semibold">{c.title}</h2><p>{c.intro}</p><p className="text-sm opacity-70">{c.quota}</p>
    {error && <p role="alert">{c.error}</p>}
    <fieldset disabled={busy || !canEdit} className="grid gap-3 md:grid-cols-2">
      <label>{c.titleField}<input className={field} value={title} maxLength={120} onChange={e=>setTitle(e.target.value)}/></label>
      <label>{c.url}<input className={field} type="url" value={url} maxLength={2048} onChange={e=>setUrl(e.target.value)}/></label>
      <label className="md:col-span-2">{c.permission}<input className={field} value={permission} maxLength={500} onChange={e=>setPermission(e.target.value)}/></label>
      <button className={button} disabled={!title.trim() || permission.trim().length < 10 || !url} onClick={()=>void act(async()=>{
        await apiFetch(`${base}/sources`,{method:"POST",body:JSON.stringify({title,url,permission_basis:permission})}); setTitle("");setUrl("");setPermission("");
      })}>{c.add}</button>
    </fieldset>
    {!brief?.sources.length && <p>{c.empty}</p>}
    <ul className="space-y-3">{brief?.sources.map(s=><li key={s.id} className="rounded border border-[var(--border)] p-3">
      <a href={s.url} target="_blank" rel="noopener noreferrer" className="underline">{s.title}</a>
      <p>{c.status}: {status(s.status)} · {s.checked_at ? new Date(s.checked_at).toLocaleString(lang) : "—"}</p>
      <div className="flex flex-wrap gap-2"><button className={button} disabled={busy || !canEdit} onClick={()=>void act(async()=>{
        setSelected(s);setSnapshot(null);setHistory([]);setChanges([]);setStatement("");setExcerpt("");
        const result: {source:Source;snapshot:Snapshot|null;changes?:{items:{before:string;after:string}[]}}=await apiFetch(`${base}/sources/${s.id}/check`,{method:"POST"});
        if (alive.current) {setSelected(result.source);setSnapshot(result.snapshot);setChanges(result.changes?.items ?? []);}
      })}>{c.check}</button>
      <button className={button} disabled={busy} onClick={()=>void act(async()=>{
        const rows: Snapshot[]=await apiFetch(`${base}/sources/${s.id}/snapshots`);
        if(alive.current){setSelected(s);setHistory(rows);setSnapshot(null);setChanges([]);setExcerpt("");setStatement("");}
      })}>{c.history}</button>
      <button className={button} disabled={busy || !canEdit} onClick={()=>{
        if(!window.confirm(researchDeleteCopy[lang].confirm))return;
        void act(async()=>{await apiFetch(`${base}/sources/${s.id}`,{method:"DELETE"});if(selected?.id===s.id){setSelected(null);setSnapshot(null);setHistory([]);setChanges([]);}});
      }}>{researchDeleteCopy[lang].remove}</button></div>
    </li>)}</ul>
    {history.map((s,i)=><details key={`${s.hash}:${i}`}><summary>{s.created_at ? new Date(s.created_at).toLocaleString(lang) : ""} · {s.change ? status(s.change) : ""} · {s.hash.slice(0,12)}</summary><pre className="max-h-72 overflow-auto whitespace-pre-wrap">{s.text}</pre></details>)}
    {snapshot && selected && <div className="space-y-3">
      {changes.length > 0 && <div><p>{diffCopy.note}</p>{changes.map((change,i)=><div className="my-2 grid gap-2 md:grid-cols-2" key={i}><p>{diffCopy.before}: <del>{change.before}</del></p><p>{diffCopy.after}: <ins>{change.after}</ins></p></div>)}</div>}
      <h3>{c.full}: {selected.title}</h3><pre className="max-h-72 overflow-auto whitespace-pre-wrap">{snapshot.text}</pre>
      <fieldset disabled={busy || !canEdit} className="space-y-3">
        <label className="block">{c.statement}<textarea className={field} maxLength={1000} value={statement} onChange={e=>setStatement(e.target.value)}/></label>
        <label className="block">{c.excerpt}<textarea className={field} maxLength={500} value={excerpt} onChange={e=>setExcerpt(e.target.value)}/></label>
        <label className="block">{c.verdict}<select className={field} value={verdict} onChange={e=>setVerdict(e.target.value)}><option value="unconfirmed">{c.unconfirmed}</option><option value="supported_by_source">{c.supported}</option><option value="contradiction">{c.contradiction}</option></select></label>
        <p>{c.basis}</p><button className={button} disabled={!statement.trim() || !excerpt.trim()} onClick={()=>void act(async()=>{
          await apiFetch(`${base}/claims`,{method:"POST",body:JSON.stringify({source_id:selected.id,source_hash:snapshot.hash,statement,excerpt,verdict})});setStatement("");setExcerpt("");
        })}>{c.save}</button>
      </fieldset>
    </div>}
    <h3>{c.draft}</h3><ul>{brief?.claims.map(claim=><li className="my-3 border-l-2 border-[var(--border)] pl-3" key={claim.id}><p>{claim.statement}</p><blockquote>{claim.excerpt}</blockquote><strong>{status(claim.status)}</strong></li>)}</ul>
    <button className={button} disabled={busy || !brief} onClick={()=>void act(async()=>{
      const value: Brief=await apiFetch(base); if(!alive.current)return;
      const link=document.createElement("a");const file=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:"application/json"}));link.href=file;link.download=`research-draft-${value.version_hash.slice(0,12)}.json`;link.click();URL.revokeObjectURL(file);
    })}>{c.export}</button>
    <button className={button} disabled={busy || !brief} onClick={()=>void act(async()=>{
      const value: Brief=await apiFetch(base);if(!alive.current)return;
      const lines=[c.draft, value.project_name ?? projectId, c.intro, `Version: ${value.version_hash}`, "", c.title,
        ...value.sources.flatMap(s=>[s.title,s.url,`${c.status}: ${status(s.status)}`,s.checked_at ?? "—",""]),
        c.statement,...value.claims.flatMap(claim=>[claim.statement,claim.excerpt,status(claim.status),`Source hash: ${claim.source_hash}`,""]),c.basis];
      const link=document.createElement("a");const file=URL.createObjectURL(new Blob([lines.join("\n")],{type:"text/plain;charset=utf-8"}));link.href=file;link.download=`research-draft-${value.version_hash.slice(0,12)}.txt`;link.click();URL.revokeObjectURL(file);
    })}>{diffCopy.exportText}</button>
    <fieldset disabled={busy || !canEdit} className="space-y-3 rounded border border-[var(--border)] p-3">
      <legend>{packetCopy.title}</legend><p>{packetCopy.info}</p><p>{researchChannelCopy[lang]}</p>
      <label className="block">{packetCopy.report}<select className={field} value={reportId} onChange={event=>setReportId(event.target.value)}><option value="">{packetCopy.choose}</option>{reviewableRuns.map(run=><option key={run.id} value={run.id}>{run.id}</option>)}</select></label>
      <button className={button} disabled={!reportId || !brief?.sources.length || brief.sources.some(source=>!source.latest_hash || ["unchecked","unavailable"].includes(source.status))} onClick={()=>void act(async()=>{
        const report=reviewableRuns.find(run=>run.id===reportId);if(!report)throw new Error("Reload report");
        await apiFetch(`${base}/packets`,{method:"POST",body:JSON.stringify({operation_id:report.id,source_ids:brief!.sources.map(source=>source.id),expected_review_hash:report.review_hash})});
        await onPacket?.();
      })}>{packetCopy.attach}</button>
    </fieldset>
  </section>;
}
