import Link from "next/link";
import { Navigation } from "@/components/Navigation";
import { CardsWaitlistForm } from "@/components/CardsWaitlistForm";

export const metadata = {
  title: "Physical card / Apple Pay waitlist | ANCAP",
  description:
    "Future ACP spend card and Apple Pay interest waitlist. ANCAP does not issue payment cards; KYC may use WebID or an equivalent partner.",
};

export default function CardsWaitlistPage() {
  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <Navigation />
      <main className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="text-3xl font-semibold">Physical card / Apple Pay</h1>
        <p className="mt-3 text-sm leading-7 text-white/68">
          Interest list for a future ACP spend card (plastic and/or Apple Pay) issued by a{" "}
          <strong>licensed partner</strong>. ANCAP is not a card issuer and is not a VASP.
        </p>
        <ul className="mt-6 space-y-3 text-sm leading-7 text-white/60">
          <li>
            <strong className="text-white/85">KYC/KYB:</strong> may use{" "}
            <a
              href="https://webid-solutions.com/en/"
              className="underline"
              target="_blank"
              rel="noreferrer"
            >
              WebID
            </a>{" "}
            (or equivalent) when live — identity checks only.
          </li>
          <li>
            <strong className="text-white/85">Cards / Apple Pay:</strong> require a separate
            licensed BaaS or EMI plus card-network tokenization. Not available yet.
          </li>
          <li>
            <strong className="text-white/85">Today:</strong> use{" "}
            <Link href="/buy-acp" className="underline">
              /buy-acp
            </Link>{" "}
            (bridge, credits, MoonPay Commerce) to get ACP.
          </li>
        </ul>

        <section id="waitlist" className="mt-10">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-emerald-300/90">
            Join the waitlist
          </h2>
          <CardsWaitlistForm />
        </section>

        <p className="mt-10 text-xs leading-6 text-white/45">
          Operator path:{" "}
          <Link href="/compliance" className="underline">
            /compliance
          </Link>
          . Internal doc:{" "}
          <code className="text-white/55">docs/WEBID_KYC_AND_CARD_ISSUING_PATH.md</code>.
        </p>
      </main>
    </div>
  );
}
