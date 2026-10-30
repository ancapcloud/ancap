import type { Metadata } from "next";
export const metadata: Metadata = {
  title: "Get ACP via rACP | ANCAP",
  description: "ACP service balances with rACP on Robinhood Chain. Official token, redemption availability and legacy wACP support.",
  alternates: { canonical: "/buy-acp" },
};
export default function Layout({ children }: { children: React.ReactNode }) { return children; }
