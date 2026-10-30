import type { Metadata } from "next";
import { Navigation } from "@/components/Navigation";
import { SiteLegalFooter } from "@/components/legal/LegalViews";
import { RacpOverview } from "@/components/RacpOverview";

export const metadata: Metadata = {
  title: "Robinhood ACP (rACP) — Official ANCAP token",
  description: "Official rACP contract on Robinhood Chain: 10,000,000 tokens, initial 1,000,000 ACP reserve, wallet import and transaction evidence. 1 ACP = 10 rACP.",
  alternates: { canonical: "/tokens/racp" },
  openGraph: { title: "Robinhood ACP · rACP", description: "An ANCAP ACP receipt on Robinhood Chain. Official contract, reserve and wallet import.", url: "https://ancap.cloud/tokens/racp", images: ["https://ancap.cloud/racp-logo.png"] },
};

export default function RacpPage() {
  return <><Navigation /><main className="container" style={{ padding: "36px 24px 64px" }}><RacpOverview /></main><SiteLegalFooter /></>;
}
