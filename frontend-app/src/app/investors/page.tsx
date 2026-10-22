import type { Metadata } from "next";
import { InvestorOverview } from "./InvestorOverview";
export const metadata: Metadata = {
  title: "Invest in ANCAP — product, business model & milestones",
  description: "ANCAP's investment thesis: customers, AI workflow revenue model, wallet and project roadmap, product evidence and milestone-based use of funds.",
};
export default function InvestorsPage() { return <InvestorOverview />; }
