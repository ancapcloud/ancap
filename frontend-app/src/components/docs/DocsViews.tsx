"use client";

import Link from "next/link";
import { Navigation } from "@/components/Navigation";
import { WacpPublicActions } from "@/components/WacpPublicActions";
import { useLanguage } from "@/components/LanguageProvider";

export function WacpDocsOverviewView() {
  const { t } = useLanguage();
  return (
    <div className="min-h-screen">
      <Navigation />
      <main className="container" style={{ padding: "48px 24px 72px" }}>
        <section style={{ padding: "24px 0 32px" }}>
          <div className="card">
            <div className="card-header">
              <div>
                <div className="section-num" style={{ marginBottom: 10 }}>wACP</div>
                <h1 style={{ fontSize: "clamp(1.8rem, 4vw, 2.8rem)", fontWeight: 800, margin: 0 }}>{t("docsWacp.overviewTitle")}</h1>
              </div>
              <span className="badge badge-active">{t("docsWacp.overviewBadge")}</span>
            </div>
            <p style={{ color: "var(--text-muted)", lineHeight: 1.75, marginTop: 16, maxWidth: 900 }}>{t("docsWacp.overviewLead")}</p>
          </div>
        </section>
        <section className="responsive-grid responsive-grid-2" style={{ gap: 16 }}>
          <div className="card">
            <h3 style={{ marginTop: 0 }}>{t("docsWacp.readNext")}</h3>
            <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.9 }}>
              <li><Link href="/docs/wacp/bridge">{t("docsWacp.bridgeFlow")}</Link></li>
              <li><Link href="/docs/wacp/reserve">{t("docsWacp.reserveModel")}</Link></li>
              <li><Link href="/docs/wacp/risks">{t("docsWacp.riskDisclosures")}</Link></li>
              <li><Link href="/docs/wacp/contracts">{t("docsWacp.contracts")}</Link></li>
              <li><Link href="/docs/wacp/pancakeswap">{t("docsWacp.pancakeswap")}</Link></li>
              <li><Link href="/markets">{t("docsWacp.markets")}</Link></li>
            </ul>
          </div>
          <div className="card">
            <h3 style={{ marginTop: 0 }}>{t("docsWacp.currentState")}</h3>
            <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.9, color: "var(--text-muted)" }}>
              <li>wACP bridge UI exists at <code>/bridge/acp-bsc</code></li>
              <li>Both public bridge directions are now live: <code>ACP -&gt; BSC</code> mint and <code>BSC -&gt; ACP</code> redeem</li>
              <li>ACP deposit tx viewer exists at <code>/acp/tx/[txid]</code></li>
              <li>Public API status endpoints are live at <code>/api/v1/wacp/status</code> and <code>/api/v1/wacp/reserve-proof</code></li>
              <li>PancakeSwap V2 technical liquidity bootstrap for <code>wACP/USDT</code> is live; GeckoTerminal indexes the pool; official token list at <code>/tokenlist.json</code></li>
            </ul>
          </div>
        </section>
      </main>
    </div>
  );
}

export function WacpBridgeDocsView() {
  const { t } = useLanguage();
  return (
    <div className="min-h-screen">
      <Navigation />
      <main className="container" style={{ padding: "48px 24px 72px" }}>
        <div className="card">
          <div className="card-header">
            <h1 style={{ margin: 0, fontWeight: 800 }}>{t("docsWacp.bridgeTitle")}</h1>
            <span className="badge badge-active">{t("docsWacp.bridgeBadge")}</span>
          </div>
          <p style={{ color: "var(--text-muted)", lineHeight: 1.75 }}>{t("docsWacp.bridgeLead")}</p>
          <ol style={{ lineHeight: 1.9, color: "var(--text-muted)" }}>
            <li>{t("docsWacp.step1")}</li>
            <li>{t("docsWacp.step2")}</li>
            <li>{t("docsWacp.step3")}</li>
            <li>{t("docsWacp.step4")}</li>
            <li>{t("docsWacp.step5")}</li>
            <li>{t("docsWacp.step6")}</li>
          </ol>
          <div style={{ marginTop: 16, padding: 14, borderRadius: 12, border: "1px solid rgba(245, 158, 11, 0.3)", background: "rgba(245, 158, 11, 0.08)", color: "var(--text-muted)", lineHeight: 1.75 }}>
            <strong style={{ color: "var(--text)" }}>{t("docsWacp.reverseStatus")}</strong> {t("docsWacp.reverseBody")}
          </div>
        </div>
      </main>
    </div>
  );
}

export function WacpReserveDocsView() {
  const { t } = useLanguage();
  return (
    <div className="min-h-screen">
      <Navigation />
      <main className="container" style={{ padding: "48px 24px 72px" }}>
        <div className="card">
          <div className="card-header">
            <h1 style={{ margin: 0, fontWeight: 800 }}>{t("docsWacp.reserveTitle")}</h1>
            <span className="badge badge-info">{t("docsWacp.reserveBadge")}</span>
          </div>
          <p style={{ color: "var(--text-muted)", lineHeight: 1.75 }}>{t("docsWacp.reserveLead")}</p>
          <ul style={{ lineHeight: 1.9, color: "var(--text-muted)" }}>
            <li>{t("docsWacp.healthy")}</li>
            <li>{t("docsWacp.degraded")}</li>
            <li>{t("docsWacp.critical")}</li>
          </ul>
          <p style={{ color: "var(--text-muted)", lineHeight: 1.75 }}>{t("docsWacp.reserveApi")}</p>
        </div>
      </main>
    </div>
  );
}

export function WacpRisksDocsView() {
  const { t } = useLanguage();
  return (
    <div className="min-h-screen">
      <Navigation />
      <main className="container" style={{ padding: "48px 24px 72px" }}>
        <div className="card">
          <div className="card-header">
            <h1 style={{ margin: 0, fontWeight: 800 }}>{t("docsWacp.risksTitle")}</h1>
            <span className="badge badge-active">{t("docsWacp.risksBadge")}</span>
          </div>
          <ul style={{ lineHeight: 1.9, color: "var(--text-muted)" }}>
            <li>{t("docsWacp.risk1")}</li>
            <li>{t("docsWacp.risk2")}</li>
            <li>{t("docsWacp.risk3")}</li>
            <li>{t("docsWacp.risk4")}</li>
            <li>{t("docsWacp.risk5")}</li>
            <li>{t("docsWacp.risk6")}</li>
          </ul>
        </div>
      </main>
    </div>
  );
}

export function WacpContractsDocsView() {
  const { t } = useLanguage();
  return (
    <div className="min-h-screen">
      <Navigation />
      <main className="container" style={{ padding: "48px 24px 72px" }}>
        <div className="card">
          <div className="card-header">
            <h1 style={{ margin: 0, fontWeight: 800 }}>{t("docsWacp.contractsTitle")}</h1>
            <span className="badge badge-info">{t("docsWacp.contractsBadge")}</span>
          </div>
          <div style={{ display: "grid", gap: 12, color: "var(--text-muted)", lineHeight: 1.75 }}>
            <div><strong style={{ color: "var(--text)" }}>wACP contract:</strong> 0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402</div>
            <div><strong style={{ color: "var(--text)" }}>Bridge / gateway contract:</strong> 0x57c24FF77B23a82328cb88914D4FD4EEBd93321b</div>
            <div><strong style={{ color: "var(--text)" }}>ACP reserve address:</strong> acp1qrz3ksr8gpv4ah208t5qvzxx0f4vc7a7ws7uqluz</div>
            <div><strong style={{ color: "var(--text)" }}>Chain IDs:</strong> ACP native chain / BNB Smart Chain (56)</div>
            <div><strong style={{ color: "var(--text)" }}>Verification:</strong> BscScan source match completed for the production wACP contract</div>
            <div><strong style={{ color: "var(--text)" }}>Pool:</strong> 0xF391ca2bcBaB93Afa23326ebF1e35DB950841601</div>
            <div><strong style={{ color: "var(--text)" }}>{t("docsWacp.contractsWarning")}</strong></div>
            <div style={{ marginTop: 8 }}>
              <WacpPublicActions layout="home" />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export function WacpPancakeDocsView() {
  const { t } = useLanguage();
  return (
    <div className="min-h-screen">
      <Navigation />
      <main className="container" style={{ padding: "48px 24px 72px" }}>
        <div className="card">
          <div className="card-header">
            <h1 style={{ margin: 0, fontWeight: 800 }}>{t("docsWacp.pancakeswapTitle")}</h1>
            <span className="badge badge-active">{t("docsWacp.pancakeswapBadge")}</span>
          </div>
          <p style={{ color: "var(--text-muted)", lineHeight: 1.75 }}>{t("docsWacp.pancakeswapLead")}</p>
        </div>
      </main>
    </div>
  );
}

export function SacpDocsOverviewView() {
  const { t } = useLanguage();
  return (
    <div className="min-h-screen">
      <Navigation />
      <main className="container" style={{ padding: "48px 24px 72px" }}>
        <section style={{ padding: "24px 0 32px" }}>
          <div className="card">
            <div className="card-header">
              <div>
                <div className="section-num" style={{ marginBottom: 10 }}>sACP</div>
                <h1 style={{ fontSize: "clamp(1.8rem, 4vw, 2.8rem)", fontWeight: 800, margin: 0 }}>{t("docsSacp.overviewTitle")}</h1>
              </div>
              <span className="badge badge-active">{t("docsSacp.overviewBadge")}</span>
            </div>
            <p style={{ color: "var(--text-muted)", lineHeight: 1.75, marginTop: 16, maxWidth: 900 }}>{t("docsSacp.overviewLead")}</p>
          </div>
        </section>
        <section className="responsive-grid responsive-grid-2" style={{ gap: 16 }}>
          <div className="card">
            <h3 style={{ marginTop: 0 }}>{t("docsSacp.readNext")}</h3>
            <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.9 }}>
              <li><Link href="/docs/sacp/reserve">{t("docsSacp.reserveLink")}</Link></li>
              <li><Link href="/docs/sacp/risks">{t("docsSacp.risksLink")}</Link></li>
              <li><Link href="/docs/wacp">{t("docsSacp.compareWacp")}</Link></li>
              <li><a href="https://github.com/dragoncattrx-hub/ancap/blob/master/docs/STABLECOIN_SACP_SPEC.md">{t("docsSacp.specLink")}</a></li>
            </ul>
          </div>
          <div className="card">
            <h3 style={{ marginTop: 0 }}>{t("docsSacp.publicApi")}</h3>
            <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.9, color: "var(--text-muted)" }}>
              <li><code>/api/v1/sacp/status</code></li>
              <li><code>/api/v1/sacp/reserve-proof</code></li>
              <li>Exchange catalog asset: <code>sacp_bsc</code></li>
              <li>Contract source: <code>contracts/bridge-bsc/src/SACP.sol</code></li>
            </ul>
          </div>
        </section>
      </main>
    </div>
  );
}

export function SacpReserveDocsView() {
  const { t } = useLanguage();
  return (
    <div className="min-h-screen">
      <Navigation />
      <main className="container" style={{ padding: "48px 24px 72px" }}>
        <div className="card">
          <div className="card-header">
            <div>
              <div className="section-num" style={{ marginBottom: 10 }}>sACP</div>
              <h1 style={{ margin: 0, fontWeight: 800 }}>{t("docsSacp.reserveTitle")}</h1>
            </div>
            <Link href="/docs/sacp">{t("docsSacp.overviewLink")}</Link>
          </div>
          <p style={{ color: "var(--text-muted)", lineHeight: 1.75, marginTop: 16, maxWidth: 900 }}>{t("docsSacp.reserveLead1")}</p>
          <p style={{ color: "var(--text-muted)", lineHeight: 1.75, maxWidth: 900 }}>{t("docsSacp.reserveLead2")}</p>
          <p style={{ marginTop: 24 }}>
            <Link href="/api/v1/sacp/reserve-proof">{t("docsSacp.liveProof")}</Link>
          </p>
        </div>
      </main>
    </div>
  );
}

export function SacpRisksDocsView() {
  const { t } = useLanguage();
  return (
    <div className="min-h-screen">
      <Navigation />
      <main className="container" style={{ padding: "48px 24px 72px" }}>
        <div className="card">
          <div className="card-header">
            <div>
              <div className="section-num" style={{ marginBottom: 10 }}>sACP</div>
              <h1 style={{ margin: 0, fontWeight: 800 }}>{t("docsSacp.risksTitle")}</h1>
            </div>
            <Link href="/docs/sacp">{t("docsSacp.overviewLink")}</Link>
          </div>
          <ul style={{ color: "var(--text-muted)", lineHeight: 1.9, maxWidth: 900 }}>
            <li><strong>{t("docsSacp.risk1Title")}</strong> {t("docsSacp.risk1Body")}</li>
            <li><strong>{t("docsSacp.risk2Title")}</strong> {t("docsSacp.risk2Body")}</li>
            <li><strong>{t("docsSacp.risk3Title")}</strong> {t("docsSacp.risk3Body")}</li>
            <li><strong>{t("docsSacp.risk4Title")}</strong> {t("docsSacp.risk4Body")}</li>
            <li><strong>{t("docsSacp.risk5Title")}</strong> {t("docsSacp.risk5Body")}</li>
          </ul>
        </div>
      </main>
    </div>
  );
}

export function MobileSecurityDocsView() {
  const { t } = useLanguage();
  const controls = [
    ["ctrl1Title", "ctrl1Body"],
    ["ctrl2Title", "ctrl2Body"],
    ["ctrl3Title", "ctrl3Body"],
    ["ctrl4Title", "ctrl4Body"],
    ["ctrl5Title", "ctrl5Body"],
  ] as const;
  const gates = ["gate1", "gate2", "gate3", "gate4"] as const;

  return (
    <div className="min-h-screen">
      <Navigation />
      <main className="container" style={{ padding: "48px 24px 72px" }}>
        <section className="card">
          <div className="card-header">
            <div>
              <div className="section-num" style={{ marginBottom: 10 }}>{t("docsMobileSecurity.kicker")}</div>
              <h1 style={{ margin: 0, fontWeight: 800 }}>{t("docsMobileSecurity.title")}</h1>
            </div>
            <span className="badge badge-active">{t("docsMobileSecurity.badge")}</span>
          </div>
          <p style={{ color: "var(--text-muted)", lineHeight: 1.75, marginTop: 16, maxWidth: 920 }}>{t("docsMobileSecurity.lead")}</p>
          <div style={{ marginTop: 16, padding: 14, borderRadius: 12, border: "1px solid rgba(56, 189, 248, 0.24)", background: "rgba(56, 189, 248, 0.08)", color: "var(--text-muted)", lineHeight: 1.75 }}>
            <strong style={{ color: "var(--text)" }}>{t("docsMobileSecurity.releaseTruth")}</strong> {t("docsMobileSecurity.releaseBody")}
          </div>
        </section>
        <section className="responsive-grid responsive-grid-2" style={{ gap: 16, marginTop: 16 }}>
          <article className="card">
            <h2 style={{ marginTop: 0 }}>{t("docsMobileSecurity.baselineTitle")}</h2>
            <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.9, color: "var(--text-muted)" }}>
              {controls.map(([titleKey, bodyKey]) => (
                <li key={titleKey}>
                  <strong style={{ color: "var(--text)" }}>{t(`docsMobileSecurity.${titleKey}`)}:</strong> {t(`docsMobileSecurity.${bodyKey}`)}
                </li>
              ))}
            </ul>
          </article>
          <article className="card">
            <h2 style={{ marginTop: 0 }}>{t("docsMobileSecurity.remainingTitle")}</h2>
            <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.9, color: "var(--text-muted)" }}>
              {gates.map((key) => (
                <li key={key}>{t(`docsMobileSecurity.${key}`)}</li>
              ))}
            </ul>
          </article>
        </section>
        <section className="card" style={{ marginTop: 16 }}>
          <h2 style={{ marginTop: 0 }}>{t("docsMobileSecurity.readNext")}</h2>
          <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.9 }}>
            <li><Link href="/docs/wacp/bridge">{t("docsMobileSecurity.bridgeFlow")}</Link></li>
            <li><Link href="/docs/wacp/risks">{t("docsMobileSecurity.bridgeRisks")}</Link></li>
            <li><Link href="/legal/terms">{t("docsMobileSecurity.terms")}</Link></li>
            <li><Link href="/legal/privacy">{t("docsMobileSecurity.privacy")}</Link></li>
            <li><Link href="/legal/cyber-defense">{t("docsMobileSecurity.cyberDefense")}</Link></li>
          </ul>
        </section>
      </main>
    </div>
  );
}
