import { beforeEach, describe, expect, it, vi } from "vitest";
import type { SmartPayRouteExecutionStep } from "@ancap/acp-api-client";
const signAndPrepareTransfer = vi.fn();
vi.mock("@ancap/acp-wallet-sdk", () => ({
  signAndPrepareTransfer: (...args: unknown[]) => signAndPrepareTransfer(...args),
}));
import { executeRoutePlanLocally } from "./smart-pay-route-broadcast";
const step: SmartPayRouteExecutionStep = { stepIndex: 0, action: "payment", network: "acp",
  fromAsset: "ACP", toAsset: "ACP", amount: "1.5", recipient: "acp1merchant", status: "ready" };
const base = { rpcUrl: "https://example/rpc", keystoreJson: "{}", fromAddress: "acp1from" };
describe("executeRoutePlanLocally", () => {
  beforeEach(() => { signAndPrepareTransfer.mockReset();
    signAndPrepareTransfer.mockResolvedValue({ txid: "signed-id", rawTx: "signed-bytes" }); });
  it("defaults to signing only", async () => {
    const broadcastRawTx = vi.fn();
    const out = await executeRoutePlanLocally({ ...base, routePlan: [step], broadcastRawTx });
    expect(out.results[0].status).toBe("signed_local");
    expect(broadcastRawTx).not.toHaveBeenCalled();
  });
  it("blocks the whole route if an unsupported prerequisite exists", async () => {
    const out = await executeRoutePlanLocally({ ...base, routePlan: [
      { ...step, action: "bridge", network: "bsc" }, { ...step, stepIndex: 1 } ] });
    expect(out.results.every(r => r.status === "skipped")).toBe(true);
    expect(signAndPrepareTransfer).not.toHaveBeenCalled();
  });
  it.each([
    { network: "acp-evil" }, { fromAsset: "wACP" }, { status: "confirmed" },
    { status: "pending" }, { status: "signed" }, { stepIndex: -1 }, { stepIndex: 0.5 },
  ])("rejects unsupported or already handled step %j before signing", async patch => {
    await executeRoutePlanLocally({ ...base, routePlan: [{ ...step, ...patch } as SmartPayRouteExecutionStep] });
    expect(signAndPrepareTransfer).not.toHaveBeenCalled();
  });
  it.each(["0", "-1", "NaN", "Infinity", "1e3", "1.000000001"])("rejects invalid amount %s", async amount => {
    const out = await executeRoutePlanLocally({ ...base, routePlan: [{ ...step, amount }] });
    expect(out.results[0].status).toBe("failed");
    expect(signAndPrepareTransfer).not.toHaveBeenCalled();
  });
  it("requires durable persistence before signing for submission", async () => {
    await executeRoutePlanLocally({ ...base, routePlan: [step], broadcastAcp: true, broadcastRawTx: vi.fn() });
    expect(signAndPrepareTransfer).not.toHaveBeenCalled();
  });
  it("persists signed bytes before broadcasting and returns tx references", async () => {
    const order: string[] = [];
    const out = await executeRoutePlanLocally({ ...base, routePlan: [step], broadcastAcp: true,
      persistSignedTx: async tx => { expect(tx.txid).toBe("signed-id"); order.push("persist"); },
      broadcastRawTx: async raw => { expect(raw).toBe("signed-bytes"); order.push("broadcast");
        return { accepted: true, txid: "signed-id" }; } });
    expect(order).toEqual(["persist", "broadcast"]);
    expect(out.results[0].status).toBe("broadcast");
    expect(out.txRefs[0].txid).toBe("signed-id");
  });
  it("does not broadcast if persistence fails or expose raw error secrets", async () => {
    const broadcastRawTx = vi.fn();
    const out = await executeRoutePlanLocally({ ...base, routePlan: [step], broadcastAcp: true,
      persistSignedTx: async () => { throw new Error("secret keystore"); }, broadcastRawTx });
    expect(broadcastRawTx).not.toHaveBeenCalled();
    expect(JSON.stringify(out)).not.toContain("secret keystore");
  });
  it("retains signed txid on ambiguous submission without claiming failure or retrying", async () => {
    const out = await executeRoutePlanLocally({ ...base, routePlan: [step], broadcastAcp: true,
      persistSignedTx: async () => {}, broadcastRawTx: async () => { throw new Error("timeout"); } });
    expect(out.results[0].status).toBe("submission_unknown");
    expect(out.results[0].txid).toBe("signed-id");
    expect(signAndPrepareTransfer).toHaveBeenCalledTimes(1);
  });
  it("reconciles a known transaction before any new signature", async () => {
    const broadcastRawTx = vi.fn();
    const prior = { rawTx: "saved-bytes", txid: "saved-id", stepIndex: 0 };
    const out = await executeRoutePlanLocally({ ...base, routePlan: [step], broadcastAcp: true,
      priorSignedTx: prior, lookupTxStatus: async () => "confirmed", broadcastRawTx,
      persistSignedTx: async () => {} });
    expect(signAndPrepareTransfer).not.toHaveBeenCalled();
    expect(broadcastRawTx).not.toHaveBeenCalled();
    expect(out.results[0].status).toBe("broadcast");
    expect(out.results[0].txid).toBe("saved-id");
  });
  it("blocks retry while transaction status is unknown", async () => {
    const broadcastRawTx = vi.fn();
    const out = await executeRoutePlanLocally({ ...base, routePlan: [step], broadcastAcp: true,
      priorSignedTx: { rawTx: "saved-bytes", txid: "saved-id", stepIndex: 0 },
      broadcastRawTx, persistSignedTx: async () => {} });
    expect(signAndPrepareTransfer).not.toHaveBeenCalled();
    expect(broadcastRawTx).not.toHaveBeenCalled();
    expect(out.results[0].status).toBe("submission_unknown");
  });
  it("resubmits the same signed bytes only after the transaction is absent", async () => {
    const broadcastRawTx = vi.fn(async () => ({ accepted: true, txid: "saved-id" }));
    const out = await executeRoutePlanLocally({ ...base, routePlan: [step], broadcastAcp: true,
      priorSignedTx: { rawTx: "saved-bytes", txid: "saved-id", stepIndex: 0 },
      lookupTxStatus: async () => "absent", broadcastRawTx, persistSignedTx: async () => {} });
    expect(signAndPrepareTransfer).not.toHaveBeenCalled();
    expect(broadcastRawTx).toHaveBeenCalledWith("saved-bytes");
    expect(out.results[0].txid).toBe("saved-id");
  });
});
