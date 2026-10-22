"use client";

import Link from "next/link";
import { Navigation } from "@/components/Navigation";
import { useLanguage } from "@/components/LanguageProvider";
import { WorkflowFooter, presentationStyles as s } from "@/components/WorkflowPresentation";
import { positioningByLang } from "@/locales/positioning";
import { investorOverviewByLang } from "@/locales/investorOverview";
import { DemoEvidencePanel } from "@/components/workflow/DemoEvidencePanel";
import { PeopleAiEconomySection } from "@/components/PeopleAiEconomySection";
import styles from "./investors.module.css";

const contactHref = "mailto:support@ancap.cloud?subject=ANCAP%20investment%20discussion";

export function InvestorOverview() {
  const { lang } = useLanguage();
  const c = investorOverviewByLang[lang];
  return <div className={s.shell}>
    <Navigation />
    <main className={s.main}>
      <section className={styles.hero} aria-labelledby="investor-title">
        <div className={styles.heroCopy}>
          <p className={s.eyebrow}>ANCAP / {positioningByLang[lang].investors}</p>
          <h1 id="investor-title" className={styles.title}>{c.title}</h1>
          <p className={s.lead}>{c.lead}</p>
          <div className={s.actions}>
            <a href={contactHref} className={s.primary}>{c.contact} →</a>
            <Link href="/ai/workflows" className={s.secondary}>{c.browse}</Link>
          </div>
        </div>
        <aside className={styles.thesis} aria-labelledby="investment-thesis">
          <h2 id="investment-thesis" className={s.eyebrow}>{c.overview}</h2>
          <dl>{c.facts.map(([label, body]) => <div key={label}>
            <dt>{label}</dt><dd>{body}</dd>
          </div>)}</dl>
        </aside>
      </section>

      <section className={s.section} aria-labelledby="customer-problem">
        <h2 id="customer-problem" className={s.heading}>{c.problem}</h2>
        <p className={s.lead}>{c.problemBody}</p>
        <ol className={styles.steps}>{c.journey.map(([title, body], i) => <li key={title}>
          <span className={styles.number} aria-hidden="true">0{i + 1}</span>
          <h3>{title}</h3><p>{body}</p>
        </li>)}</ol>
      </section>

      <section id="investor-ecosystem" className={s.section} aria-labelledby="ecosystem-title">
        <h2 id="ecosystem-title" className={s.heading}>{c.ecosystem}</h2>
        <p className={s.lead}>{c.ecosystemLead}</p>
        <div className={s.grid}>{c.tracks.map(([status, title, body], i) => <article key={title} className={`${s.card} ${i === 0 ? styles.focusCard : ""}`}>
          <span className={`${s.tag} ${i === 0 ? s.core : ""}`}>{status}</span>
          <h3>{title}</h3><p>{body}</p>
        </article>)}</div>
        <div className={s.actions}><Link href="/projects" className={s.secondary}>{c.portfolio} →</Link></div>
      </section>

      <section className={s.section} aria-labelledby="revenue-model">
        <h2 id="revenue-model" className={s.heading}>{c.economics}</h2>
        <p className={s.lead}>{c.economicsBody}</p>
        <p className={s.note}>{c.token}</p>
      </section>

      <section id="investor-evidence" className={s.section} aria-labelledby="evidence-title">
        <h2 id="evidence-title" className={s.heading}>{c.proof}</h2>
        <p className={s.lead}>{c.proofBody}</p>
        <div className={s.actions}>
          <Link href="/ai/studio" className={s.secondary}>{c.studio}</Link>
          <Link href="/sample-reports/token-risk-report-pro" className={s.secondary}>{c.sample}</Link>
          <Link href="/proof-center" className={s.secondary}>{c.trust}</Link>
          <Link href="/developers" className={s.secondary}>{c.documents}</Link>
          <a className={s.secondary} href="https://github.com/ancapcloud/ancap" target="_blank" rel="noopener noreferrer">GitHub ↗</a>
        </div>
        <details className={styles.evidenceDetails}>
          <summary>{c.execution}</summary>
          <DemoEvidencePanel />
        </details>
        <div className={s.gridTwo}>
          <article className={s.card}><h3>{c.metrics}</h3><p>{c.metricsBody}</p></article>
          <article className={s.card}><h3>{c.founder}</h3><p>{c.founderBody}</p></article>
        </div>
      </section>

      <section id="investor-funding" className={s.section} aria-labelledby="funding-title">
        <h2 id="funding-title" className={s.heading}>{c.funding}</h2>
        <p className={s.lead}>{c.fundingBody}</p>
        <div className={s.grid}>{c.milestones.map(([title, body], i) => <article key={title} className={s.card}>
          <span className={styles.number} aria-hidden="true">0{i + 1}</span><h3>{title}</h3><p>{body}</p>
        </article>)}</div>
        <div className={s.note}><strong>{c.structure}</strong><p>{c.structureBody}</p></div>
        <div className={s.actions}>
          <Link href="/docs/investors/budget-12m" className={s.secondary}>{c.budget}</Link>
          <Link href="/docs/investors/demo-5min" className={s.secondary}>{c.demo}</Link>
        </div>
      </section>

      <PeopleAiEconomySection compact />

      <section className={styles.contact} aria-labelledby="investor-contact">
        <p className={s.eyebrow}>ANCAP</p>
        <h2 id="investor-contact" className={s.heading}>{c.next}</h2>
        <p className={s.lead}>{c.nextBody}</p>
        <div className={s.actions}><a href={contactHref} className={s.primary}>{c.contact} →</a><a href="mailto:support@ancap.cloud" className={s.secondary}>support@ancap.cloud</a></div>
        <p className={styles.footnote}>{c.note}</p>
      </section>
    </main>
    <WorkflowFooter />
  </div>;
}
