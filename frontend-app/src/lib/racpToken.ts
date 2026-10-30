import { getPreferredEvmProvider, type Eip1193Provider } from "@/lib/evmProvider";

export const RACP_CONTRACT = "0xD53f91A63f95beAc61Ec8417c40C5e620FE3a911";
export const RACP_CHAIN_ID = 4663;
export const RACP_CHAIN_HEX = "0x1237";
export const RACP_EXPLORER = "https://robinhoodchain.blockscout.com";
export const RACP_RESERVE = "acp1qqqsdr00nem230z3e84stqkx7drh2xwncupts2lz";
export const RACP_ISSUANCE_TX = "0xe9b437c7e2260ae284ae011fdae4699b9bca63e3712997ffad28be8d105334e8";
export const RACP_FUNDING_TX = "1b369ac2dc6c21c84e1ca798bd5f4059a5c45ea4ca25ef5068042533a77cd0c2";
export const RACP_NETWORK = {
  chainId: RACP_CHAIN_HEX,
  chainName: "Robinhood Chain",
  nativeCurrency: { name: "Ether", symbol: "ETH", decimals: 18 },
  rpcUrls: ["https://rpc.mainnet.chain.robinhood.com"],
  blockExplorerUrls: [RACP_EXPLORER],
};

/** No signing, token approval or transaction: only a wallet network/import prompt. */
export async function watchRacpInWallet(provider: Eip1193Provider | null = getPreferredEvmProvider() ?? null): Promise<boolean> {
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
  return (await provider.request({ method: "wallet_watchAsset", params: {
    type: "ERC20", options: { address: RACP_CONTRACT, symbol: "rACP", decimals: 18, image: "https://ancap.cloud/racp-logo.png" },
  } })) !== false;
}
