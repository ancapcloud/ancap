import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Markets — rACP on Robinhood Chain",
  description:
    "Official rACP on Robinhood Chain: contract, reserve evidence, redemption availability and legacy wACP support. No market price is promised.",
  alternates: { canonical: "/markets" },
};

export default function MarketsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
