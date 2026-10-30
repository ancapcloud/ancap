import { describe, expect, it, vi } from "vitest";
import { RACP_CONTRACT, RACP_NETWORK, watchRacpInWallet } from "../racpToken";
import type { Eip1193Provider } from "../evmProvider";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("rACP wallet import", () => {
  it("refuses to import on a wallet that stays on the wrong network", async () => {
    const request = vi.fn(async ({ method }: { method: string }) => method === "eth_chainId" ? "0x38" : null);
    await expect(watchRacpInWallet({ request })).rejects.toThrow("another chain");
    expect(request.mock.calls.some(([x]) => x.method === "wallet_watchAsset")).toBe(false);
  });
  it("adds an unknown chain, checks it, then imports the exact token", async () => {
    let chain = "0x38";
    let added = false;
    const request: Eip1193Provider["request"] = vi.fn(async (args) => {
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
    const request: Eip1193Provider["request"] = async ({ method }) => method === "eth_chainId" ? "0x1237" : false;
    expect(await watchRacpInWallet({ request })).toBe(false);
  });
  it("publishes rACP on its actual chain without removing wACP", () => {
    const list = JSON.parse(readFileSync(resolve(process.cwd(), "public/tokenlist.json"), "utf8"));
    expect(list.tokens.find((t: {symbol: string}) => t.symbol === "wACP").chainId).toBe(56);
    expect(list.tokens.find((t: {symbol: string}) => t.symbol === "rACP")).toMatchObject({ chainId: 4663, address: RACP_CONTRACT, decimals: 18 });
  });
});
