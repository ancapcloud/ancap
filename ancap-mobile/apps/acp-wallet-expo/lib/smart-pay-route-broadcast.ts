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
  status: "broadcast" | "signed_local" | "skipped" | "failed";
  txid?: string;
  reason?: string;
};

export type RouteBroadcastInput = {
  routePlan: SmartPayRouteExecutionStep[];
  rpcUrl: string;
  keystoreJson: string;
  fromAddress: string;
  /** When false, ACP legs are signed but not submitted. Default true. */
  broadcastAcp?: boolean;
  /** Submit a signed raw ACP tx; required when broadcastAcp is true. */
  broadcastRawTx?: (rawTx: string) => Promise<{ accepted: boolean; txid?: string; reason?: string }>;
};

function isAcpNetwork(network: string): boolean {
  const n = network.trim().toLowerCase();
  return n === "acp" || n === "ancap" || n.startsWith("acp");
}

/**
 * Walk routePlan in order. ACP transfer/payment steps are signed (and optionally
 * broadcast). Non-ACP / bridge / swap steps are marked skipped with a reason.
 */
export async function executeRoutePlanLocally(
  input: RouteBroadcastInput
): Promise<{ results: RouteBroadcastStepResult[]; txRefs: SmartPayTxRef[] }> {
  const broadcastAcp = input.broadcastAcp !== false;
  const results: RouteBroadcastStepResult[] = [];
  const txRefs: SmartPayTxRef[] = [];

  const steps = [...input.routePlan].sort((a, b) => a.stepIndex - b.stepIndex);
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

    if (!step.recipient || !step.amount) {
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
      const submitted = await input.broadcastRawTx(signed.rawTx);
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
      const txid = submitted.txid || signed.txid;
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
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      results.push({
        stepIndex: step.stepIndex,
        action: step.action,
        network: step.network,
        status: "failed",
        reason: message.slice(0, 240),
      });
    }
  }

  return { results, txRefs };
}
