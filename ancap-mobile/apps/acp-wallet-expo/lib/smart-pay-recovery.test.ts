import { describe, expect, it } from "vitest";

import {
  canSubmitSmartPayRecoveryInput,
  formatSmartPayRecoveryRefPreview,
  getSmartPayRecoveryInputBlockReason,
  normalizeSmartPayRecoveryRef,
  normalizeSmartPayRecoveryToken,
  parseSmartPayRecoveryInput,
} from "./smart-pay-recovery";

describe("smart pay recovery helpers", () => {
  it("does not infer trusted networks from lookalike explorer domains", () => {
    for (const hostname of ["bscscan.com.evil.example", "fakebasescan.org", "ancap.cloud.evil.example"]) {
      const ref = normalizeSmartPayRecoveryRef(`https://${hostname}/acp/tx/fixture-tx-alpha`);
      expect(ref?.network).toBeNull();
    }
    expect(normalizeSmartPayRecoveryRef("https://testnet.bscscan.com/tx/fixture-tx-alpha")?.network).toBe("bsc");
  });

  it("parses explorer links into structured recovery refs with inferred network", () => {
    expect(
      normalizeSmartPayRecoveryRef("https://bscscan.com/tx/fixture-tx-alpha")
    ).toEqual({
      txid: "fixture-tx-alpha",
      network: "bsc",
      explorerUrl: "https://bscscan.com/tx/fixture-tx-alpha",
    });

    expect(
      normalizeSmartPayRecoveryRef("https://ancap.cloud/acp/transactions/tx-789")
    ).toEqual({
      txid: "tx-789",
      network: "acp",
      explorerUrl: "https://ancap.cloud/acp/transactions/tx-789",
    });
  });

  it("preserves raw tx hashes when no explorer metadata is available", () => {
    expect(normalizeSmartPayRecoveryRef("  fixture-feed-proof  ")).toEqual({
      txid: "fixture-feed-proof",
      network: null,
      explorerUrl: null,
    });
    expect(normalizeSmartPayRecoveryToken("  fixture-feed-proof  ")).toBe("fixture-feed-proof");
  });

  it("rejects structured locator noise that does not expose a tx id", () => {
    expect(normalizeSmartPayRecoveryRef("https://merchant.example/invoice/123")).toBeNull();
    expect(normalizeSmartPayRecoveryRef("merchant.example/pay?id=123")).toBeNull();
  });

  it("deduplicates recovery refs case-insensitively while keeping richer explorer metadata", () => {
    const parsed = parseSmartPayRecoveryInput(
      [
        "FIXTURE-TX-ALPHA",
        "https://basescan.org/tx/fixture-tx-alpha",
        "https://etherscan.io/tx/fixture-tx-beta",
        "FIXTURE-TX-BETA",
      ].join("\n")
    );

    expect(parsed.txids).toEqual(["fixture-tx-alpha", "fixture-tx-beta"]);
    expect(parsed.duplicateTokens).toEqual([
      "https://basescan.org/tx/fixture-tx-alpha",
      "FIXTURE-TX-BETA",
    ]);
    expect(parsed.invalidTokens).toEqual([]);
    expect(parsed.refs).toEqual([
      {
        txid: "fixture-tx-alpha",
        network: "base",
        explorerUrl: "https://basescan.org/tx/fixture-tx-alpha",
      },
      {
        txid: "fixture-tx-beta",
        network: "ethereum",
        explorerUrl: "https://etherscan.io/tx/fixture-tx-beta",
      },
    ]);
  });

  it("blocks submission when pasted recovery input only contains invalid structured noise", () => {
    const input = "https://merchant.example/invoice/123 https://merchant.example/pay?id=456";

    expect(canSubmitSmartPayRecoveryInput(input)).toBe(false);
    expect(getSmartPayRecoveryInputBlockReason(input)).toBe(
      "No valid tx hash or explorer link was parsed from this recovery input. Fix the pasted values or clear the field to run a status-only recovery pass."
    );
  });

  it("allows empty status-only passes and formats preview text for valid refs", () => {
    expect(canSubmitSmartPayRecoveryInput("   ")).toBe(true);
    expect(getSmartPayRecoveryInputBlockReason("   ")).toBeNull();
    expect(
      formatSmartPayRecoveryRefPreview({
        txid: "fixture-tx-alpha",
        network: "base",
        explorerUrl: "https://basescan.org/tx/fixture-tx-alpha",
      })
    ).toBe("BASE · fixture-tx-alpha · explorer link preserved");
  });
});
