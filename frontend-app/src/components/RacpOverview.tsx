"use client";
import Link from "next/link";
import { useState } from "react";
import { useLanguage } from "./LanguageProvider";
import { racpCopy } from "@/locales/racp";
import { RACP_CONTRACT, RACP_EXPLORER, RACP_FUNDING_TX, RACP_ISSUANCE_TX, RACP_RESERVE, watchRacpInWallet } from "@/lib/racpToken";
import styles from "./RacpOverview.module.css";
import { racpAirdropCopy } from "@/locales/racpAirdrop";
import { racpRedeemCopy } from "@/locales/racpRedeem";

export function RacpOverview({ compact = false }: { compact?: boolean }) {
  const { lang } = useLanguage();
  const c = racpCopy[lang];
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const Heading = compact ? "h2" : "h1";
  async function add() {
    setBusy(true); setMessage("");
    try { setMessage(await watchRacpInWallet() ? c.added : c.error); }
    catch { setMessage(c.error); }
    finally { setBusy(false); }
  }
  async function copy() {
    try { await navigator.clipboard.writeText(RACP_CONTRACT); setMessage(c.copied); }
    catch { setMessage(RACP_CONTRACT); }
  }
  return <section className="card" aria-label="Robinhood ACP" style={{ padding: "clamp(20px, 4vw, 36px)", margin: "24px 0", overflow: "hidden" }}>
    <div className={styles.header}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/racp-logo.svg" width={52} height={52} alt="rACP" />
      <div className={styles.identity}><p className="section-num">ANCAP · ROBINHOOD CHAIN</p><Heading style={{ fontSize: compact ? "1.6rem" : "clamp(2rem, 5vw, 3.2rem)", margin: "4px 0" }}>Robinhood ACP <span style={{ color: "var(--accent-strong)" }}>rACP</span></Heading></div>
      <span className={`badge ${styles.badge}`}>ERC-20 · 4663</span>
    </div>
    <p style={{ color: "var(--text-muted)", lineHeight: 1.7, margin: "16px 0" }}>{c.lead}</p>
    <dl className="responsive-grid responsive-grid-3" style={{ gap: 20, margin: "24px 0" }}>
      {[[c.supply, new Intl.NumberFormat(lang).format(10_000_000)], [c.reserve, new Intl.NumberFormat(lang).format(1_000_000)], [c.ratio, "1 ACP = 10 rACP"]].map(([label, value]) => <div key={label}><dt style={{ color: "var(--text-muted)", fontSize: ".85rem" }}>{label}</dt><dd style={{ margin: "8px 0 0", fontWeight: 750, fontSize: "1.3rem" }}>{value}</dd></div>)}
    </dl>
    <code style={{ display: "block", overflowWrap: "anywhere", fontSize: ".85rem", padding: 12, background: "var(--bg)", borderRadius: 8 }}>{RACP_CONTRACT}</code>
    <div className="action-cluster" style={{ marginTop: 18 }}>
      <Link className="btn btn-primary" href="/tokens/racp/airdrop">{racpAirdropCopy[lang].title}</Link>
      <Link className="btn btn-primary" href="/tokens/racp/redeem">{racpRedeemCopy[lang].title}</Link>
      <button type="button" className="btn btn-primary" disabled={busy} aria-busy={busy} onClick={() => void add()}>{busy ? c.opening : c.add}</button>
      {compact ? <Link className="btn btn-ghost" href="/tokens/racp">{c.details} →</Link> : <button type="button" className="btn btn-ghost" onClick={() => void copy()}>{c.copy}</button>}
      <a className="btn btn-ghost" href={`${RACP_EXPLORER}/address/${RACP_CONTRACT}?tab=contract`} target="_blank" rel="noopener noreferrer">{c.explorer} ↗</a>
    </div>
    <p role="status" aria-live="polite" style={{ margin: "8px 0", color: "var(--text-muted)" }}>{message}</p>
    <p style={{ color: "var(--text-muted)", fontSize: ".87rem", lineHeight: 1.7 }}>{c.limits}</p>
    {!compact && <>
      <div className="action-cluster" style={{ marginTop: 20 }}>
        <a href={`/acp/tx/${RACP_FUNDING_TX}`}>{c.funding} ↗</a>
        <a href={`${RACP_EXPLORER}/tx/${RACP_ISSUANCE_TX}`} target="_blank" rel="noopener noreferrer">{c.issue} ↗</a>
        <a href={`/api/v1/acp/address/${RACP_RESERVE}/balance`} target="_blank" rel="noopener noreferrer">{c.balance} ↗</a>
        <a href="/tokenlist.json">tokenlist.json</a>
        <a href="/whitepaper/racp.md">Whitepaper</a>
        <a href={`https://repo.sourcify.dev/4663/${RACP_CONTRACT}`} target="_blank" rel="noopener noreferrer">Sourcify ✓</a>
        <a href="/racp-listings.json">Listings JSON</a>
      </div>
      <p style={{ overflowWrap: "anywhere", fontSize: ".85rem", marginTop: 20 }}>ACP: <code>{RACP_RESERVE}</code></p>
      <p style={{ color: "var(--text-muted)", lineHeight: 1.7 }}>{c.listing}</p>
    </>}
  </section>;
}
