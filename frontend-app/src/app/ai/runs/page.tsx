"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Navigation } from "@/components/Navigation";
import { useAuth } from "@/components/AuthProvider";
import { useLanguage } from "@/components/LanguageProvider";
import { workflowValueCopy } from "@/locales/workflowValue";
import { workflowStore } from "@/lib/api";

type WorkflowRun = {
  id: string;
  workflow_slug: string;
  title: string;
  category: string;
  status: string;
  price: { amount: string; currency: string };
  payment_currency: string;
  unlock_full_result: boolean;
  created_at: string;
  receipt?: {
    status?: string;
    proof?: {
      settlement_status?: string;
      settlement_error?: string;
      settlement_intent_id?: string;
      settlement_correlation_id?: string;
      payment_confirmation?: {
        reference?: string;
        method?: string;
      };
    };
  };
};

export default function WorkflowRunsPage() {
  const router = useRouter();
  const { lang } = useLanguage();
  const { isAuthenticated, isLoading } = useAuth();
  const [items, setItems] = useState<WorkflowRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    (async () => {
      try {
        setLoading(true);
        const data = await workflowStore.listRuns(50);
        setItems(data.items || []);
      } catch (e: any) {
        setError(e?.message || String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, [isAuthenticated]);

  if (isLoading || !isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <Navigation />
      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-[0.18em] text-white/45">Workflow Store</div>
            <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] sm:text-5xl">My workflow runs</h1>
          </div>
          <Link href="/ai/value" className="btn btn-ghost">{workflowValueCopy[lang].title}</Link>
          <Link href="/ai/workflows" className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85 transition hover:border-white/30 hover:text-white">
            Browse workflows
          </Link>
        </div>

        {error && <div className="mb-6 rounded-2xl border border-red-400/25 bg-red-500/10 p-4 text-sm text-red-200">{error}</div>}

        {loading ? (
          <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 text-white/55">Loading workflow runs…</div>
        ) : items.length === 0 ? (
          <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-6">
            <div className="text-lg font-semibold">No workflow runs yet</div>
            <div className="mt-2 text-sm text-white/60">Create your first paid workflow quote from the catalog.</div>
          </div>
        ) : (
          <div className="grid gap-4">
            {items.map((run) => {
              const settlementStatus = run.receipt?.proof?.settlement_status;
              const settlementError = run.receipt?.proof?.settlement_error;
              const settlementIntentId = run.receipt?.proof?.settlement_intent_id;
              const settlementCorrelationId = run.receipt?.proof?.settlement_correlation_id;
              const paymentReference = run.receipt?.proof?.payment_confirmation?.reference;

              return (
                <article key={run.id} className="rounded-3xl border border-white/10 bg-white/[0.03] p-6">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <div className="text-xs uppercase tracking-[0.18em] text-white/45">{run.category}</div>
                      <h2 className="mt-2 text-xl font-semibold tracking-[-0.02em]">{run.title}</h2>
                      <div className="mt-2 text-sm text-white/55">Slug: {run.workflow_slug}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-white/55">Quoted price</div>
                      <div className="mt-1 text-lg font-semibold text-emerald-300">{run.price.amount} {run.price.currency}</div>
                    </div>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-3 text-sm text-white/65">
                    <span className="rounded-full border border-white/12 px-3 py-1">Status: {run.status}</span>
                    <span className="rounded-full border border-white/12 px-3 py-1">Receipt: {run.receipt?.status || run.status}</span>
                    <span className="rounded-full border border-white/12 px-3 py-1">Payment: {run.payment_currency}</span>
                    <span className="rounded-full border border-white/12 px-3 py-1">Full result shell: {run.unlock_full_result ? "yes" : "no"}</span>
                    {settlementStatus && (
                      <span className={`rounded-full border px-3 py-1 ${settlementStatus === "executed" ? "border-emerald-400/30 text-emerald-300" : settlementStatus === "failed" ? "border-red-400/30 text-red-200" : "border-amber-400/30 text-amber-200"}`}>
                        Settlement: {settlementStatus}
                      </span>
                    )}
                    {settlementIntentId && (
                      <span className="rounded-full border border-white/12 px-3 py-1">Trail: linked</span>
                    )}
                  </div>

                  {(paymentReference || settlementCorrelationId || settlementError) && (
                    <div className="mt-4 grid gap-3 rounded-2xl border border-white/10 bg-black/15 p-4 text-sm text-white/72 sm:grid-cols-2">
                      {paymentReference && (
                        <div>
                          <div className="text-white/45">Payment ref</div>
                          <div className="mt-1 break-all text-white/88">{paymentReference}</div>
                        </div>
                      )}
                      {settlementCorrelationId && (
                        <div>
                          <div className="text-white/45">Correlation</div>
                          <div className="mt-1 break-all text-white/88">{settlementCorrelationId}</div>
                        </div>
                      )}
                      {settlementError && (
                        <div className="sm:col-span-2 rounded-2xl border border-red-400/25 bg-red-500/10 p-3 text-red-200">
                          <div className="text-red-100">Settlement error</div>
                          <div className="mt-1">{settlementError}</div>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                    <div className="text-sm text-white/45">Created: {new Date(run.created_at).toLocaleString()}</div>
                    <div className="flex flex-wrap gap-2">
                      <Link href={`/ai/runs/${run.id}#proof-bundle`} className="rounded-full border border-emerald-400/25 px-4 py-2 text-sm font-semibold text-emerald-200 transition hover:border-emerald-300/50 hover:text-emerald-100">
                        Proof bundle
                      </Link>
                      <Link href={`/ai/runs/${run.id}#settlement-trail`} className="rounded-full border border-white/15 px-4 py-2 text-sm font-semibold text-white/75 transition hover:border-white/30 hover:text-white">
                        Settlement trail
                      </Link>
                      <Link href={`/ai/runs/${run.id}`} className="rounded-full border border-white/15 px-4 py-2 text-sm font-semibold text-white/85 transition hover:border-white/30 hover:text-white">
                        Open run
                      </Link>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
