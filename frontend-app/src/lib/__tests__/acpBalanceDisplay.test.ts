import { describe, expect, it } from "vitest";
import {
  formatAcpDisplay,
  selectDragonAcp,
  selectHeroAcp,
  selectOnChainAtDeposit,
  selectPlatformLedger,
  selectWithdrawableNow,
} from "../acpBalanceDisplay";

const HOT = "acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9";

describe("acpBalanceDisplay", () => {
  it("hero prefers primary over on-chain zero and headline", () => {
    expect(
      selectHeroAcp({
        primary_acp: "100",
        headline_acp: "100",
        acp: "100",
        on_chain_acp: "0",
      }),
    ).toBe("100");
  });

  it("hero never falls back to on_chain_acp alone", () => {
    expect(selectHeroAcp({ on_chain_acp: "999" })).toBeNull();
    expect(selectHeroAcp({ acp: "42", on_chain_acp: "999" })).toBe("42");
  });

  it("withdrawable uses withdrawable_now then available", () => {
    expect(selectWithdrawableNow({ withdrawable_now_acp: "7", available_acp: "9", acp: "9" })).toBe("7");
    expect(selectWithdrawableNow({ available_acp: "9", acp: "3" })).toBe("9");
    expect(selectWithdrawableNow({})).toBe("0");
  });

  it("partition selectors prefer new fields", () => {
    expect(
      selectOnChainAtDeposit({ on_chain_at_deposit_acp: "1", on_chain_acp: "2" }),
    ).toBe("1");
    expect(
      selectPlatformLedger({
        platform_ledger_acp: "50",
        platform_credits_acp: "40",
        ledger_credits_acp: "30",
      }),
    ).toBe("50");
  });

  it("dragon balance keeps ACP that left wACP and skips design fallbacks", () => {
    expect(
      selectDragonAcp(
        {
          address: "acp1qpersonaladdress000000000000000",
          on_chain_at_deposit_acp: "1000.5",
          operator_hot_live_acp: "20",
          tokenomics_buckets: [
            { key: "bridge_reserve", label: "Bridge reserve", acp: "32883823.16372116" },
            { key: "public", label: "Public & liquidity", acp: "25200000" },
          ],
        },
        HOT,
      ),
    ).toBe("32884843.66372116");
    expect(
      selectDragonAcp(
        {
          address: HOT,
          on_chain_at_deposit_acp: "20",
          operator_hot_live_acp: "20",
          tokenomics_buckets: [
            { key: "bridge_reserve", label: "Bridge reserve (design; probe unavailable)", acp: "0" },
          ],
        },
        HOT,
      ),
    ).toBe("20");
  });

  it("formatAcpDisplay compacts large balances", () => {
    expect(formatAcpDisplay("205036960.66474406")).toMatch(/205,036,960/);
    expect(formatAcpDisplay("108726.00465741")).toMatch(/108,726/);
    expect(formatAcpDisplay("0")).toBe("0");
    expect(formatAcpDisplay(null)).toBe("0");
  });
});
