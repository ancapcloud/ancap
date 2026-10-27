"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { WorkflowResultAssessment } from "@/components/WorkflowResultAssessment";
import { Navigation } from "@/components/Navigation";
import { useAuth } from "@/components/AuthProvider";
import { useLanguage } from "@/components/LanguageProvider";
import { payments, workflowStore } from "@/lib/api";
import { useRunEvents } from "@/lib/useRunEvents";

type WorkflowRunStatus = "quoted" | "paid" | "queued" | "running" | "completed" | "failed" | "cancelled";

type WorkflowRunTimelineItem = {
  from?: string | null;
  to: string;
  changed_at: string;
};

type WorkflowRun = {
  result_hash?: string | null;
  id: string;
  workflow_slug: string;
  title: string;
  category: string;
  status: WorkflowRunStatus;
  price: { amount: string; currency: string };
  payment_currency: string;
  unlock_full_result: boolean;
  inputs: Record<string, any>;
  preview: Record<string, any>;
  result?: Record<string, any> | null;
  receipt: {
    workflow_slug: string;
    payment_currency: string;
    quoted_price: { amount: string; currency: string };
    status: string;
    receipt_items: string[];
    proof: Record<string, any> & { status_timeline?: WorkflowRunTimelineItem[] };
  };
  created_at: string;
  owner_user_id?: string | null;
};

type WorkflowRunReceiptTrail = {
  workflow_run_id: string;
  settlement_intent?: {
    id: string;
    intent_type: string;
    source_owner_type: string;
    source_owner_id: string;
    target_owner_type: string;
    target_owner_id: string;
    amount_currency: string;
    amount_value: string;
    status: string;
    correlation_id: string;
    metadata_json?: Record<string, any> | null;
    error_message?: string | null;
    executed_at?: string | null;
    created_at: string;
    updated_at: string;
  } | null;
  chain_receipts: Array<{
    id: string;
    settlement_intent_id: string;
    chain_id: string;
    tx_hash?: string | null;
    node_signature?: string | null;
    node_public_key?: string | null;
    status: string;
    correlation_id: string;
    payload_hash: string;
    receipt_json?: Record<string, any> | null;
    error_message?: string | null;
    finalized_at?: string | null;
    created_at: string;
    updated_at: string;
  }>;
};

type WorkflowRunProofBundle = {
  bundle_version: string;
  generated_at: string;
  workflow_run_id: string;
  proof_hash: string;
  receipt_items: string[];
  payment_confirmation?: Record<string, any> | null;
  execution: Record<string, any>;
  settlement_intent?: WorkflowRunReceiptTrail["settlement_intent"];
  chain_receipts: WorkflowRunReceiptTrail["chain_receipts"];
  status_timeline: WorkflowRunTimelineItem[];
  summary: {
    payment_confirmed: boolean;
    settlement_status?: string | null;
    chain_receipt_count: number;
    finalized_receipt_count: number;
    failed_receipt_count: number;
    submitted_receipt_count: number;
    execution_mode?: string | null;
    executed_at?: string | null;
    latest_chain_receipt_status?: string | null;
  };
};

type RefundRequest = {
  id: string;
  payment_intent_id: string;
  user_id: string;
  amount: { amount: string; currency: string };
  reason: string;
  status: string;
  admin_notes?: string | null;
  refund_ledger_event_id?: string | null;
  created_at: string;
  updated_at: string;
  processed_at?: string | null;
};

const NEXT_ACTIONS: Record<WorkflowRunStatus, WorkflowRunStatus[]> = {
  quoted: ["cancelled"],
  paid: ["queued", "cancelled"],
  queued: ["running", "cancelled"],
  running: ["completed", "failed", "cancelled"],
  completed: [],
  failed: [],
  cancelled: [],
};

export default function WorkflowRunDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  const { t } = useLanguage();
  const [run, setRun] = useState<WorkflowRun | null>(null);
  const [receiptTrail, setReceiptTrail] = useState<WorkflowRunReceiptTrail | null>(null);
  const [proofBundle, setProofBundle] = useState<WorkflowRunProofBundle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState<WorkflowRunStatus | null>(null);
  const [executeLoading, setExecuteLoading] = useState(false);
  const [repeatLoading, setRepeatLoading] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [reserveCreditsLoading, setReserveCreditsLoading] = useState(false);
  const [retrySettlementLoading, setRetrySettlementLoading] = useState(false);
  const [proofBundleActionMessage, setProofBundleActionMessage] = useState("");
  const [paymentReference, setPaymentReference] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("manual");
  const [paymentNote, setPaymentNote] = useState("");
  const [refundReason, setRefundReason] = useState("");
  const [refundLoading, setRefundLoading] = useState(false);
  const [refundRequest, setRefundRequest] = useState<RefundRequest | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  const loadRun = useCallback(async () => {
    if (!params?.id) return;
    try {
      setLoading(true);
      setError("");
      const [data, trail, bundle] = await Promise.all([
        workflowStore.getRun(params.id),
        workflowStore.getReceiptTrail(params.id),
        workflowStore.getProofBundle(params.id),
      ]);
      setRun(data);
      setReceiptTrail(trail);
      setProofBundle(bundle);

      const paymentIntentId = typeof data?.receipt?.proof?.payment_intent_id === "string" ? data.receipt.proof.payment_intent_id : "";
      if (paymentIntentId) {
        try {
          const refundResponse = await payments.listMyRefundRequests(undefined, paymentIntentId) as { items?: RefundRequest[] };
          const items = Array.isArray(refundResponse.items) ? refundResponse.items : [];
          setRefundRequest(items[0] || null);
        } catch {
          setRefundRequest(null);
        }
      } else {
        setRefundRequest(null);
      }
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  }, [params?.id]);

  useEffect(() => {
    if (!isAuthenticated || !params?.id) return;
    void loadRun();
  }, [isAuthenticated, params?.id, loadRun]);

  useEffect(() => {
    setRefundReason("");
  }, [run?.id]);

  async function refreshProofArtifacts(runId: string) {
    const [trail, bundle] = await Promise.all([
      workflowStore.getReceiptTrail(runId),
      workflowStore.getProofBundle(runId),
    ]);
    setReceiptTrail(trail);
    setProofBundle(bundle);
  }

  async function updateStatus(status: WorkflowRunStatus) {
    if (!run) return;
    try {
      setActionLoading(status);
      setError("");
      const response = await workflowStore.updateRunStatus(run.id, status);
      const nextRun = response.item || response;
      setRun(nextRun);
      await refreshProofArtifacts(nextRun.id);
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setActionLoading(null);
    }
  }

  async function executeRun() {
    if (!run) return;
    try {
      setExecuteLoading(true);
      setError("");
      const response = await workflowStore.executeRun(run.id);
      const nextRun = response.item || response;
      setRun(nextRun);
      await refreshProofArtifacts(nextRun.id);
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setExecuteLoading(false);
    }
  }

  async function confirmPayment() {
    if (!run) return;
    if (!paymentReference.trim()) {
      setError(t("workflowRunDetail.paymentReferenceRequired"));
      return;
    }
    try {
      setPaymentLoading(true);
      setError("");
      const response = await workflowStore.confirmRunPayment(run.id, {
        payment_reference: paymentReference.trim(),
        payment_method: paymentMethod.trim() || "manual",
        payment_amount: { amount: run.price.amount, currency: run.payment_currency },
        note: paymentNote.trim() || undefined,
      });
      const nextRun = response.item || response;
      setRun(nextRun);
      await refreshProofArtifacts(nextRun.id);
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setPaymentLoading(false);
    }
  }

  async function reserveCredits() {
    if (!run) return;
    try {
      setReserveCreditsLoading(true);
      setError("");
      const response = await workflowStore.createPaymentIntent(run.id, {
        payment_method: "credits",
        note: "Reserved from workflow credits.",
      });
      const nextRun = response.run || response.item?.run || response;
      setRun(nextRun);
      await refreshProofArtifacts(nextRun.id);
    } catch (e: any) {
      setError(e?.message || String(e));
      await loadRun();
    } finally {
      setReserveCreditsLoading(false);
    }
  }

  async function retrySettlement() {
    if (!run) return;
    try {
      setRetrySettlementLoading(true);
      setError("");
      const response = await workflowStore.retrySettlement(run.id);
      const nextRun = response.item || response;
      setRun(nextRun);
      await refreshProofArtifacts(nextRun.id);
    } catch (e: any) {
      setError(e?.message || String(e));
      await loadRun();
    } finally {
      setRetrySettlementLoading(false);
    }
  }

  async function repeatRun() {
    if (!run) return;
    try {
      setRepeatLoading(true);
      setError("");
      const created = await workflowStore.repeatRun(run.id);
      router.push(`/ai/runs/${created.id}`);
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setRepeatLoading(false);
    }
  }

  async function submitRefundRequest() {
    if (!run) return;
    const paymentIntentId = typeof run.receipt?.proof?.payment_intent_id === "string" ? run.receipt.proof.payment_intent_id : "";
    if (!paymentIntentId) {
      setError(t("workflowRunDetail.refundUnavailable"));
      return;
    }
    if (refundReason.trim().length < 3) {
      setError(t("workflowRunDetail.refundReasonMin"));
      return;
    }
    try {
      setRefundLoading(true);
      setError("");
      const created = await payments.createRefundRequest({
        payment_intent_id: paymentIntentId,
        reason: refundReason.trim(),
      }) as RefundRequest;
      setRefundRequest(created);
      setRefundReason("");
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setRefundLoading(false);
    }
  }

  function editAndRepeatRun() {
    if (!run) return;
    const params = new URLSearchParams({
      fromRun: run.id,
      prefill: "1",
      inputs: JSON.stringify(run.inputs || {}),
      paymentCurrency: run.payment_currency,
      unlockFullResult: run.unlock_full_result ? "1" : "0",
    });
    router.push(`/ai/run/${run.workflow_slug}?${params.toString()}`);
  }

  const nextActions = useMemo(() => (run ? NEXT_ACTIONS[run.status] || [] : []), [run]);
  const canExecute = useMemo(() => (run ? ["paid", "queued", "running"].includes(run.status) : false), [run]);
  const canConfirmPayment = useMemo(() => run?.status === "quoted", [run]);
  const timeline = useMemo(() => {
    const raw = run?.receipt?.proof?.status_timeline;
    return Array.isArray(raw) ? raw : [];
  }, [run]);
  const paymentConfirmation = run?.receipt?.proof?.payment_confirmation;
  const settlementError = run?.receipt?.proof?.settlement_error;
  const settlementStatus = String(run?.receipt?.proof?.settlement_status || "");
  const paymentIntentId = typeof run?.receipt?.proof?.payment_intent_id === "string" ? run.receipt.proof.payment_intent_id : "";
  const paymentIntentStatus = typeof run?.receipt?.proof?.payment_intent_status === "string" ? String(run.receipt.proof.payment_intent_status) : "";
  const canRetrySettlement = run?.status === "quoted" && settlementStatus === "failed";
  const canRequestRefund = Boolean(run && run.status === "completed" && paymentIntentId && paymentIntentStatus === "captured" && !refundRequest);
  const settlementAttempts = useMemo(() => {
    const receipts = Array.isArray(receiptTrail?.chain_receipts) ? [...receiptTrail.chain_receipts] : [];
    return receipts
      .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
      .map((item, index) => ({
        ...item,
        attemptNumber: index + 1,
        driver: String(item.receipt_json?.driver || item.chain_id),
        replayed: Boolean(item.receipt_json?.replayed),
        ledgerEventReused: Boolean(item.receipt_json?.ledger_event_reused),
      }));
  }, [receiptTrail]);
  const latestSettlementAttempt = settlementAttempts.length > 0 ? settlementAttempts[settlementAttempts.length - 1] : null;
  const settlementAttemptStats = useMemo(() => ({
    total: settlementAttempts.length,
    finalized: settlementAttempts.filter((item) => item.status === "finalized").length,
    failed: settlementAttempts.filter((item) => item.status === "failed").length,
    submitted: settlementAttempts.filter((item) => item.status === "submitted").length,
  }), [settlementAttempts]);

  const proofBundleText = useMemo(() => (proofBundle ? JSON.stringify(proofBundle, null, 2) : ""), [proofBundle]);
  const invoiceReference = useMemo(() => (run ? `ANCAP-${run.id.slice(0, 8)}-${run.workflow_slug}` : ""), [run]);
  const paymentTarget = "ancap-workflow-treasury";
  const shouldPollRun = Boolean(run && ["quoted", "paid", "queued", "running"].includes(run.status));
  const { lastEvent: runEvent, connectionState: runEventState } = useRunEvents(run?.id, shouldPollRun);

  useEffect(() => {
    if (!runEvent || !run || runEvent.workflow_run_id !== run.id) return;
    if (runEvent.status !== run.status || runEvent.receipt_ready) {
      void loadRun();
    }
  }, [loadRun, run, runEvent]);

  useEffect(() => {
    if (!shouldPollRun) return;
    const interval = window.setInterval(() => {
      void loadRun();
    }, 10000);
    return () => window.clearInterval(interval);
  }, [shouldPollRun, loadRun]);

  async function copyProofBundle() {
    if (!proofBundleText) return;
    try {
      await navigator.clipboard.writeText(proofBundleText);
      setProofBundleActionMessage(t("workflowRunDetail.proofBundleCopied"));
    } catch {
      setProofBundleActionMessage(t("workflowRunDetail.proofBundleCopyFailed"));
    }
  }

  async function copyProofHash() {
    if (!proofBundle?.proof_hash) return;
    try {
      await navigator.clipboard.writeText(proofBundle.proof_hash);
      setProofBundleActionMessage(t("workflowRunDetail.proofHashCopied"));
    } catch {
      setProofBundleActionMessage(t("workflowRunDetail.proofHashCopyFailed"));
    }
  }

  function downloadProofBundle() {
    if (!proofBundleText || !proofBundle) return;
    const blob = new Blob([proofBundleText], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `workflow-run-proof-${proofBundle.workflow_run_id}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setProofBundleActionMessage(t("workflowRunDetail.proofBundleDownloaded"));
  }

  if (isLoading || !isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <Navigation />
      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.kicker")}</div>
            <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] sm:text-5xl">{t("workflowRunDetail.title")}</h1>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link href="/ai/runs" className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85 transition hover:border-white/30 hover:text-white">
              {t("workflowRunDetail.backToRuns")}
            </Link>
            <Link href="/billing" className="rounded-full border border-emerald-400/25 px-5 py-2.5 text-sm font-semibold text-emerald-200 transition hover:border-emerald-300/50 hover:text-emerald-100">
              {t("workflowRunDetail.billingOverview")}
            </Link>
            <Link href="/wallet/credits" className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85 transition hover:border-white/30 hover:text-white">
              {t("workflowRunDetail.credits")}
            </Link>
            {run && (
              <Link href={`/proof-center?run=${run.id}`} className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85 transition hover:border-white/30 hover:text-white">
                {t("workflowRunDetail.proofCenter")}
              </Link>
            )}
            {run && (
              <Link href={`/ai/run/${run.workflow_slug}`} className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85 transition hover:border-white/30 hover:text-white">
                {t("workflowRunDetail.openTemplate")}
              </Link>
            )}
          </div>
        </div>

        {error && <div className="mb-6 rounded-2xl border border-red-400/25 bg-red-500/10 p-4 text-sm text-red-200">{error}</div>}

        {loading ? (
          <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 text-white/55">{t("workflowRunDetail.loading")}</div>
        ) : !run ? (
          <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 text-white/55">{t("workflowRunDetail.notFound")}</div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
            <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-6">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="text-xs uppercase tracking-[0.18em] text-white/45">{run.category}</div>
                  <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em]">{run.title}</h2>
                  <div className="mt-2 text-sm text-white/55">{t("workflowRunDetail.runId")} {run.id}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-white/55">{t("workflowRunDetail.status")}</div>
                  <div className="mt-1 text-lg font-semibold text-emerald-300">{run.status}</div>
                  <div className="mt-1 text-xs text-white/45">
                    {t("workflowRunDetail.live")} {shouldPollRun ? runEventState : t("workflowRunDetail.terminal")}
                  </div>
                </div>
              </div>

              <div className="mt-6 rounded-2xl border border-white/10 bg-black/15 p-4">
                <div className="text-sm font-semibold text-white/90">{t("workflowRunDetail.lifecycleActions")}</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={repeatRun}
                    disabled={repeatLoading || executeLoading || actionLoading !== null || paymentLoading}
                    className="rounded-full border border-emerald-400/40 px-4 py-2 text-sm font-semibold text-emerald-300 transition hover:border-emerald-300 hover:text-emerald-200 disabled:opacity-50"
                  >
                    {repeatLoading ? t("workflowRunDetail.repeating") : t("workflowRunDetail.repeatRun")}
                  </button>
                  <button
                    type="button"
                    onClick={editAndRepeatRun}
                    disabled={repeatLoading || executeLoading || actionLoading !== null || paymentLoading}
                    className="rounded-full border border-white/15 px-4 py-2 text-sm font-semibold text-white/85 transition hover:border-white/30 hover:text-white disabled:opacity-50"
                  >
                    {t("workflowRunDetail.editRepeat")}
                  </button>
                  {canExecute && (
                    <button
                      type="button"
                      onClick={executeRun}
                      disabled={executeLoading || repeatLoading || actionLoading !== null || paymentLoading || retrySettlementLoading}
                      className="rounded-full bg-emerald-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:opacity-90 disabled:opacity-50"
                    >
                      {executeLoading ? t("workflowRunDetail.executing") : t("workflowRunDetail.executeWorkflow")}
                    </button>
                  )}
                  {canRetrySettlement && (
                    <button
                      type="button"
                      onClick={retrySettlement}
                      disabled={retrySettlementLoading || executeLoading || repeatLoading || actionLoading !== null || paymentLoading}
                      className="rounded-full bg-amber-300 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:opacity-90 disabled:opacity-50"
                    >
                      {retrySettlementLoading ? t("workflowRunDetail.retryingSettlement") : t("workflowRunDetail.retrySettlement")}
                    </button>
                  )}
                  {nextActions.map((status) => (
                    <button
                      key={status}
                      type="button"
                      onClick={() => updateStatus(status)}
                      disabled={actionLoading !== null || executeLoading || repeatLoading || paymentLoading}
                      className="rounded-full border border-white/15 px-4 py-2 text-sm font-semibold text-white/85 transition hover:border-white/30 hover:text-white disabled:opacity-50"
                    >
                      {actionLoading === status ? t("workflowRunDetail.updatingTo").replace("{status}", status) : t("workflowRunDetail.markStatus").replace("{status}", status)}
                    </button>
                  ))}
                  {!canExecute && !canConfirmPayment && nextActions.length === 0 && (
                    <div className="text-sm text-white/55">{t("workflowRunDetail.terminalState")}</div>
                  )}
                </div>
              </div>

              {canConfirmPayment && (
                <div className="mt-6 rounded-2xl border border-white/10 bg-black/15 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="text-sm font-semibold text-white/90">{t("workflowRunDetail.confirmPayment")}</div>
                    <div className="flex flex-wrap gap-2 text-xs">
                      <Link href="/billing" className="rounded-full border border-emerald-400/25 px-3 py-1.5 font-semibold text-emerald-200 transition hover:border-emerald-300/50 hover:text-emerald-100">
                        {t("workflowRunDetail.openBilling")}
                      </Link>
                      <Link href="/wallet/credits" className="rounded-full border border-white/15 px-3 py-1.5 font-semibold text-white/80 transition hover:border-white/30 hover:text-white">
                        {t("workflowRunDetail.checkCredits")}
                      </Link>
                    </div>
                  </div>
                  <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <div className="text-sm font-semibold text-white/90">{t("workflowRunDetail.checkoutInvoice")}</div>
                        <div className="mt-1 text-sm text-white/58">{t("workflowRunDetail.checkoutLead")}</div>
                      </div>
                      <button
                        type="button"
                        onClick={() => void loadRun()}
                        className="rounded-full border border-white/15 px-3 py-1.5 text-xs font-semibold text-white/80 transition hover:border-white/30 hover:text-white"
                      >
                        {t("workflowRunDetail.pollStatus")}
                      </button>
                    </div>
                    <div className="mt-4 grid gap-3 sm:grid-cols-2">
                      <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
                        <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.amountDue")}</div>
                        <div className="mt-2 text-lg font-semibold text-emerald-300">{run.price.amount} {run.payment_currency}</div>
                      </div>
                      <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
                        <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.paymentTarget")}</div>
                        <div className="mt-2 break-all text-sm font-semibold text-white/88">{paymentTarget}</div>
                      </div>
                      <div className="rounded-2xl border border-white/10 bg-black/20 p-3 sm:col-span-2">
                        <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.reference")}</div>
                        <div className="mt-2 break-all text-sm font-semibold text-white/88">{invoiceReference}</div>
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 rounded-2xl border border-emerald-400/20 bg-emerald-400/8 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-emerald-100">{t("workflowRunDetail.payWithCredits")}</div>
                        <div className="mt-1 text-sm text-emerald-100/70">
                          {t("workflowRunDetail.reserveCreditsLead").replace("{amount}", run.price.amount).replace("{currency}", run.payment_currency)}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={reserveCredits}
                        disabled={reserveCreditsLoading || paymentLoading || retrySettlementLoading || executeLoading || repeatLoading || actionLoading !== null}
                        className="rounded-full bg-emerald-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:opacity-90 disabled:opacity-50"
                      >
                        {reserveCreditsLoading ? t("workflowRunDetail.reserving") : t("workflowRunDetail.reserveCredits")}
                      </button>
                    </div>
                  </div>
                  <div className="mt-4 grid gap-4">
                    <div>
                      <div className="mb-2 text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.paymentReference")}</div>
                      <input
                        value={paymentReference}
                        onChange={(e) => setPaymentReference(e.target.value)}
                        placeholder={invoiceReference || t("workflowRunDetail.paymentRefPlaceholder")}
                        className="w-full rounded-2xl border border-white/10 bg-[var(--bg)] px-4 py-3 text-sm text-white outline-none"
                      />
                    </div>
                    <div>
                      <div className="mb-2 text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.paymentMethod")}</div>
                      <input
                        value={paymentMethod}
                        onChange={(e) => setPaymentMethod(e.target.value)}
                        placeholder="manual"
                        className="w-full rounded-2xl border border-white/10 bg-[var(--bg)] px-4 py-3 text-sm text-white outline-none"
                      />
                    </div>
                    <div>
                      <div className="mb-2 text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.note")}</div>
                      <textarea
                        value={paymentNote}
                        onChange={(e) => setPaymentNote(e.target.value)}
                        rows={3}
                        className="w-full rounded-2xl border border-white/10 bg-[var(--bg)] p-3 text-sm text-white outline-none"
                      />
                    </div>
                    <div>
                      <button
                        type="button"
                        onClick={confirmPayment}
                        disabled={paymentLoading || retrySettlementLoading || executeLoading || repeatLoading || actionLoading !== null}
                        className="rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-950 transition hover:opacity-90 disabled:opacity-50"
                      >
                        {paymentLoading ? t("workflowRunDetail.confirming") : t("workflowRunDetail.confirmPaymentBtn")}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-black/15 p-4">
                  <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.quotedPrice")}</div>
                  <div className="mt-2 text-lg font-semibold text-white/92">{run.price.amount} {run.price.currency}</div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/15 p-4">
                  <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.paymentCurrency")}</div>
                  <div className="mt-2 text-lg font-semibold text-white/92">{run.payment_currency}</div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/15 p-4">
                  <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.fullResultShell")}</div>
                  <div className="mt-2 text-lg font-semibold text-white/92">{run.unlock_full_result ? t("workflowRunDetail.enabled") : t("workflowRunDetail.disabled")}</div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/15 p-4">
                  <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.created")}</div>
                  <div className="mt-2 text-sm font-medium text-white/75">{new Date(run.created_at).toLocaleString()}</div>
                </div>
              </div>

              <div className="mt-6">
                <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.inputs")}</div>
                <pre className="mt-3 overflow-x-auto rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-white/78">{JSON.stringify(run.inputs, null, 2)}</pre>
              </div>

              <div className="mt-6">
                <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.preview")}</div>
                <pre className="mt-3 overflow-x-auto rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-white/78">{JSON.stringify(run.preview, null, 2)}</pre>
              </div>

              <div className="mt-6">
                <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.resultShell")}</div>
                <pre className="mt-3 overflow-x-auto rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-white/78">{JSON.stringify(run.result, null, 2)}</pre>
                {run.status === "completed" && run.result_hash && <div className="mt-6"><WorkflowResultAssessment runId={run.id} resultHash={run.result_hash} /></div>}
              </div>
            </section>

            <aside className="rounded-3xl border border-white/10 bg-white/[0.03] p-6">
              <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.receipt")}</div>
              <div className="mt-4 rounded-2xl border border-white/10 bg-black/15 p-4">
                <div className="text-sm text-white/60">{t("workflowRunDetail.workflow")}</div>
                <div className="mt-1 font-medium text-white/88">{run.receipt.workflow_slug}</div>
                <div className="mt-4 text-sm text-white/60">{t("workflowRunDetail.quotedPrice")}</div>
                <div className="mt-1 font-medium text-emerald-300">{run.receipt.quoted_price.amount} {run.receipt.quoted_price.currency}</div>
                <div className="mt-4 text-sm text-white/60">{t("workflowRunDetail.receiptStatus")}</div>
                <div className="mt-1 font-medium text-white/88">{run.receipt.status}</div>
              </div>

              {proofBundle && (
                <div id="proof-bundle" className="mt-6 rounded-2xl border border-emerald-400/20 bg-emerald-400/5 p-4 scroll-mt-24">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-emerald-200">{t("workflowRunDetail.proofBundle")}</div>
                      <div className="mt-1 text-xs text-emerald-100/70">{proofBundle.bundle_version}</div>
                    </div>
                    <div className="text-right text-xs text-emerald-100/70">
                      <div>{t("workflowRunDetail.generated")} {new Date(proofBundle.generated_at).toLocaleString()}</div>
                      <div className="mt-1">{t("workflowRunDetail.hash")} {proofBundle.proof_hash.slice(0, 16)}…</div>
                    </div>
                  </div>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl border border-emerald-400/15 bg-black/20 p-3">
                      <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.paymentConfirmed")}</div>
                      <div className="mt-2 text-lg font-semibold text-white/92">{proofBundle.summary.payment_confirmed ? t("workflowRunDetail.yes") : t("workflowRunDetail.no")}</div>
                    </div>
                    <div className="rounded-2xl border border-emerald-400/15 bg-black/20 p-3">
                      <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.settlement")}</div>
                      <div className="mt-2 text-lg font-semibold text-white/92">{proofBundle.summary.settlement_status || t("workflowRunDetail.dash")}</div>
                    </div>
                    <div className="rounded-2xl border border-emerald-400/15 bg-black/20 p-3">
                      <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.chainReceipts")}</div>
                      <div className="mt-2 text-lg font-semibold text-white/92">{proofBundle.summary.chain_receipt_count}</div>
                    </div>
                    <div className="rounded-2xl border border-emerald-400/15 bg-black/20 p-3">
                      <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.executionMode")}</div>
                      <div className="mt-2 text-lg font-semibold text-white/92">{proofBundle.summary.execution_mode || t("workflowRunDetail.notExecuted")}</div>
                    </div>
                    <div className="rounded-2xl border border-emerald-400/15 bg-black/20 p-3">
                      <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.finalizedReceipts")}</div>
                      <div className="mt-2 text-lg font-semibold text-emerald-300">{proofBundle.summary.finalized_receipt_count}</div>
                    </div>
                    <div className="rounded-2xl border border-emerald-400/15 bg-black/20 p-3">
                      <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.failedReceipts")}</div>
                      <div className="mt-2 text-lg font-semibold text-red-200">{proofBundle.summary.failed_receipt_count}</div>
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={copyProofBundle}
                      className="rounded-full border border-emerald-400/30 px-4 py-2 text-sm font-semibold text-emerald-200 transition hover:border-emerald-300 hover:text-emerald-100"
                    >
                      {t("workflowRunDetail.copyBundleJson")}
                    </button>
                    <button
                      type="button"
                      onClick={copyProofHash}
                      className="rounded-full border border-white/15 px-4 py-2 text-sm font-semibold text-white/85 transition hover:border-white/30 hover:text-white"
                    >
                      {t("workflowRunDetail.copyProofHash")}
                    </button>
                    <button
                      type="button"
                      onClick={downloadProofBundle}
                      className="rounded-full bg-emerald-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:opacity-90"
                    >
                      {t("workflowRunDetail.downloadProofBundle")}
                    </button>
                  </div>
                  {proofBundleActionMessage && (
                    <div className="mt-3 text-sm text-emerald-100/80">{proofBundleActionMessage}</div>
                  )}
                </div>
              )}

              <div className="mt-6 rounded-2xl border border-white/10 bg-black/15 p-4">
                <div className="text-sm font-semibold text-white/90">{t("workflowRunDetail.paymentEvidence")}</div>
                {paymentConfirmation ? (
                  <div className="mt-3 space-y-3 text-sm text-white/78">
                    <div>
                      <div className="text-white/50">{t("workflowRunDetail.refLabel")}</div>
                      <div>{String(paymentConfirmation.reference || t("workflowRunDetail.dash"))}</div>
                    </div>
                    <div>
                      <div className="text-white/50">{t("workflowRunDetail.methodLabel")}</div>
                      <div>{String(paymentConfirmation.method || t("workflowRunDetail.dash"))}</div>
                    </div>
                    <div>
                      <div className="text-white/50">{t("workflowRunDetail.confirmedAt")}</div>
                      <div>{paymentConfirmation.confirmed_at ? new Date(paymentConfirmation.confirmed_at).toLocaleString() : t("workflowRunDetail.dash")}</div>
                    </div>
                    <div>
                      <div className="text-white/50">{t("workflowRunDetail.amountLabel")}</div>
                      <div>{paymentConfirmation.payment_amount?.amount || t("workflowRunDetail.dash")} {paymentConfirmation.payment_amount?.currency || ""}</div>
                    </div>
                    {paymentConfirmation.note && (
                      <div>
                        <div className="text-white/50">{t("workflowRunDetail.noteLabel")}</div>
                        <div>{String(paymentConfirmation.note)}</div>
                      </div>
                    )}
                    {settlementError && (
                      <div className="rounded-2xl border border-red-400/25 bg-red-500/10 p-3 text-red-200">
                        <div className="text-red-100">{t("workflowRunDetail.settlementError")}</div>
                        <div className="mt-1 text-sm">{String(settlementError)}</div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="mt-3 text-sm text-white/55">{t("workflowRunDetail.noPaymentConfirmation")}</div>
                )}
              </div>

              <div className="mt-6 rounded-2xl border border-white/10 bg-black/15 p-4">
                <div className="text-sm font-semibold text-white/90">{t("workflowRunDetail.refundDispute")}</div>
                <div className="mt-2 text-sm text-white/60">
                  {t("workflowRunDetail.refundLead")}
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
                    <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.paymentIntent")}</div>
                    <div className="mt-2 break-all text-sm font-medium text-white/88">{paymentIntentId || t("workflowRunDetail.dash")}</div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
                    <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.refundEligibility")}</div>
                    <div className="mt-2 text-sm font-medium text-white/88">
                      {paymentIntentStatus === "refunded" ? t("workflowRunDetail.alreadyRefunded") : canRequestRefund ? t("workflowRunDetail.capturedCanRequest") : paymentIntentStatus || t("workflowRunDetail.notAvailable")}
                    </div>
                  </div>
                </div>
                {refundRequest ? (
                  <div className="mt-4 rounded-2xl border border-amber-300/25 bg-amber-300/10 p-4 text-sm text-amber-100">
                    <div className="font-semibold text-amber-50">{t("workflowRunDetail.refundSubmitted")}</div>
                    <div className="mt-2">{t("workflowRunDetail.statusLabel")} {refundRequest.status}</div>
                    <div className="mt-1">{t("workflowRunDetail.createdLabel")} {new Date(refundRequest.created_at).toLocaleString()}</div>
                    <div className="mt-1">{t("workflowRunDetail.reasonLabel")} {refundRequest.reason}</div>
                    {refundRequest.admin_notes && <div className="mt-1">{t("workflowRunDetail.adminNotes")} {refundRequest.admin_notes}</div>}
                  </div>
                ) : paymentIntentStatus === "refunded" ? (
                  <div className="mt-4 rounded-2xl border border-emerald-400/25 bg-emerald-400/10 p-4 text-sm text-emerald-100">
                    {t("workflowRunDetail.paymentIntentRefunded")}
                  </div>
                ) : canRequestRefund ? (
                  <div className="mt-4 grid gap-3">
                    <div>
                      <div className="mb-2 text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.whyRefund")}</div>
                      <textarea
                        value={refundReason}
                        onChange={(e) => setRefundReason(e.target.value)}
                        rows={4}
                        placeholder={t("workflowRunDetail.refundPlaceholder")}
                        className="w-full rounded-2xl border border-white/10 bg-[var(--bg)] p-3 text-sm text-white outline-none"
                      />
                    </div>
                    <div className="flex flex-wrap gap-3">
                      <button
                        type="button"
                        onClick={submitRefundRequest}
                        disabled={refundLoading || !refundReason.trim()}
                        className="rounded-full border border-amber-300/40 px-4 py-2 text-sm font-semibold text-amber-100 transition hover:border-amber-200 hover:text-amber-50 disabled:opacity-50"
                      >
                        {refundLoading ? t("workflowRunDetail.submitting") : t("workflowRunDetail.submitRefund")}
                      </button>
                      <div className="text-sm text-white/50">
                        {t("workflowRunDetail.adminReviewRequired")}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="mt-4 text-sm text-white/55">
                    {t("workflowRunDetail.refundAvailableAfter")}
                  </div>
                )}
              </div>

              <div className="mt-6 rounded-2xl border border-white/10 bg-black/15 p-4">
                <div className="text-sm font-semibold text-white/90">{t("workflowRunDetail.receiptItems")}</div>
                {run.receipt.receipt_items.length === 0 ? (
                  <div className="mt-3 text-sm text-white/55">{t("workflowRunDetail.noReceiptItems")}</div>
                ) : (
                  <ul className="mt-3 space-y-2 text-sm text-white/75">
                    {run.receipt.receipt_items.map((item) => (
                      <li key={item} className="flex items-center gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-300" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div id="settlement-trail" className="mt-6 rounded-2xl border border-white/10 bg-black/15 p-4 scroll-mt-24">
                <div className="text-sm font-semibold text-white/90">{t("workflowRunDetail.settlementTrail")}</div>
                {!receiptTrail?.settlement_intent ? (
                  <div className="mt-3 text-sm text-white/55">{t("workflowRunDetail.noSettlementTrail")}</div>
                ) : (
                  <div className="mt-3 space-y-4 text-sm text-white/78">
                    <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
                      <div className="text-white/50">{t("workflowRunDetail.settlementIntent")}</div>
                      <div className="mt-1 font-medium text-white/88">{receiptTrail.settlement_intent.intent_type}</div>
                      <div className="mt-2 text-white/60">{t("workflowRunDetail.statusLabel")} {receiptTrail.settlement_intent.status}</div>
                      <div className="text-white/60">{t("workflowRunDetail.amount")} {receiptTrail.settlement_intent.amount_value} {receiptTrail.settlement_intent.amount_currency}</div>
                      <div className="text-white/60">{t("workflowRunDetail.correlation")} {receiptTrail.settlement_intent.correlation_id}</div>
                      <div className="text-white/45">{t("workflowRunDetail.executed")} {receiptTrail.settlement_intent.executed_at ? new Date(receiptTrail.settlement_intent.executed_at).toLocaleString() : t("workflowRunDetail.dash")}</div>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                      <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
                        <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.attempts")}</div>
                        <div className="mt-2 text-lg font-semibold text-white/92">{settlementAttemptStats.total}</div>
                      </div>
                      <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
                        <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.finalized")}</div>
                        <div className="mt-2 text-lg font-semibold text-emerald-300">{settlementAttemptStats.finalized}</div>
                      </div>
                      <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
                        <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.failed")}</div>
                        <div className="mt-2 text-lg font-semibold text-red-200">{settlementAttemptStats.failed}</div>
                      </div>
                      <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
                        <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.latestOutcome")}</div>
                        <div className={`mt-2 text-lg font-semibold ${latestSettlementAttempt?.status === "finalized" ? "text-emerald-300" : latestSettlementAttempt?.status === "failed" ? "text-red-200" : "text-amber-200"}`}>
                          {latestSettlementAttempt?.status || t("workflowRunDetail.dash")}
                        </div>
                      </div>
                    </div>

                    <div>
                      <div className="text-white/50">{t("workflowRunDetail.settlementAttempts")}</div>
                      {settlementAttempts.length === 0 ? (
                        <div className="mt-2 text-white/55">{t("workflowRunDetail.noChainReceipts")}</div>
                      ) : (
                        <div className="mt-2 space-y-3">
                          {[...settlementAttempts].reverse().map((item) => (
                            <div key={item.id} className="rounded-2xl border border-white/10 bg-black/20 p-3">
                              <div className="flex flex-wrap items-start justify-between gap-3">
                                <div>
                                  <div className="font-medium text-white/88">{t("workflowRunDetail.attemptLine").replace("{n}", String(item.attemptNumber)).replace("{chain}", item.chain_id).replace("{status}", item.status)}</div>
                                  <div className="mt-1 text-white/45">{t("workflowRunDetail.started")} {new Date(item.created_at).toLocaleString()}</div>
                                </div>
                                <div className="text-right text-xs text-white/45">{t("workflowRunDetail.driver")} {item.driver}</div>
                              </div>
                              <div className="mt-3 grid gap-2 text-white/60 sm:grid-cols-2">
                                <div>{t("workflowRunDetail.tx")} {item.tx_hash || t("workflowRunDetail.dash")}</div>
                                <div>{t("workflowRunDetail.correlation")} {item.correlation_id}</div>
                                <div>{t("workflowRunDetail.payload")} {item.payload_hash.slice(0, 16)}…</div>
                                <div>{t("workflowRunDetail.finalizedAt")} {item.finalized_at ? new Date(item.finalized_at).toLocaleString() : t("workflowRunDetail.dash")}</div>
                              </div>
                              {(item.replayed || item.ledgerEventReused) && (
                                <div className="mt-3 flex flex-wrap gap-2 text-xs">
                                  {item.replayed && <span className="rounded-full border border-amber-400/30 px-2 py-1 text-amber-200">{t("workflowRunDetail.replayedIntent")}</span>}
                                  {item.ledgerEventReused && <span className="rounded-full border border-emerald-400/30 px-2 py-1 text-emerald-200">{t("workflowRunDetail.ledgerReused")}</span>}
                                </div>
                              )}
                              {item.error_message && (
                                <div className="mt-3 rounded-2xl border border-red-400/25 bg-red-500/10 p-3 text-red-200">
                                  <div className="text-red-100">{t("workflowRunDetail.attemptError")}</div>
                                  <div className="mt-1 text-sm">{item.error_message}</div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-6 rounded-2xl border border-white/10 bg-black/15 p-4">
                <div className="text-sm text-white/60">{t("workflowRunDetail.executionMode")}</div>
                <div className="mt-1 font-medium text-white/88">{String(run.receipt.proof?.execution_mode || t("workflowRunDetail.notExecuted"))}</div>
                <div className="mt-4 text-sm text-white/60">{t("workflowRunDetail.executedAt")}</div>
                <div className="mt-1 font-medium text-white/88">{run.receipt.proof?.executed_at ? new Date(run.receipt.proof.executed_at).toLocaleString() : t("workflowRunDetail.dash")}</div>
              </div>

              <div className="mt-6 rounded-2xl border border-white/10 bg-black/15 p-4">
                <div className="text-sm font-semibold text-white/90">{t("workflowRunDetail.statusTimeline")}</div>
                {timeline.length === 0 ? (
                  <div className="mt-3 text-sm text-white/55">{t("workflowRunDetail.noStatusHistory")}</div>
                ) : (
                  <div className="mt-3 space-y-3">
                    {timeline.map((item, index) => (
                      <div key={`${item.changed_at}-${index}`} className="rounded-2xl border border-white/10 bg-black/20 p-3 text-sm">
                        <div className="text-white/85">{item.from ? `${item.from} → ${item.to}` : `→ ${item.to}`}</div>
                        <div className="mt-1 text-white/45">{new Date(item.changed_at).toLocaleString()}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="mt-6">
                <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.proofMetadata")}</div>
                <pre className="mt-3 overflow-x-auto rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-white/78">{JSON.stringify(run.receipt.proof, null, 2)}</pre>
              </div>

              {proofBundle && (
                <div className="mt-6">
                  <div className="text-xs uppercase tracking-[0.18em] text-white/45">{t("workflowRunDetail.proofBundleJson")}</div>
                  <pre className="mt-3 overflow-x-auto rounded-2xl border border-emerald-400/20 bg-black/20 p-4 text-sm text-white/78">{proofBundleText}</pre>
                </div>
              )}
            </aside>
          </div>
        )}
      </main>
    </div>
  );
}
