"use client";

import Link from "next/link";
import { Navigation } from "@/components/Navigation";
import { useLanguage } from "@/components/LanguageProvider";

export function PayLandingContent() {
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <Navigation />
      <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="text-xs uppercase tracking-[0.18em] text-emerald-300">{t("payPage.kicker")}</div>
        <h1 className="mt-3 text-3xl font-semibold tracking-[-0.04em] sm:text-5xl">{t("payPage.title")}</h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/68 sm:text-base">{t("payPage.lead")}</p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/pay/create" className="rounded-full bg-emerald-400 px-5 py-2.5 text-sm font-semibold text-slate-950">
            {t("payPage.createLink")}
          </Link>
          <Link href="/invoices" className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85">
            {t("payPage.createInvoice")}
          </Link>
          <Link href="/merchant" className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85">
            {t("payPage.merchantDashboard")}
          </Link>
        </div>
      </main>
    </div>
  );
}
