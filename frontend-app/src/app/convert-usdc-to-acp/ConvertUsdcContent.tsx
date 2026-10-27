"use client";

import Link from "next/link";
import { Navigation } from "@/components/Navigation";
import { useLanguage } from "@/components/LanguageProvider";

export function ConvertUsdcContent() {
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <Navigation />
      <main className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="text-3xl font-semibold">{t("convertUsdcPage.title")}</h1>
        <p className="mt-3 text-sm leading-7 text-white/68">{t("convertUsdcPage.lead")}</p>
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <Link href="/bridge" className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 hover:border-white/20">
            <div className="font-semibold">{t("convertUsdcPage.bscBridge")}</div>
            <p className="mt-2 text-sm text-white/60">{t("convertUsdcPage.bscBridgeLead")}</p>
          </Link>
          <Link href="/pay-with-stablecoin" className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 hover:border-white/20">
            <div className="font-semibold">{t("convertUsdcPage.partnerRamp")}</div>
            <p className="mt-2 text-sm text-white/60">{t("convertUsdcPage.partnerRampLead")}</p>
          </Link>
          <Link href="/buy-acp" className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 hover:border-white/20">
            <div className="font-semibold">{t("convertUsdcPage.cardCheckout")}</div>
            <p className="mt-2 text-sm text-white/60">{t("convertUsdcPage.cardCheckoutLead")}</p>
          </Link>
          <Link href="/compliance" className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 hover:border-white/20">
            <div className="font-semibold">{t("convertUsdcPage.complianceMatrix")}</div>
            <p className="mt-2 text-sm text-white/60">{t("convertUsdcPage.complianceMatrixLead")}</p>
          </Link>
        </div>
      </main>
    </div>
  );
}
