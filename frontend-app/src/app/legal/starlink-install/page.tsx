import { StarlinkInstallLegalView } from "@/components/legal/LegalViews";

export const metadata = {
  title: "Starlink installation — legal notice | ANCAP",
  description:
    "ANCAP Starlink installation desk: ACP accounting and rACP payment and partner handoff. Not an official Starlink reseller, not Telekom, not a Jobcenter or AVGS funding guarantee.",
};

export default function LegalStarlinkInstallPage() {
  return <StarlinkInstallLegalView />;
}
