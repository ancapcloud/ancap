"use client";

import Link from "next/link";
import { useLanguage } from "./LanguageProvider";
import { RacpOverview } from "./RacpOverview";
import { racpTransitionCopy } from "@/locales/racpTransition";

export function LegacyWacpNotice() {
  const { lang } = useLanguage();
  const c = racpTransitionCopy[lang];
  return <aside className="card" style={{ margin: "24px 0", padding: 24 }}>
    <h2 style={{ marginTop: 0 }}>{c.legacy}</h2>
    <p style={{ color: "var(--text-muted)", lineHeight: 1.7 }}>{c.legacyBody}</p>
    <Link href="/tokens/racp" className="btn btn-ghost">rACP · Robinhood Chain</Link>
  </aside>;
}

export function RacpUnitBar() {
  return <div className="market-rate-bar"><div className="market-rate-bar__inner">
    <Link href="/tokens/racp" className="market-rate-bar__link">rACP · Robinhood Chain</Link>
    <span>10 rACP = 1 ACP</span>
  </div></div>;
}

export function RacpEntry() {
  const { lang } = useLanguage();
  const c = racpTransitionCopy[lang];
  return <>
    <h1 style={{ fontSize: "clamp(1.8rem, 4vw, 2.8rem)" }}>{c.title}</h1>
    <p style={{ color: "var(--text-muted)", lineHeight: 1.7 }}>{c.lead}</p>
    <RacpOverview compact />
    <section className="card" style={{ padding: 24 }}>
      <h2>{c.redeem}</h2>
      <p style={{ color: "var(--text-muted)", lineHeight: 1.7 }}>{c.limits}</p>
      <div className="action-cluster">
        <Link href="/tokens/racp/redeem" className="btn btn-primary">{c.redeem}</Link>
        <Link href="/wallet/acp" className="btn btn-ghost">{c.wallet}</Link>
        <Link href="/ai/workflows" className="btn btn-ghost">{c.spend}</Link>
      </div>
    </section>
    <section style={{ margin: "24px 0" }}>
      <h2>{c.markets}</h2>
      <p style={{ color: "var(--text-muted)", lineHeight: 1.7 }}>{c.price}</p>
      <div className="action-cluster">
        <Link href="/tokens/racp" className="btn btn-ghost">{c.documents}</Link>
        <a href="/racp-listings.json" className="btn btn-ghost">rACP listings</a>
        <a href="/tokenlist.json" className="btn btn-ghost">Token list</a>
      </div>
    </section>
    <p style={{ color: "var(--text-muted)", lineHeight: 1.7 }}>{c.displayNote}</p>
  </>;
}
