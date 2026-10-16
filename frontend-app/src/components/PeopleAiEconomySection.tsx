"use client";
import Link from "next/link";
import { useLanguage } from "./LanguageProvider";
import { economyByLang } from "@/locales/economy";
import { presentationStyles as s } from "./WorkflowPresentation";

export function PeopleAiEconomySection({ compact = false }: { compact?: boolean }) {
  const { lang } = useLanguage();
  const c = economyByLang[lang];
  return <section id="people-ai-economy" className={s.section} aria-labelledby="people-ai-title">
    <p className={s.eyebrow}>{c.badge}</p><h2 id="people-ai-title" className={s.heading}>{c.title}</h2>
    <p className={s.lead}>{c.lead}</p><p className={s.note}>{c.limits}</p>
    {!compact && <ol className={s.grid} style={{ padding: 0, listStyle: "none" }}>{c.steps.map((step, i) => <li className={s.card} key={step}><h3>{i + 1}. {step}</h3><p>{c.stepNotes[i]}</p></li>)}</ol>}
    <div className={s.actions}>
      {compact && <Link className={s.secondary} href="/projects#people-ai-economy">{c.explore}</Link>}
      <Link className={s.secondary} href="/economy">{c.tests} →</Link>
      <Link className={s.secondary} href="/projects#test-projects">{lang === "ru" ? "Песочница AI" : "AI sandbox"} →</Link>
      <Link className={s.secondary} href="/ai/workflows">{c.browse}</Link>
      {!compact && <Link className={s.secondary} href="/">{c.home} →</Link>}
    </div>
  </section>;
}
