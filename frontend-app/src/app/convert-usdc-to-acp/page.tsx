import Link from "next/link";
import { Navigation } from "@/components/Navigation";

export const metadata = {
  title: "Convert USDC to ACP | ANCAP",
  description: "Bridge and ramp paths from USDC to ACP credits.",
};

export default function ConvertUsdcToAcpPage() {
  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <Navigation />
      <main className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="text-3xl font-semibold">Convert USDC to ACP</h1>
        <p className="mt-3 text-sm leading-7 text-white/68">
          ANCAP uses ACP internally and rACP on Robinhood Chain externally. Direct USDCâ†’ACP partner ramps are waitlisted while compliance review completes.
        </p>
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <Link href="/tokens/racp" className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 hover:border-white/20">
            <div className="font-semibold">rACP on Robinhood Chain</div>
            <p className="mt-2 text-sm text-white/60">Official token, reserve evidence and redemption availability.</p>
          </Link>
          <Link href="/pay-with-stablecoin" className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 hover:border-white/20">
            <div className="font-semibold">Partner ramp waitlist</div>
            <p className="mt-2 text-sm text-white/60">USDC/USDT top-up without manual bridge steps.</p>
          </Link>
          <Link href="/buy-acp" className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 hover:border-white/20">
            <div className="font-semibold">Card checkout</div>
            <p className="mt-2 text-sm text-white/60">Stripe credits top-up for workflows and Pay.</p>
          </Link>
          <Link href="/compliance" className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 hover:border-white/20">
            <div className="font-semibold">Compliance matrix</div>
            <p className="mt-2 text-sm text-white/60">Regional availability and risk disclosures.</p>
          </Link>
        </div>
      </main>
    </div>
  );
}
