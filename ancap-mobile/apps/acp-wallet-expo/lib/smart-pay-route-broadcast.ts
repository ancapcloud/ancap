/**
 * Client-side routePlan orchestration (SQ-7).
 *
 * Execute returns actionable signing steps; this module signs ACP legs locally
 * and optionally submits them via the caller-provided broadcast function.
 * Bridge/swap legs are reported as skipped until their chain clients are wired.
 */
import type { SmartPayRouteExecutionStep, SmartPayTxRef } from "@ancap/acp-api-client";
import { signAndPrepareTransfer } from "@ancap/acp-wallet-sdk";

export type RouteBroadcastStepResult = {
  stepIndex: number;
  action: SmartPayRouteExecutionStep["action"];
  network: string;
  status: "broadcast" | "signed_local" | "skipped" | "failed" | "submission_unknown";
  txid?: string;
  reason?: string;
};

export type RouteBroadcastInput = {
  routePlan: SmartPayRouteExecutionStep[];
  rpcUrl: string;
  keystoreJson: string;
  fromAddress: string;
  /** Submission requires explicit opt-in. Default false. */
  broadcastAcp?: boolean;
  /** Submit a signed raw ACP tx; required when broadcastAcp is true. */
  broadcastRawTx?: (rawTx: string) => Promise<{ accepted: boolean; txid?: string; reason?: string }>;
  /** Persist signed bytes/txid BEFORE submission; retries must reconcile this record. */
  persistSignedTx?: (tx: { rawTx: string; txid: string; stepIndex: number }) => Promise<void>;
  /** Signed transaction from an earlier attempt. A retry must not create another signature. */
  priorSignedTx?: { rawTx: string; txid: string; stepIndex: number };
  /** Read chain/API status before any resubmission. Unknown status blocks a new send. */
  lookupTxStatus?: (txid: string) => Promise<"confirmed" | "seen" | "absent" | "unknown">;
};

function isAcpNetwork(network: string): boolean {
  const n = network.trim().toLowerCase();
  return n === "acp";
}

/**
 * Walk routePlan in order. ACP transfer/payment steps are signed (and optionally
 * broadcast). Non-ACP / bridge / swap steps are marked skipped with a reason.
 */
export async function executeRoutePlanLocally(
  input: RouteBroadcastInput
): Promise<{ results: RouteBroadcastStepResult[]; txRefs: SmartPayTxRef[] }> {
  const broadcastAcp = input.broadcastAcp === true;
  const results: RouteBroadcastStepResult[] = [];
  const txRefs: SmartPayTxRef[] = [];

  const steps = [...input.routePlan].sort((a, b) => a.stepIndex - b.stepIndex);
  // Multi-leg dependencies, input reservation and recovery are not implemented.
  // Fail the complete plan before signing any leg, rather than skipping a prerequisite.
  if (steps.length !== 1 || steps.some((step) =>
    !Number.isSafeInteger(step.stepIndex) || step.stepIndex < 0 ||
    !["transfer", "payment"].includes(step.action) || !isAcpNetwork(step.network) ||
    step.fromAsset !== "ACP" || step.toAsset !== "ACP" || step.status !== "ready"
  )) {
    return { results: steps.map((step) => ({
      stepIndex: step.stepIndex, action: step.action, network: step.network,
      status: "skipped" as const, reason: "Only a single ready native ACP payment is supported; reconcile other routes first",
    })), txRefs };
  }
  if (broadcastAcp && (!input.broadcastRawTx || !input.persistSignedTx)) {
    return { results: steps.map((step) => ({
      stepIndex: step.stepIndex, action: step.action, network: step.network,
      status: "failed" as const, reason: "Durable signed transaction persistence and broadcast callback required",
    })), txRefs };
  }
  for (const step of steps) {
    if (step.action === "bridge" || step.action === "swap" || !isAcpNetwork(step.network)) {
      results.push({
        stepIndex: step.stepIndex,
        action: step.action,
        network: step.network,
        status: "skipped",
        reason: `Route step ${step.action}/${step.network} needs chain client — not auto-broadcast`,
      });
      continue;
    }

    const prior = input.priorSignedTx;
    if (prior) {
      if (prior.stepIndex !== step.stepIndex || !prior.txid.trim() || !prior.rawTx.trim()) {
        results.push({
          stepIndex: step.stepIndex,
          action: step.action,
          network: step.network,
          status: "failed",
          reason: "Saved signature does not match this route step",
        });
        break;
      }
      const observed = input.lookupTxStatus ? await input.lookupTxStatus(prior.txid) : "unknown";
      if (observed === "confirmed" || observed === "seen") {
        results.push({
          stepIndex: step.stepIndex,
          action: step.action,
          network: step.network,
          status: "broadcast",
          txid: prior.txid,
          reason: "Existing transaction is already known; no new signature was created",
        });
        txRefs.push({
          network: step.network,
          txid: prior.txid,
          role: step.action === "payment" ? "payment" : "transfer",
          routeStepIndex: step.stepIndex,
        });
        continue;
      }
      if (observed !== "absent") {
        results.push({
          stepIndex: step.stepIndex,
          action: step.action,
          network: step.network,
          status: "submission_unknown",
          txid: prior.txid,
          reason: "Transaction status is unknown. Reconcile before retry.",
        });
        break;
      }
      if (!broadcastAcp) {
        results.push({
          stepIndex: step.stepIndex,
          action: step.action,
          network: step.network,
          status: "signed_local",
          txid: prior.txid,
          reason: "Existing signature is not on the network yet; submission was not requested",
        });
        continue;
      }
      if (!input.broadcastRawTx) {
        results.push({
          stepIndex: step.stepIndex,
          action: step.action,
          network: step.network,
          status: "failed",
          reason: "broadcastRawTx callback required when broadcastAcp is true",
        });
        break;
      }
      let submitted;
      try {
        submitted = await input.broadcastRawTx(prior.rawTx);
      } catch {
        results.push({
          stepIndex: step.stepIndex,
          action: step.action,
          network: step.network,
          status: "submission_unknown",
          txid: prior.txid,
          reason: "Resubmission outcome unknown. Reconcile the same transaction before retrying.",
        });
        break;
      }
      if (!submitted.accepted || (submitted.txid && submitted.txid !== prior.txid)) {
        results.push({
          stepIndex: step.stepIndex,
          action: step.action,
          network: step.network,
          status: "submission_unknown",
          txid: prior.txid,
          reason: "Resubmission did not confirm the saved transaction",
        });
        break;
      }
      results.push({
        stepIndex: step.stepIndex,
        action: step.action,
        network: step.network,
        status: "broadcast",
        txid: prior.txid,
      });
      txRefs.push({
        network: step.network,
        txid: prior.txid,
        role: step.action === "payment" ? "payment" : "transfer",
        routeStepIndex: step.stepIndex,
      });
      continue;
    }

    if (!step.recipient?.trim() || !step.amount || !/^\d+(?:\.\d{1,8})?$/.test(step.amount.trim()) ||
        !/[1-9]/.test(step.amount)) {
      results.push({
        stepIndex: step.stepIndex,
        action: step.action,
        network: step.network,
        status: "failed",
        reason: "ACP route step missing recipient or amount",
      });
      continue;
    }

    try {
      const signed = await signAndPrepareTransfer(input.rpcUrl, input.keystoreJson, {
        from: input.fromAddress,
        to: step.recipient.trim(),
        amountAcp: String(step.amount).trim(),
      });
      if (!broadcastAcp) {
        results.push({
          stepIndex: step.stepIndex,
          action: step.action,
          network: step.network,
          status: "signed_local",
          txid: signed.txid,
        });
        continue;
      }
      if (!input.broadcastRawTx) {
        results.push({
          stepIndex: step.stepIndex,
          action: step.action,
          network: step.network,
          status: "failed",
          reason: "broadcastRawTx callback required when broadcastAcp is true",
        });
        continue;
      }
      await input.persistSignedTx!({ ...signed, stepIndex: step.stepIndex });
      let submitted;
      try {
        submitted = await input.broadcastRawTx(signed.rawTx);
      } catch {
        results.push({ stepIndex: step.stepIndex, action: step.action, network: step.network,
          status: "submission_unknown", txid: signed.txid,
          reason: "Submission outcome unknown. Reconcile the persisted transaction before retrying." });
        break;
      }
      if (!submitted.accepted) {
        results.push({
          stepIndex: step.stepIndex,
          action: step.action,
          network: step.network,
          status: "failed",
          reason: submitted.reason ?? "broadcast rejected",
        });
        continue;
      }
      if (submitted.txid && submitted.txid !== signed.txid) {
        results.push({ stepIndex: step.stepIndex, action: step.action, network: step.network,
          status: "submission_unknown", txid: signed.txid, reason: "Broadcast txid mismatch; reconcile signed transaction" });
        break;
      }
      const txid = signed.txid;
      results.push({
        stepIndex: step.stepIndex,
        action: step.action,
        network: step.network,
        status: "broadcast",
        txid,
      });
      txRefs.push({
        network: step.network,
        txid,
        role: step.action === "payment" ? "payment" : "transfer",
        routeStepIndex: step.stepIndex,
      });
    } catch {
      results.push({
        stepIndex: step.stepIndex,
        action: step.action,
        network: step.network,
        status: "failed",
        reason: "Local signing or durable persistence failed; transaction was not submitted",
      });
    }
  }

  return { results, txRefs };
}
