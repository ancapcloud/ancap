/** Canonical wACP (BEP-20) metadata for wallet_watchAsset (EIP-747). */
export const WACP_BSC_CONTRACT = "0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402";
export const WACP_SYMBOL = "wACP";
export const WACP_DECIMALS = 18;
export const BSC_CHAIN_ID_HEX = "0x38";
export const BSC_CHAIN_ID = 56;
/** PancakeSwap V2 thin reference (checkout oracle until V3 gate). */
export const WACP_V2_POOL = "0xF391ca2bcBaB93Afa23326ebF1e35DB950841601";
/** PancakeSwap V3 wACP/USDT 0.25% bootstrap (shallow — not oracle by default). */
export const WACP_V3_POOL = "0xe626bd3ef516c4f784e5d5fb46e297d9c0d7f5e1";
export const WACP_USDT_BSC = "0x55d398326f99059fF775485246999027B3197955";
export const WACP_TOKEN_IMAGE_ORIGIN = "https://ancap.cloud";
export const WACP_LOGO_PATH = "/wacp-logo.png";

export type WatchAssetParams = {
  type: "ERC20";
  options: {
    address: string;
    symbol: string;
    decimals: number;
    image: string;
  };
};

export function getWacpLogoUrl(origin?: string): string {
  const base = (origin?.trim() || WACP_TOKEN_IMAGE_ORIGIN).replace(/\/+$/, "");
  return `${base}${WACP_LOGO_PATH}`;
}

/** @deprecated Use getWacpLogoUrl — kept for callers expecting this name. */
export function getWacpTokenImageUrl(origin?: string): string {
  return getWacpLogoUrl(origin);
}

export function buildWacpWatchAssetParams(
  contractAddress: string = WACP_BSC_CONTRACT,
  imageUrl?: string,
): WatchAssetParams {
  return {
    type: "ERC20",
    options: {
      address: contractAddress,
      symbol: WACP_SYMBOL,
      decimals: WACP_DECIMALS,
      image: imageUrl || getWacpLogoUrl(),
    },
  };
}
