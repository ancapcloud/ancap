import { Suspense } from "react";
import type { Metadata } from "next";
import { HomePage } from "./HomePage";

export const metadata: Metadata = {
  title: "ANCAP — AI Workflow Commerce",
  description:
    "Turn a task into a finished AI result. Choose a workflow, review the quote and receive a structured result with an execution receipt.",
};

export default function Page() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[var(--bg)]" aria-hidden />}>
      <HomePage />
    </Suspense>
  );
}
