"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useLanguage } from "./LanguageProvider";
import { homeFirstRunByLang } from "@/locales/homeFirstRun";
import { positioningByLang } from "@/locales/positioning";
import { trackEvent } from "@/lib/analytics";
import h from "./HomeFirstRun.module.css";

const recommendedHref = "/ai/run/token-risk-report";

export function HomeFirstRun({ afterHero }: { afterHero?: ReactNode }) {
  const { lang } = useLanguage();
  const c = homeFirstRunByLang[lang];
  const p = positioningByLang[lang];
  const steps = [
    [c.input, c.inputBody], [c.review, c.reviewBody],
    [c.run, c.runBody], [c.result, c.resultBody],
  ];
  const workflows = [
    { category: c.research, title: c.workflowTitle, body: c.workflowBody, href: recommendedHref },
    { category: c.launch, title: p.launch, body: p.launchBody, href: "/ai/run/exchange-listing-submission-pack" },
    { category: c.growth, title: p.growth, body: p.growthBody, href: "/ai/run/crypto-campaign-builder" },
  ];
  const start = (placement: string) => trackEvent("homepage_primary_cta_click", {
    slug: "token-risk-report", placement, language: lang,
  });

  return <div className={h.experience}>
    <section className={h.hero} id="product" aria-labelledby="homepage-title">
      <div className={h.heroCopy}>
        <p className={h.eyebrow}><span className={h.dot} /> ANCAP / {c.kicker}</p>
        <h1 id="homepage-title">{c.title} <span>{c.accent}</span></h1>
        <p className={h.lead}>{c.lead}</p>
        <div className={h.actions}>
          <Link href={recommendedHref} className={h.primary} onClick={() => start("hero")}>{c.start}<span aria-hidden="true">↗</span></Link>
          <Link href="/ai/workflows" className={h.secondary}>{c.browse}<span aria-hidden="true">→</span></Link>
        </div>
        <ul className={h.capabilities}>
          {[c.research, c.launch, c.growth].map(label => <li key={label}>{label}</li>)}
        </ul>
      </div>

      <figure className={h.visual} aria-labelledby="execution-preview-title">
        <div className={h.windowBar}><span className={h.windowBrand}><svg viewBox="0 0 32 32" fill="none" aria-hidden="true"><path d="m6 25 10-18 10 18M11 18h10" stroke="currentColor" strokeWidth="2" /></svg><span>ANCAP</span><span className={h.toolbarDivider}>/</span>{p.workflows}</span><span className={h.windowDots} aria-hidden="true">•••</span></div>
        <div className={h.visualBody}>
          <div className={h.visualHeading}><span className={h.eyebrow}>{c.research}</span><span className={h.previewBadge}>{c.preview}</span></div>
          <h2 id="execution-preview-title">{c.workflowTitle}</h2>
          <ol className={h.flowRail}>
            {[c.input, c.review, c.run, c.result].map((label, i) => <li key={label}><span>0{i + 1}</span>{label}</li>)}
          </ol>
          <div className={h.workflowCanvas}>
            <svg className={h.connections} viewBox="0 0 600 360" fill="none" preserveAspectRatio="none" aria-hidden="true">
              <defs><linearGradient id="home-workflow-edge"><stop stopColor="#49d3b0" stopOpacity=".1"/><stop offset=".5" stopColor="#71e4d3" stopOpacity=".8"/><stop offset="1" stopColor="#70bcf1" stopOpacity=".4"/></linearGradient></defs>
              <path d="M120 82H232Q260 82 260 112V180H340M120 278H232Q260 278 260 248V180M340 180H470" stroke="url(#home-workflow-edge)" strokeWidth="1.5"/>
              <circle cx="260" cy="180" r="5" fill="#7de2c9"/>
            </svg>
            <div className={h.sourceNodes}>
              <div className={h.inputNode}><div className={h.nodeLabel}><span className={h.nodeIcon} aria-hidden="true">↳</span><span>01 / {c.input}</span></div><p>{c.inputPreview}</p><div className={h.inputLines} aria-hidden="true"><i/><i/><i/></div><span className={h.nodePort} aria-hidden="true"/></div>
              <div className={h.quoteNode}><div className={h.nodeLabel}><span className={h.nodeIcon} aria-hidden="true">≋</span><span>02 / {c.review}</span></div><p>{c.quotePreview}</p><span className={h.nodePort} aria-hidden="true"/></div>
            </div>
            <div className={h.engine} aria-hidden="true"><div><svg viewBox="0 0 48 48" fill="none"><path d="m10 36 14-25 14 25M17 25h14" stroke="currentColor" strokeWidth="2"/></svg></div><span>ANCAP</span></div>
            <div className={h.outputDock}>
              <div className={h.resultPanel}>
                <div className={h.resultHeader}><span className={h.resultIcon} aria-hidden="true">▤</span><strong>{c.outputLabel}</strong></div>
                <ul>{c.outputPreview.split(" · ").map((item, i) => <li key={item}><span aria-hidden="true">0{i + 1}</span>{item}<i aria-hidden="true"/></li>)}</ul>
                <div className={h.documentLines} aria-hidden="true"><i/><i/><i/></div>
              </div>
              <div className={h.receipt}><span className={h.receiptSeal} aria-hidden="true">↗</span><div><strong>{c.receipt}</strong><p>{c.receiptPreview}</p></div><span className={h.receiptEdge} aria-hidden="true">⠿</span></div>
            </div>
          </div>
        </div>
      </figure>
    </section>

    {afterHero}

    <section className={h.principles} aria-label={c.principlesTitle}>
      {[[c.execution, c.executionBody], [c.quote, c.quoteBody], [c.receipt, c.receiptBody]].map(([title, body], i) => <div key={title}><span className={h.ordinal}>0{i + 1}</span><div><h2>{title}</h2><p>{body}</p></div></div>)}
    </section>

    <section className={h.section} id="first-workflow" aria-labelledby="first-workflow-title">
      <p className={h.eyebrow}>{c.startHere}</p>
      <div className={h.sectionIntro}><h2 id="first-workflow-title">{c.firstTitle}</h2><p>{c.firstLead}</p></div>
      <div className={h.recommended}>
        <article className={h.offer}>
          <div className={h.offerTop}><span className={h.category}>{c.research}</span><span className={h.recommendedBadge}><span aria-hidden="true">✦</span> {c.recommended}</span></div>
          <span className={h.offerIcon} aria-hidden="true">⌕</span>
          <h3>{c.workflowTitle}</h3><p className={h.offerBody}>{c.workflowBody}</p>
          <ol className={h.offerStages}>{[c.input, c.review, c.result].map((label, i) => <li key={label}><span>0{i + 1}</span>{label}</li>)}</ol>
          <div className={h.actions}><Link className={h.primary} href={recommendedHref} onClick={() => start("recommended")}>{c.startWorkflow}<span aria-hidden="true">↗</span></Link><Link className={h.textLink} href="/ai/workflows">{c.allWorkflows}<span aria-hidden="true">→</span></Link></div>
        </article>
        <div className={h.path}><p className={h.eyebrow}>{c.path}</p><ol>{steps.map(([title, body], i) => <li key={title}><span className={h.pathNumber}>0{i + 1}</span><div><h3>{title}</h3><p>{body}</p></div></li>)}</ol></div>
      </div>
      <div className={h.completion}><span aria-hidden="true">↳</span><p><strong>{c.completion}</strong> {c.completionBody}</p></div>
    </section>

    <section className={`${h.section} ${h.discovery}`} id="workflow-discovery" aria-labelledby="workflow-examples-title">
      <p className={h.eyebrow}>{c.discover}</p>
      <div className={h.sectionIntro}><h2 id="workflow-examples-title">{c.discoverTitle}</h2><p>{c.discoverLead}</p></div>
      <div className={h.cards}>{workflows.map((workflow, i) => <article className={h.discoveryCard} key={workflow.href}>
        <div className={h.cardTop}><span className={h.category}>{workflow.category}</span><span className={h.ordinal}>0{i + 1}</span></div>
        <svg className={h.discoveryIcon} viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">{i === 0 ? <><circle cx="21" cy="20" r="11"/><path d="m29 28 11 11M16 20h10M21 15v10"/></> : i === 1 ? <><path d="M13 6h16l8 8v28H13zM28 6v10h9M20 24h10M20 30h10M20 36h6"/></> : <><path d="M7 38h34M11 31l10-10 8 5 12-15M31 11h10v10"/><circle cx="11" cy="31" r="2"/></>}</svg>
        <h3>{workflow.title}</h3><p>{workflow.body}</p><Link className={h.textLink} href={workflow.href}>{c.open}<span aria-hidden="true">↗</span></Link>
      </article>)}</div>
    </section>
  </div>;
}
