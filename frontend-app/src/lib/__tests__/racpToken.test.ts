import { describe, expect, it, vi } from "vitest";
import {
  ACP_ADDRESS_RE,
  metamaskDappLink,
  parseRacpHumanToWei,
  redeemTransaction,
  RACP_CONTRACT,
  RACP_NETWORK,
  RACP_WEI_PER_ACP_SMALLEST,
  watchRacpInWallet,
} from "../racpToken";
import type { Eip1193Provider } from "../evmProvider";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("rACP wallet import", () => {
  it("builds a MetaMask mobile dapp deep link for phone connect", () => {
    expect(metamaskDappLink("/tokens/racp")).toBe("https://metamask.app.link/dapp/ancap.cloud/tokens/racp");
    expect(metamaskDappLink("/tokens/racp/airdrop")).toContain("/tokens/racp/airdrop");
  });
  it("refuses to import on a wallet that stays on the wrong network", async () => {
    const request = vi.fn(async ({ method }: { method: string }) => {
      if (method === "eth_requestAccounts") return ["0x" + "11".repeat(20)];
      if (method === "eth_chainId") return "0x38";
      return null;
    });
    await expect(watchRacpInWallet({ request })).rejects.toThrow("another chain");
    expect(request.mock.calls.some(([x]) => x.method === "wallet_watchAsset")).toBe(false);
  });
  it("adds an unknown chain, checks it, then imports the exact token", async () => {
    let chain = "0x38";
    let added = false;
    const request: Eip1193Provider["request"] = vi.fn(async (args) => {
      if (args.method === "eth_requestAccounts") return ["0x" + "11".repeat(20)];
      if (args.method === "eth_chainId") return chain;
      if (args.method === "wallet_switchEthereumChain") {
        if (!added) throw { code: 4902 };
        chain = "0x1237";
      }
      if (args.method === "wallet_addEthereumChain") { expect(args.params).toEqual([RACP_NETWORK]); added = true; }
      if (args.method === "wallet_watchAsset") { expect(args.params).toMatchObject({ type: "ERC20", options: { address: RACP_CONTRACT, decimals: 18, symbol: "rACP" } }); return true; }
      return null;
    });
    expect(await watchRacpInWallet({ request })).toBe(true);
  });
  it("keeps a rejected import unsuccessful", async () => {
    const request: Eip1193Provider["request"] = async ({ method }) => {
      if (method === "eth_requestAccounts") return ["0x" + "11".repeat(20)];
      if (method === "eth_chainId") return "0x1237";
      return false;
    };
    expect(await watchRacpInWallet({ request })).toBe(false);
  });
  it("publishes rACP on its actual chain without removing wACP", () => {
    const list = JSON.parse(readFileSync(resolve(process.cwd(), "public/tokenlist.json"), "utf8"));
    expect(list.tokens.find((t: {symbol: string}) => t.symbol === "wACP").chainId).toBe(56);
    expect(list.tokens.find((t: {symbol: string}) => t.symbol === "rACP")).toMatchObject({ chainId: 4663, address: RACP_CONTRACT, decimals: 18 });
  });
});

describe("rACP redeem encoding", () => {
  it("maps 10 rACP to aligned wei and builds requestRedemption calldata", () => {
    const wei = parseRacpHumanToWei("10");
    expect(wei % RACP_WEI_PER_ACP_SMALLEST).toBe(0n);
    expect(ACP_ADDRESS_RE.test("acp1qqqsdr00nem230z3e84stqkx7drh2xwncupts2lz")).toBe(true);
    const account = "0x" + "11".repeat(20);
    const tx = redeemTransaction(account, wei, "acp1qqqsdr00nem230z3e84stqkx7drh2xwncupts2lz");
    expect(tx.to).toBe(RACP_CONTRACT);
    expect(tx.value).toBe("0x0");
    expect(tx.data.startsWith("0x86511595")).toBe(true);
    expect(tx.from).toBe(account);
  });
  it("rejects unaligned amounts and bad ACP addresses", () => {
    expect(() => parseRacpHumanToWei("0.000000000000000001")).toThrow();
    expect(() =>
      redeemTransaction("0x" + "11".repeat(20), 10n * 10n ** 18n, "0xdead"),
    ).toThrow(/ACP address/i);
  });
});
