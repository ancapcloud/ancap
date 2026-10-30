import { getPreferredEvmProvider, type Eip1193Provider } from "@/lib/evmProvider";
import {
  BSC_CHAIN_ID,
  BSC_CHAIN_ID_HEX,
  buildWacpWatchAssetParams,
  getWacpTokenImageUrl,
} from "@/lib/wacpToken";

export type WatchWacpResult =
  | { ok: true }
  | { ok: false; reason: "no_provider" | "rejected" | "error"; message: string };

function normalizeChainId(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return null;
    if (trimmed.startsWith("0x") || trimmed.startsWith("0X")) {
      const parsed = Number.parseInt(trimmed, 16);
      return Number.isFinite(parsed) ? parsed : null;
    }
    const parsed = Number(trimmed);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

async function ensureBscChain(provider: Eip1193Provider): Promise<void> {
  const chainRaw = await provider.request({ method: "eth_chainId" });
  const chainId = normalizeChainId(chainRaw);
  if (chainId === BSC_CHAIN_ID) return;

  try {
    await provider.request({
      method: "wallet_switchEthereumChain",
      params: [{ chainId: BSC_CHAIN_ID_HEX }],
    });
    return;
  } catch (err: unknown) {
    const code =
      typeof err === "object" && err && "code" in err
        ? Number((err as { code?: unknown }).code)
        : undefined;
    if (code !== 4902) throw err;
  }

  await provider.request({
    method: "wallet_addEthereumChain",
    params: [
      {
        chainId: BSC_CHAIN_ID_HEX,
        chainName: "BNB Smart Chain",
        nativeCurrency: { name: "BNB", symbol: "BNB", decimals: 18 },
        rpcUrls: ["https://bsc-dataseed.binance.org/"],
        blockExplorerUrls: ["https://bscscan.com/"],
      },
    ],
  });
}

/** Prompt MetaMask (or compatible wallet) to add wACP with logo via wallet_watchAsset. */
export async function watchWacpInWallet(contractAddress?: string): Promise<WatchWacpResult> {
  let provider: Eip1193Provider | undefined = getPreferredEvmProvider();
  if (!provider) {
    try {
      const { resolveEvmProvider } = await import("@/lib/metamaskConnect");
      provider = await resolveEvmProvider([BSC_CHAIN_ID_HEX]);
    } catch {
      return {
        ok: false,
        reason: "no_provider",
        message: "Install MetaMask, open this page in Chrome, then connect and return to Chrome.",
      };
    }
  }
  if (!provider) {
    return {
      ok: false,
      reason: "no_provider",
      message: "Install MetaMask, open this page in Chrome, then connect and return to Chrome.",
    };
  }

  try {
    await ensureBscChain(provider);
    const imageUrl =
      typeof window !== "undefined" ? getWacpTokenImageUrl(window.location.origin) : undefined;
    const params = buildWacpWatchAssetParams(contractAddress, imageUrl);
    const added = await provider.request({
      method: "wallet_watchAsset",
      params,
    });
    if (added === false) {
      return {
        ok: false,
        reason: "rejected",
        message: "Token was not added. You can approve it in the wallet prompt.",
      };
    }
    return { ok: true };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Failed to add wACP to wallet.";
    return { ok: false, reason: "error", message };
  }
}
