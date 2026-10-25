"use client";

import Link from "next/link";
import { catalogPriceLabel } from "@/lib/workflowStore";
import { Navigation } from "@/components/Navigation";
import { useLanguage } from "@/components/LanguageProvider";

type Money = { amount: string; currency: string };

type PricingBundle = {
  slug: string;
  category: string;
  title: string;
  summary: string;
  price: Money;
  usd_sticker?: Money | null;
  price_acp?: Money | null;
  output_items: string[];
};

type PricingWorkflow = {
  slug: string;
  category: string;
  title: string;
  description: string;
  price: Money;
  usd_sticker?: Money | null;
  price_acp?: Money | null;
};

const TIERS = [
  ["pricing.tierFree", "pricing.tierFreePrice", "pricing.tierFreeText"],
  ["pricing.tierPro", "pricing.tierProPrice", "pricing.tierProText"],
  ["pricing.tierCreator", "pricing.tierCreatorPrice", "pricing.tierCreatorText"],
  ["pricing.tierMerchant", "pricing.tierMerchantPrice", "pricing.tierMerchantText"],
  ["pricing.tierDeveloper", "pricing.tierDeveloperPrice", "pricing.tierDeveloperText"],
  ["pricing.tierEnterprise", "pricing.tierEnterprisePrice", "pricing.tierEnterpriseText"],
] as const;

function PriceFace({ item }: { item: { price: Money; usd_sticker?: Money | null; price_acp?: Money | null } }) {
  return <div className="text-3xl font-black text-emerald-300">{catalogPriceLabel(item)}</div>;
}

export function PricingView({
  bundles,
  workflows,
}: {
  bundles: PricingBundle[];
  workflows: PricingWorkflow[];
}) {
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <Navigation />
      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <section className="mb-8">
          <div className="text-xs uppercase tracking-[0.18em] text-emerald-300">{t("pricing.eyebrow")}</div>
          <h1 className="mt-3 max-w-4xl text-3xl font-semibold tracking-[-0.04em] sm:text-5xl">
            {t("pricing.title")}
          </h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-white/68 sm:text-base">
            {t("pricing.subtitle")}
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/token-snapshot" className="rounded-full bg-emerald-400 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:opacity-90">
              {t("pricing.freeSnapshot")}
            </Link>
            <Link href="/sample-reports/token-risk-report-pro" className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85 transition hover:border-white/30 hover:text-white">
              {t("pricing.sampleReport")}
            </Link>
            <Link href="/dashboard/seller" className="rounded-full border border-sky-300/25 bg-sky-400/[0.08] px-5 py-2.5 text-sm font-semibold text-sky-100 transition hover:border-sky-200/45 hover:text-white">
              {t("pricing.sellWorkflows")}
            </Link>
          </div>
        </section>

        <section className="mb-10 grid gap-4 md:grid-cols-3 lg:grid-cols-6">
          {TIERS.map(([titleKey, priceKey, textKey]) => (
            <div key={titleKey} className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
              <div className="text-sm font-semibold text-white/90">{t(titleKey)}</div>
              <div className="mt-2 text-lg font-bold text-emerald-300">{t(priceKey)}</div>
              <p className="mt-2 text-sm leading-6 text-white/62">{t(textKey)}</p>
            </div>
          ))}
        </section>

        <section className="mb-10 grid gap-5 lg:grid-cols-3">
          {bundles.map((bundle) => (
            <article key={bundle.slug} className="rounded-3xl border border-emerald-400/20 bg-emerald-400/[0.06] p-6">
              <div className="text-xs uppercase tracking-[0.18em] text-emerald-200/75">{bundle.category}</div>
              <h2 className="mt-3 text-2xl font-semibold tracking-[-0.03em]">{bundle.title}</h2>
              <div className="mt-3">
                <PriceFace item={bundle} />
              </div>
              <p className="mt-4 text-sm leading-6 text-white/70">{bundle.summary}</p>
              <ul className="mt-5 space-y-2 text-sm text-white/75">
                {bundle.output_items.slice(0, 5).map((item) => (
                  <li key={item} className="flex gap-2">
                    <span className="mt-2 h-1.5 w-1.5 rounded-full bg-emerald-300" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
              <Link href={`/ai/bundles/${bundle.slug}`} className="mt-6 inline-flex rounded-full bg-emerald-400 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:opacity-90">
                {t("pricing.buyBundle")}
              </Link>
            </article>
          ))}
        </section>

        <section>
          <div className="mb-4 flex flex-wrap items-end justify-between gap-4">
            <div>
              <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("pricing.singleEyebrow")}</div>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em]">{t("pricing.singleTitle")}</h2>
            </div>
            <Link href="/token-snapshot" className="rounded-full border border-white/15 px-4 py-2 text-sm font-semibold text-white/85 transition hover:border-white/30 hover:text-white">
              {t("pricing.tryFreeSnapshot")}
            </Link>
          </div>
          <div className="grid gap-5 md:grid-cols-3">
            {workflows.map((workflow) => (
              <article key={workflow.slug} className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                <div className="flex items-start justify-between gap-3">
                  <span className="rounded-full border border-white/12 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-white/55">{workflow.category}</span>
                  <div className="text-right">
                    {workflow.usd_sticker?.amount ? (
                      <>
                        <strong className="text-emerald-300">${workflow.usd_sticker.amount}</strong>
                        <div className="text-[11px] text-white/45">≈ {(workflow.price_acp || workflow.price).amount} ACP</div>
                      </>
                    ) : (
                      <strong className="text-emerald-300">{workflow.price.amount} {workflow.price.currency}</strong>
                    )}
                  </div>
                </div>
                <h3 className="mt-4 text-xl font-semibold tracking-[-0.02em]">{workflow.title}</h3>
                <p className="mt-3 text-sm leading-6 text-white/68">{workflow.description}</p>
                <div className="mt-5 flex flex-wrap gap-2">
                  <Link href={`/ai/run/${workflow.slug}`} className="rounded-full bg-emerald-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:opacity-90">
                    {t("pricing.buyWorkflow")}
                  </Link>
                  <Link href={`/sample-reports/${workflow.slug}`} className="rounded-full border border-white/15 px-4 py-2 text-sm font-semibold text-white/80 transition hover:border-white/25 hover:text-white">
                    {t("pricing.sample")}
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
