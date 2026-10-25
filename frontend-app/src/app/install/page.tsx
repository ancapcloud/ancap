import type { Metadata } from "next";
import { Navigation } from "@/components/Navigation";
import { WorkflowFooter, presentationStyles as s } from "@/components/WorkflowPresentation";
import { WebInstallGuide } from "@/components/WebInstallGuide";

export const metadata: Metadata = {
  title: "ANCAP installieren · iPhone & Android",
  description: "ANCAP über Safari auf dem iPhone oder Chrome auf Android zum Home-Bildschirm hinzufügen. Schritt-für-Schritt-Anleitung ohne App Store.",
};

export default function InstallPage() {
  return <div className={s.shell} style={{ position: "relative", zIndex: 1 }}>
    <Navigation />
    <main className={s.main}><WebInstallGuide standalone /></main>
    <WorkflowFooter />
  </div>;
}
