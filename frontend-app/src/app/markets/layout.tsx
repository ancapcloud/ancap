import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Markets — wACP and rACP official tokens",
  description:
    "Where Wrapped ACP (wACP) is already visible without CoinGecko approval: PancakeSwap, GeckoTerminal, BscScan, and the ANCAP official token list.",
  alternates: { canonical: "/markets" },
};

export default function MarketsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
