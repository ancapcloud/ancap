"use client";

import Link from "next/link";
import { Navigation } from "@/components/Navigation";
import { useLanguage } from "@/components/LanguageProvider";

type WorkflowInfo = {
  slug: string;
  title: string;
  summary: string;
  price: { amount: string; currency: string };
  receipt_items: string[];
};

type SampleInfo = {
  score: string;
  summary: string;
  sections: string[];
};

export function SampleReportView({ workflow, sample }: { workflow: WorkflowInfo; sample: SampleInfo }) {
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <Navigation />
      <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link href="/ai/workflows" className="text-sm text-emerald-300 hover:text-emerald-200">
            {t("sampleReportsPage.back")}
          </Link>
        </div>

        <section className="rounded-3xl border border-emerald-400/20 bg-emerald-400/[0.06] p-6 sm:p-8">
          <div className="text-xs uppercase tracking-[0.18em] text-emerald-200/75">{t("sampleReportsPage.kicker")}</div>
          <h1 className="mt-3 text-3xl font-semibold tracking-[-0.04em] sm:text-5xl">{workflow.title}</h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-white/72 sm:text-base">{sample.summary}</p>
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-black/15 p-4">
              <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("sampleReportsPage.sampleScore")}</div>
              <div className="mt-2 text-xl font-semibold text-emerald-300">{sample.score}</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/15 p-4">
              <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("sampleReportsPage.price")}</div>
              <div className="mt-2 text-xl font-semibold text-white/92">{workflow.price.amount} {workflow.price.currency}</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/15 p-4">
              <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("sampleReportsPage.proof")}</div>
              <div className="mt-2 text-xl font-semibold text-white/92">{t("sampleReportsPage.receiptReady")}</div>
            </div>
          </div>
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1fr_0.72fr]">
          <article className="rounded-3xl border border-white/10 bg-white/[0.03] p-6">
            <h2 className="text-2xl font-semibold tracking-[-0.03em]">{t("sampleReportsPage.includesTitle")}</h2>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {sample.sections.map((section) => (
                <div key={section} className="rounded-2xl border border-white/10 bg-black/15 p-4">
                  <div className="font-semibold text-white/90">{section}</div>
                  <p className="mt-2 text-sm leading-6 text-white/62">{t("sampleReportsPage.sectionDesc")}</p>
                </div>
              ))}
            </div>
            <pre className="mt-6 overflow-x-auto rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-white/78">{JSON.stringify({
              workflow_slug: workflow.slug,
              sample_score: sample.score,
              paid_output_sections: sample.sections,
              receipt_items: workflow.receipt_items,
              upgrade_cta: `/ai/run/${workflow.slug}`,
            }, null, 2)}</pre>
          </article>

          <aside className="rounded-3xl border border-white/10 bg-white/[0.03] p-6">
            <div className="text-sm font-semibold text-white/90">{t("sampleReportsPage.ctaTitle")}</div>
            <p className="mt-3 text-sm leading-6 text-white/65">{t("sampleReportsPage.ctaBody")}</p>
            <div className="mt-5 flex flex-col gap-3">
              <Link href={`/ai/run/${workflow.slug}`} className="rounded-full bg-emerald-400 px-5 py-3 text-center text-sm font-semibold text-slate-950 transition hover:opacity-90">
                {t("sampleReportsPage.buyWorkflow")}
              </Link>
              <Link href="/token-snapshot" className="rounded-full border border-white/15 px-5 py-3 text-center text-sm font-semibold text-white/85 transition hover:border-white/30 hover:text-white">
                {t("sampleReportsPage.freeSnapshot")}
              </Link>
            </div>
          </aside>
        </section>
      </main>
    </div>
  );
}
