import type { Eip1193Provider } from "@/lib/evmProvider";
import { RACP_CHAIN_HEX, RACP_NETWORK } from "@/lib/racpToken";

type EvmClient = {
  connect: (opts: { chainIds: string[] }) => Promise<{ accounts: string[]; chainId: string }>;
  getProvider: () => Eip1193Provider | null | undefined;
};

const BSC_HEX = "0x38";
const BSC_RPC = "https://bsc-dataseed.binance.org/";

let clientPromise: Promise<EvmClient> | null = null;

function dappUrl(): string {
  if (typeof window !== "undefined" && window.location?.origin) return window.location.origin;
  return "https://ancap.cloud";
}

async function getEvmClient(): Promise<EvmClient> {
  if (!clientPromise) {
    clientPromise = (async () => {
      const { createEVMClient } = await import("@metamask/connect-evm");
      return (await createEVMClient({
        dapp: {
          name: "ANCAP",
          url: dappUrl(),
          iconUrl: `${dappUrl()}/racp-logo.png`,
        },
        api: {
          supportedNetworks: {
            [RACP_CHAIN_HEX]: RACP_NETWORK.rpcUrls[0],
            [BSC_HEX]: BSC_RPC,
          },
        },
        // Keep false so Chrome/iOS deeplinks into MetaMask app instead of a QR install modal.
        ui: { showInstallModal: false },
      })) as unknown as EvmClient;
    })();
  }
  return clientPromise;
}

/**
 * Connect MetaMask from a mobile browser (Chrome on iPhone) via MetaMask Connect.
 * Opens the MetaMask app for approval, then returns an EIP-1193 provider usable back in Chrome.
 */
export async function connectMetaMaskProvider(chainIds: string[] = [RACP_CHAIN_HEX]): Promise<Eip1193Provider> {
  if (typeof window === "undefined") throw new Error("MetaMask Connect requires a browser");
  const client = await getEvmClient();
  await client.connect({ chainIds: chainIds.length ? chainIds : [RACP_CHAIN_HEX] });
  const provider = client.getProvider();
  if (!provider || typeof provider.request !== "function") {
    throw new Error("MetaMask connected but no provider was returned");
  }
  return provider;
}

/** Prefer injected MetaMask; otherwise connect through MetaMask Connect (Chrome iOS / mobile). */
export async function resolveEvmProvider(chainIds?: string[]): Promise<Eip1193Provider> {
  const { getPreferredEvmProvider } = await import("@/lib/evmProvider");
  const injected = getPreferredEvmProvider();
  if (injected) return injected;
  return connectMetaMaskProvider(chainIds);
}
