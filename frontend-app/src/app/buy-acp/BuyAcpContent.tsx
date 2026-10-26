"use client";

import Link from "next/link";
import { Navigation } from "@/components/Navigation";
import { useLanguage } from "@/components/LanguageProvider";

export function BuyAcpContent() {
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <Navigation />
      <main className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="text-3xl font-semibold">{t("buyAcpPage.title")}</h1>
        <p className="mt-3 text-sm leading-7 text-white/68">{t("buyAcpPage.lead")}</p>

        <section className="mt-8 space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-emerald-300/90">{t("buyAcpPage.acpFirstHeading")}</h2>
          <div className="flex flex-wrap gap-3">
            <Link href="/wallet/acp" className="rounded-full bg-emerald-400 px-5 py-2.5 text-sm font-semibold text-slate-950">
              {t("buyAcpPage.usdtSwap")}
            </Link>
            <Link href="/bridge" className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85">
              {t("buyAcpPage.bridgeWacp")}
            </Link>
            <Link href="/wallet/credits" className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85">
              {t("buyAcpPage.creditsInvoice")}
            </Link>
            <Link href="/ai/workflows" className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85">
              {t("buyAcpPage.spendWorkflows")}
            </Link>
          </div>
          <p className="text-xs leading-6 text-white/50">{t("buyAcpPage.mobileHint")}</p>
        </section>

        <section className="mt-10 space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-white/55">{t("buyAcpPage.fiatHeading")}</h2>
          <div className="flex flex-wrap gap-3">
            <Link href="/wallet/top-up" className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85">
              {t("buyAcpPage.cardTopUp")}
            </Link>
            <Link href="/pricing" className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85">
              {t("buyAcpPage.pricing")}
            </Link>
          </div>
        </section>

        <div className="mt-10 rounded-2xl border border-amber-400/20 bg-amber-400/[0.06] p-5 text-sm text-amber-100/90">
          {t("buyAcpPage.disclaimer")}
        </div>
      </main>
    </div>
  );
}
