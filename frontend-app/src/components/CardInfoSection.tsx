"use client";
import Link from "next/link";
import { useId } from "react";
import { useLanguage } from "./LanguageProvider";
import { cardInfoByLang } from "@/locales/cardInfo";
import { presentationStyles as s } from "./WorkflowPresentation";

export function CardInfoSection() {
  const { lang } = useLanguage();
  const c = cardInfoByLang[lang];
  const id = useId();
  return <section id="ancap-card" className={s.section} aria-labelledby={`${id}-title`}>
    <p className={s.eyebrow}>{c.badge}</p>
    <h2 id={`${id}-title`} className={s.heading}>{c.title}</h2>
    <p className={s.lead}>{c.lead}</p>
    <p className={s.note}>{c.status}</p>
    <div className={s.gridTwo}>
      <div className={s.card}>
        <div className="mb-6 flex aspect-[1.586] w-full max-w-sm flex-col justify-between rounded-2xl border border-emerald-300/30 bg-gradient-to-br from-[#121923] to-[#0B0F14] p-6 text-[#F4F7FB]">
          <span className="text-xl font-semibold tracking-widest">ANCAP</span>
          <span className="text-sm tracking-widest text-[#62E6B7]">CARD CONCEPT</span>
          <span className="text-xs text-[#A7B1BF]">{c.model}</span>
        </div>
        <ul className="list-disc space-y-3 pl-5 text-sm">{c.benefits.map(benefit => <li key={benefit}>{benefit}</li>)}</ul>
      </div>
      <div className={s.card}>
        <h3>{c.rewardsTitle}</h3><p>{c.rewards}</p>
        <p className="mt-4 font-semibold text-[var(--accent)]">{c.rewardsStatus}</p>
        <p className="mt-4">{c.bonuses}</p>
      </div>
    </div>
    <p className={s.note}>{c.transparency}</p>
    <div className={s.actions}><Link href="/cards#waitlist" className={s.primary}>{c.cta} →</Link><Link href="/cards" className={s.secondary}>{c.concept}</Link></div>
  </section>;
}
