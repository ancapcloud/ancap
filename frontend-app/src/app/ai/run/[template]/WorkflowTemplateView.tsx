"use client";

import Link from "next/link";
import { Navigation } from "@/components/Navigation";
import { useLanguage } from "@/components/LanguageProvider";
import { WorkflowRunPanel } from "@/components/workflow/WorkflowRunPanel";
import type { WorkflowTemplate } from "@/lib/workflowStore";

export function WorkflowTemplateView({ workflow }: { workflow: WorkflowTemplate }) {
  const { t } = useLanguage();

  const flowSteps = [
    [
      t("workflowTemplatePage.stepQuote"),
      t("workflowTemplatePage.stepQuoteValue")
        .replace("{amount}", workflow.price.amount)
        .replace("{currency}", workflow.price.currency),
    ],
    [t("workflowTemplatePage.stepPayment"), t("workflowTemplatePage.stepPaymentValue")],
    [t("workflowTemplatePage.stepReceipt"), t("workflowTemplatePage.stepReceiptValue")],
    [t("workflowTemplatePage.stepProof"), t("workflowTemplatePage.stepProofValue")],
  ] as const;

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <Navigation />
      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link href="/ai/workflows" className="text-sm text-emerald-300 hover:text-emerald-200">
            {t("workflowTemplatePage.backToCatalog")}
          </Link>
        </div>

        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 sm:p-8">
            <div className="mb-3 inline-flex rounded-full border border-white/12 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.18em] text-white/55">
              {workflow.category}
            </div>
            <h1 className="text-3xl font-semibold tracking-[-0.04em] sm:text-5xl">{workflow.title}</h1>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-white/72 sm:text-base">{workflow.summary}</p>
            <p className="mt-4 rounded-2xl border border-emerald-400/15 bg-emerald-400/8 p-4 text-sm leading-6 text-emerald-100/90">
              {workflow.description}
            </p>

            <div className="mt-6 flex flex-wrap gap-2">
              {workflow.tags.map((tag) => (
                <span key={tag} className="rounded-full border border-white/12 px-3 py-1 text-xs text-white/60">
                  {tag}
                </span>
              ))}
            </div>

            <div className="mt-8 grid gap-6 md:grid-cols-2">
              <div>
                <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowTemplatePage.previewIncludes")}</div>
                <ul className="mt-4 space-y-3 text-sm text-white/75">
                  {workflow.preview_items.map((item) => (
                    <li key={item} className="flex items-start gap-3">
                      <span className="mt-2 h-1.5 w-1.5 rounded-full bg-emerald-300" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowTemplatePage.expectedOutputs")}</div>
                <ul className="mt-4 space-y-3 text-sm text-white/75">
                  {workflow.output_items.map((item) => (
                    <li key={item} className="flex items-start gap-3">
                      <span className="mt-2 h-1.5 w-1.5 rounded-full bg-emerald-300" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href={`/sample-reports/${workflow.slug}`} className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85 transition hover:border-white/30 hover:text-white">
                {t("workflowTemplatePage.viewSampleOutput")}
              </Link>
              <Link href="/proof-center" className="rounded-full border border-emerald-400/25 px-5 py-2.5 text-sm font-semibold text-emerald-200 transition hover:border-emerald-300/50 hover:text-emerald-100">
                {t("workflowTemplatePage.howProofWorks")}
              </Link>
            </div>
          </div>

          <aside className="rounded-3xl border border-white/10 bg-white/[0.03] p-6">
            <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowTemplatePage.runSummary")}</div>
            <div className="mt-4 flex items-end justify-between gap-3">
              <div>
                <div className="text-sm text-white/55">{t("workflowTemplatePage.price")}</div>
                <div className="mt-1 text-2xl font-semibold text-emerald-300">
                  {t("workflowTemplatePage.fromPrice")
                    .replace("{amount}", workflow.price.amount)
                    .replace("{currency}", workflow.price.currency)}
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-white/55">{t("workflowTemplatePage.eta")}</div>
                <div className="mt-1 text-base font-medium text-white/90">
                  {workflow.estimated_time_minutes} {t("workflowTemplatePage.minUnit")}
                </div>
              </div>
            </div>
            {workflow.billing === "subscription" ? (
              <div className="mt-4 rounded-2xl border border-emerald-400/20 bg-emerald-400/[0.06] p-4 text-sm text-white/75">
                <div className="text-xs uppercase tracking-[0.18em] text-emerald-200/80">{t("workflowTemplatePage.subscription")}</div>
                <ul className="mt-2 space-y-1 font-mono text-xs text-emerald-100/90">
                  {workflow.subscription_price_monthly ? (
                    <li>
                      {t("workflowTemplatePage.monthly")} {workflow.subscription_price_monthly.amount} {workflow.subscription_price_monthly.currency}
                    </li>
                  ) : null}
                  {workflow.subscription_price_quarterly ? (
                    <li>
                      {t("workflowTemplatePage.quarterly")} {workflow.subscription_price_quarterly.amount} {workflow.subscription_price_quarterly.currency}
                    </li>
                  ) : null}
                  {workflow.subscription_price_annual ? (
                    <li>
                      {t("workflowTemplatePage.annual")} {workflow.subscription_price_annual.amount} {workflow.subscription_price_annual.currency}
                    </li>
                  ) : null}
                </ul>
                <p className="mt-2 text-xs leading-5 text-white/50">{t("workflowTemplatePage.subscriptionRenewalNote")}</p>
              </div>
            ) : null}

            <div className="mt-6 rounded-2xl border border-white/10 bg-black/15 p-4">
              <div className="text-sm font-semibold">{t("workflowTemplatePage.receiptProofIncludes")}</div>
              <ul className="mt-3 space-y-2 text-sm text-white/70">
                {workflow.receipt_items.map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <span className="mt-2 h-1.5 w-1.5 rounded-full bg-emerald-300" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-6 rounded-2xl border border-white/10 bg-black/15 p-4 text-sm text-white/72">
              <div className="font-semibold text-white/90">{t("workflowTemplatePage.acceptedCurrencies")}</div>
              <div className="mt-2 flex flex-wrap gap-2">
                {workflow.accepted_currencies.map((currency) => (
                  <span key={currency} className="rounded-full border border-white/12 px-3 py-1 text-xs text-white/60">
                    {currency}
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-6 grid gap-3">
              {flowSteps.map(([label, value]) => (
                <div key={label} className="rounded-2xl border border-white/10 bg-black/15 p-3">
                  <div className="text-xs uppercase tracking-[0.18em] text-white/40">{label}</div>
                  <div className="mt-1 text-sm text-white/75">{value}</div>
                </div>
              ))}
            </div>

            <div className="mt-6 text-xs leading-6 text-white/45">{t("workflowTemplatePage.runRecordNote")}</div>
          </aside>
        </section>

        <section className="mt-6">
          <WorkflowRunPanel workflow={workflow} />
        </section>
      </main>
    </div>
  );
}
