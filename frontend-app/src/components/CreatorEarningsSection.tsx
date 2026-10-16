"use client";
import Link from "next/link";
import { useId, useState } from "react";
import { useLanguage } from "./LanguageProvider";
import { economyByLang } from "@/locales/economy";
import { calculateEarningsScenario, exampleEarningsInputs, formatScenarioAmount, type EarningsInputs } from "@/lib/earningsScenario";
import { presentationStyles as s } from "./WorkflowPresentation";

export function CreatorEarningsSection() {
  const { lang } = useLanguage();
  const c = economyByLang[lang];
  const id = useId();
  const [input, setInput] = useState<EarningsInputs>(exampleEarningsInputs);
  const result = calculateEarningsScenario(input);
  const fields = ["price", "orders", "feePercent", "variableCost", "fixedCost"] as const;
  return <section id="creator-earnings" className={s.section} aria-labelledby={`${id}-title`}>
    <h2 id={`${id}-title`} className={s.heading}>{c.earnings}</h2><p className={s.lead}>{c.earningsLead}</p>
    <p id={`${id}-assumptions`} className={s.note}>{c.assumptions}</p>
    <div className={s.gridTwo}>
      <div className={s.card}><div className="grid gap-4">{fields.map(field => <label key={field} htmlFor={`${id}-${field}`} className="grid min-w-0 gap-2 text-sm">
        <span>{c[field]}</span><input id={`${id}-${field}`} type="number" min="0" max={field === "feePercent" ? "100" : field === "orders" ? "999999" : "999999999"} step={field === "orders" ? "1" : field === "feePercent" ? "0.01" : "0.00000001"} value={input[field]} onChange={event => setInput(previous => ({ ...previous, [field]: event.target.value }))} aria-describedby={`${id}-assumptions ${id}-limits`} className="w-full min-w-0 rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-[var(--text)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--accent)]" />
      </label>)}</div></div>
      <div className={s.card} aria-live="polite" aria-atomic="true">
        {result ? <><dl className="grid gap-5">{(["gross", "fee", "costs", "net"] as const).map(key => <div key={key}><dt className="text-sm text-[var(--text-muted)]">{c[key]}</dt><dd className={`mt-1 break-words font-semibold ${key === "net" ? "text-2xl" : "text-lg"}`} data-testid={`earnings-${key}`}>{formatScenarioAmount(result[key], lang)} ACP</dd></div>)}</dl>{result.loss && <p className="mt-5 font-semibold">{c.loss}</p>}</> : <p role="status">{c.invalid}</p>}
        <p className="mt-6 text-xs text-[var(--text-muted)]">{c.formula}</p>
      </div>
    </div>
    <p id={`${id}-limits`} className={s.note}>{c.disclaimer}</p><div className={s.actions}><Link href="/dashboard/seller" className={s.primary}>{c.creator} →</Link><Link href="/ai/workflows" className={s.secondary}>{c.browse}</Link></div>
  </section>;
}
