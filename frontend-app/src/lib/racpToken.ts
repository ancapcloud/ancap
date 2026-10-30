import type { Eip1193Provider } from "@/lib/evmProvider";

export const RACP_CONTRACT = "0xD53f91A63f95beAc61Ec8417c40C5e620FE3a911";
export const RACP_WETH_POOL = "0x7583745440e9e8CBdCaeC3BF97dD02d9872d9c85";
export const RACP_POOL_URL = "https://pancakeswap.finance/liquidity/pool/robinhood/0x7583745440e9e8CBdCaeC3BF97dD02d9872d9c85?chain=robinhood";
export const RACP_CHAIN_ID = 4663;
export const RACP_CHAIN_HEX = "0x1237";
export const RACP_EXPLORER = "https://robinhoodchain.blockscout.com";
export const RACP_RESERVE = "acp1qqqsdr00nem230z3e84stqkx7drh2xwncupts2lz";
export const RACP_ISSUANCE_TX = "0xe9b437c7e2260ae284ae011fdae4699b9bca63e3712997ffad28be8d105334e8";
export const RACP_FUNDING_TX = "1b369ac2dc6c21c84e1ca798bd5f4059a5c45ea4ca25ef5068042533a77cd0c2";
export const RACP_PUBLIC_ORIGIN = "https://ancap.cloud";
export const RACP_DAPP_PATH = "/tokens/racp";
export const RACP_NETWORK = {
  chainId: RACP_CHAIN_HEX,
  chainName: "Robinhood Chain",
  nativeCurrency: { name: "Ether", symbol: "ETH", decimals: 18 },
  rpcUrls: ["https://rpc.mainnet.chain.robinhood.com"],
  blockExplorerUrls: [RACP_EXPLORER],
};

export function isLikelyMobileBrowser(): boolean {
  if (typeof navigator === "undefined") return false;
  return /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);
}

/** Fallback: open the page inside MetaMask's in-app browser (not Chrome→MetaMask Connect). */
export function metamaskDappLink(path: string = RACP_DAPP_PATH): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `https://metamask.app.link/dapp/ancap.cloud${normalized}`;
}

export async function ensureRobinhoodChain(provider: Eip1193Provider): Promise<void> {
  if (!provider) throw new Error("No compatible EVM wallet");
  const chainId = () => provider.request({ method: "eth_chainId" });
  if (BigInt(String(await chainId())) !== BigInt(RACP_CHAIN_ID)) {
    try {
      await provider.request({ method: "wallet_switchEthereumChain", params: [{ chainId: RACP_CHAIN_HEX }] });
    } catch (error) {
      if (typeof error !== "object" || error === null || !("code" in error) || Number(error.code) !== 4902) throw error;
      await provider.request({ method: "wallet_addEthereumChain", params: [RACP_NETWORK] });
      await provider.request({ method: "wallet_switchEthereumChain", params: [{ chainId: RACP_CHAIN_HEX }] });
    }
  }
  if (BigInt(String(await chainId())) !== BigInt(RACP_CHAIN_ID)) throw new Error("Wallet is on another chain");
}

/** No signing, token approval or transaction: only a wallet network/import prompt. */
export async function watchRacpInWallet(provider?: Eip1193Provider | null): Promise<boolean> {
  const { resolveEvmProvider } = await import("@/lib/metamaskConnect");
  const active = provider ?? (await resolveEvmProvider([RACP_CHAIN_HEX]));
  await active.request({ method: "eth_requestAccounts" });
  await ensureRobinhoodChain(active);
  return (await active.request({ method: "wallet_watchAsset", params: {
    type: "ERC20", options: { address: RACP_CONTRACT, symbol: "rACP", decimals: 18, image: `${RACP_PUBLIC_ORIGIN}/racp-logo.png` },
  } })) !== false;
}

/** 10^11 wei = 1 native ACP unit; contract rejects non-multiples. */
export const RACP_WEI_PER_ACP_SMALLEST = 100_000_000_000n;
export const RACP_PER_ACP = 10n;
export const ACP_ADDRESS_RE = /^acp1[a-z0-9]{20,100}$/;

export function parseRacpHumanToWei(amount: string): bigint {
  const raw = amount.trim();
  if (!/^\d+(\.\d{1,18})?$/.test(raw)) throw new Error("Invalid rACP amount");
  const [whole, frac = ""] = raw.split(".");
  const wei = BigInt(whole) * 10n ** 18n + BigInt((frac + "0".repeat(18)).slice(0, 18));
  if (wei <= 0n || wei % RACP_WEI_PER_ACP_SMALLEST !== 0n) throw new Error("Amount must map to whole ACP units (multiples of 0.0000001 rACP / 10^-7)");
  return wei;
}

/** Encode requestRedemption(uint256,string) — selector 0x86511595. */
export function redeemTransaction(account: string, amountWei: bigint, acpAddress: string) {
  if (!/^0x[0-9a-f]{40}$/i.test(account)) throw new Error("Invalid EVM account");
  if (!ACP_ADDRESS_RE.test(acpAddress.trim())) throw new Error("Invalid ACP address");
  if (amountWei <= 0n || amountWei % RACP_WEI_PER_ACP_SMALLEST !== 0n) throw new Error("Invalid redeem amount");
  const dest = acpAddress.trim();
  const word = (value: bigint) => value.toString(16).padStart(64, "0");
  const strBytes = new TextEncoder().encode(dest);
  const strHex = Array.from(strBytes, (b) => b.toString(16).padStart(2, "0")).join("");
  const paddedLen = Math.ceil(strBytes.length / 32) * 64;
  const data =
    "0x86511595" +
    word(amountWei) +
    word(64n) +
    word(BigInt(strBytes.length)) +
    strHex.padEnd(paddedLen, "0");
  return { from: account, to: RACP_CONTRACT, data, value: "0x0", chainId: RACP_CHAIN_HEX };
}
