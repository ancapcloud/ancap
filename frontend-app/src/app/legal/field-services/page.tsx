import { FieldServicesLegalView } from "@/components/legal/LegalViews";

export const metadata = {
  title: "Field services â€” legal notice | ANCAP",
  description:
    "ANCAP field services hub (Starlink, IT, cameras, solar): ACP accounting and rACP payment and partner handoff. Not an equipment reseller, not a Jobcenter or AVGS funding guarantee.",
};

export default function LegalFieldServicesPage() {
  return <FieldServicesLegalView />;
}
