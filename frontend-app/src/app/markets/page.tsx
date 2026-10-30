import { Navigation } from "@/components/Navigation";
import { SiteLegalFooter } from "@/components/legal/LegalViews";
import { RacpEntry } from "@/components/RacpEntry";

export default function Page() {
  return <><Navigation /><main className="container" style={{ padding: "36px 24px 64px" }}><RacpEntry /></main><SiteLegalFooter /></>;
}
