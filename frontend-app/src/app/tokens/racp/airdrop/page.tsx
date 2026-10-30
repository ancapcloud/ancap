import type { Metadata } from "next";
import { Navigation } from "@/components/Navigation";
import { SiteLegalFooter } from "@/components/legal/LegalViews";
import { RacpAirdrop } from "@/components/RacpAirdrop";
export const metadata: Metadata = { title: "rACP Airdrop — Get 500 rACP", description: "Opt-in ANCAP giveaway: 1,000,000 rACP campaign, 500 per verified wallet and account. Robinhood Chain ETH transaction fees apply.", alternates: { canonical: "/tokens/racp/airdrop" } };
export default function AirdropPage() { return <><Navigation /><main className="container" style={{ padding: "36px 24px 64px" }}><RacpAirdrop /></main><SiteLegalFooter /></>; }
