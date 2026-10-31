"use client";

import Link from "next/link";
import { Navigation } from "@/components/Navigation";
import { useLanguage } from "@/components/LanguageProvider";

const PRODUCT_KEYS = [
  ["token-risk", "/paid-api/token-risk", "2.00 ACP", "productTokenRisk"],
  ["listing-readiness", "/paid-api/listing-readiness", "1.50 ACP", "productListing"],
  ["wallet-risk", "/paid-api/wallet-risk", "2.00 ACP", "productWallet"],
  ["bridge-proof", "/paid-api/bridge-proof", "1.00 ACP", "productBridge"],
  ["campaign-score", "/paid-api/campaign-score", "1.00 ACP", "productCampaign"],
] as const;

export function DevelopersContent() {
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <Navigation />
      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <section className="mb-8 rounded-3xl border border-emerald-400/20 bg-emerald-400/[0.06] p-6 sm:p-8">
          <div className="text-xs uppercase tracking-[0.18em] text-emerald-200/75">{t("developersPage.kicker")}</div>
          <h1 className="mt-3 max-w-4xl text-3xl font-semibold tracking-[-0.04em] sm:text-5xl">
            {t("developersPage.title")}
          </h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-white/72 sm:text-base">
            {t("developersPage.lead")}
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/developers/connect" className="rounded-full bg-emerald-400 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:opacity-90">
              {t("developersPage.createKey")}
            </Link>
            <Link href="/developers/usage" className="rounded-full border border-emerald-400/25 px-5 py-2.5 text-sm font-semibold text-emerald-200 transition hover:border-emerald-300/50 hover:text-emerald-100">
              {t("developersPage.usageDashboard")}
            </Link>
            <Link href="/billing" className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85 transition hover:border-white/30 hover:text-white">
              {t("developersPage.billingCredits")}
            </Link>
            <a href="/api/docs" className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85 transition hover:border-white/30 hover:text-white">
              {t("developersPage.openApiDocs")}
            </a>
            <a href="/agent-products.json" className="rounded-full border border-sky-300/25 bg-sky-400/[0.08] px-5 py-2.5 text-sm font-semibold text-sky-100 transition hover:border-sky-200/45 hover:text-white">
              {t("developersPage.agentProductJson")}
            </a>
          </div>
        </section>

        <section className="mb-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {PRODUCT_KEYS.map(([slug, endpoint, price, descKey]) => (
            <article key={slug} className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
              <div className="text-xs uppercase tracking-[0.18em] text-white/45">{endpoint}</div>
              <h2 className="mt-3 text-xl font-semibold tracking-[-0.02em]">{slug}</h2>
              <div className="mt-2 text-lg font-black text-emerald-300">{price}</div>
              <p className="mt-3 text-sm leading-6 text-white/65">{t(`developersPage.${descKey}`)}</p>
            </article>
          ))}
        </section>

        <section className="grid gap-6 lg:grid-cols-[1fr_0.8fr]">
          <article className="rounded-3xl border border-white/10 bg-white/[0.03] p-6">
            <h2 className="text-2xl font-semibold tracking-[-0.03em]">{t("developersPage.requestExample")}</h2>
            <pre className="mt-4 overflow-x-auto rounded-2xl border border-white/10 bg-black/25 p-4 text-sm text-white/80">{`curl -X POST https://ancap.cloud/api/v1/paid-api/token-risk \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: $ANCAP_API_KEY" \\
  -d '{"subject":"TOKEN","chain":"Base","signals":{"owner":"known","liquidity":"locked"}}'`}</pre>
            <h3 className="mt-6 text-lg font-semibold">{t("developersPage.paymentTerms")}</h3>
            <pre className="mt-4 overflow-x-auto rounded-2xl border border-emerald-400/20 bg-black/25 p-4 text-sm text-white/80">{JSON.stringify({
              status: 402,
              detail: {
                message: "Insufficient credits for paid API usage",
                x402: {
                  version: "x402-compatible-preview",
                  accepts: [{ scheme: "exact", network: "base", currency: "ACP", amount: "2.00" }],
                  resource: "https://ancap.cloud/api/v1/paid-api/token-risk",
                  pay_to: "ancap-workflow-treasury",
                },
              },
            }, null, 2)}</pre>
          </article>

          <aside className="rounded-3xl border border-white/10 bg-white/[0.03] p-6">
            <div className="text-sm font-semibold text-white/90">{t("developersPage.spendControls")}</div>
            <ul className="mt-4 space-y-3 text-sm text-white/70">
              <li>{t("developersPage.spendCap")}</li>
              <li>{t("developersPage.spendDebit")}</li>
              <li>{t("developersPage.spendExport")}</li>
              <li>{t("developersPage.spendReceipts")}</li>
            </ul>
            <Link href="/ai/run/agent-api-readiness-pack" className="mt-6 inline-flex rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:opacity-90">
              {t("developersPage.buyReadiness")}
            </Link>
          </aside>
        </section>

        <section className="mt-8 rounded-3xl border border-sky-300/15 bg-sky-400/[0.055] p-6">
          <div className="text-xs uppercase tracking-[0.18em] text-sky-100/75">{t("developersPage.discoveryKicker")}</div>
          <h2 className="mt-3 text-2xl font-semibold tracking-[-0.03em]">{t("developersPage.discoveryTitle")}</h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-white/70">{t("developersPage.discoveryLead")}</p>
          <div className="mt-5 grid gap-3 md:grid-cols-2">
            <a href="/llms.txt" className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-white/78 transition hover:border-sky-300/35 hover:text-white">
              <div className="font-semibold text-sky-100">/llms.txt</div>
              <div className="mt-2 leading-6">{t("developersPage.llmsHint")}</div>
            </a>
            <a href="/agent-products.json" className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-white/78 transition hover:border-sky-300/35 hover:text-white">
              <div className="font-semibold text-sky-100">/agent-products.json</div>
              <div className="mt-2 leading-6">{t("developersPage.productsJsonHint")}</div>
            </a>
          </div>
        </section>
      </main>
    </div>
  );
}
