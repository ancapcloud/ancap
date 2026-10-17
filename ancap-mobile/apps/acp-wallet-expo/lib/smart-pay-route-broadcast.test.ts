import { beforeEach, describe, expect, it, vi } from "vitest";

const signAndPrepareTransfer = vi.fn();

vi.mock("@ancap/acp-wallet-sdk", () => ({
  signAndPrepareTransfer: (...args: unknown[]) => signAndPrepareTransfer(...args),
}));

import { executeRoutePlanLocally } from "./smart-pay-route-broadcast";

describe("executeRoutePlanLocally", () => {
  beforeEach(() => {
    signAndPrepareTransfer.mockReset();
    signAndPrepareTransfer.mockResolvedValue({
      txid: "txid-acp-1",
      rawTx: "raw-1",
    });
  });

  it("skips bridge/swap legs and broadcasts ACP transfer", async () => {
    const broadcastRawTx = vi.fn(async () => ({ accepted: true, txid: "txid-acp-1" }));
    const { results, txRefs } = await executeRoutePlanLocally({
      rpcUrl: "https://example/rpc",
      keystoreJson: "{}",
      fromAddress: "acp1from",
      broadcastRawTx,
      routePlan: [
        {
          stepIndex: 0,
          action: "bridge",
          network: "bsc",
          fromAsset: "ACP",
          toAsset: "wACP",
          status: "ready",
        },
        {
          stepIndex: 1,
          action: "transfer",
          network: "acp",
          fromAsset: "ACP",
          toAsset: "ACP",
          amount: "1.5",
          recipient: "acp1to",
          status: "ready",
        },
      ],
    });

    expect(results[0]?.status).toBe("skipped");
    expect(results[1]?.status).toBe("broadcast");
    expect(txRefs).toHaveLength(1);
    expect(broadcastRawTx).toHaveBeenCalledWith("raw-1");
    expect(signAndPrepareTransfer).toHaveBeenCalledTimes(1);
  });

  it("can sign ACP legs without broadcasting", async () => {
    const { results, txRefs } = await executeRoutePlanLocally({
      rpcUrl: "https://example/rpc",
      keystoreJson: "{}",
      fromAddress: "acp1from",
      broadcastAcp: false,
      routePlan: [
        {
          stepIndex: 0,
          action: "payment",
          network: "acp",
          fromAsset: "ACP",
          toAsset: "ACP",
          amount: "2",
          recipient: "acp1merchant",
          status: "ready",
        },
      ],
    });
    expect(results[0]?.status).toBe("signed_local");
    expect(txRefs).toHaveLength(0);
  });
});
