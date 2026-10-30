import type { Metadata } from "next";
import { Navigation } from "@/components/Navigation";
import { SiteLegalFooter } from "@/components/legal/LegalViews";
import { RacpRedeem } from "@/components/RacpRedeem";

export const metadata: Metadata = {
  title: "Redeem rACP for ACP",
  description:
    "Burn rACP on Robinhood Chain to request ACP from the exclusive ANCAP reserve. 1 ACP = 10 rACP. ETH network fees apply.",
  alternates: { canonical: "/tokens/racp/redeem" },
};

export default function RacpRedeemPage() {
  return (
    <>
      <Navigation />
      <main className="container" style={{ padding: "36px 24px 64px" }}>
        <RacpRedeem />
      </main>
      <SiteLegalFooter />
    </>
  );
}
