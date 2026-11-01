import { RacpOverview } from "@/components/RacpOverview";
import Link from "next/link";
import { Navigation } from "@/components/Navigation";
import { getServerApiBase, serverApiFetch } from "@/lib/serverApi";
import { TokenomicsSnapshotSection } from "./TokenomicsSnapshotSection";

export const dynamic = "force-dynamic";
export const revalidate = 0;

const API_BASE = getServerApiBase();

async function loadSupply() {
  const ctrl = AbortSignal.timeout(8_000);
  try {
    const [statusRes, explorerRes, tokenomicsRes] = await Promise.all([
      serverApiFetch(`${API_BASE}/acp/explorer/status`, { signal: ctrl, cache: "no-store" }),
      serverApiFetch(`${API_BASE}/wacp/status`, { signal: ctrl, cache: "no-store" }),
      serverApiFetch(`${API_BASE}/acp/explorer/tokenomics/snapshot`, { signal: ctrl, cache: "no-store" }),
    ]);
    const explorer = statusRes.ok ? await statusRes.json() : null;
    const wacp = explorerRes.ok ? await explorerRes.json() : null;
    const tokenomics = tokenomicsRes.ok ? await tokenomicsRes.json() : null;
    return { explorer, wacp, tokenomics };
  } catch {
    return { explorer: null, wacp: null, tokenomics: null };
  }
}

export const metadata = {
  title: "ACP Supply | ANCAP transparency",
  description: "Public ACP chain height snapshot and official 210M tokenomics distribution.",
};

export default async function AcpSupplyPage() {
  const { explorer, tokenomics } = await loadSupply();

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <Navigation />
      <main className="mx-auto max-w-5xl px-4 py-10">
        <h1 className="text-3xl font-semibold">ACP supply snapshot</h1>
        <p className="mt-3 text-sm leading-7 text-white/68">
          Public transparency for native ACP chain activity, official genesis tokenomics (210M), and rACP on Robinhood Chain.
        </p>
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
            <h2 className="font-semibold">Native ACP chain</h2>
            {explorer ? (
              <div className="mt-3 space-y-1 text-sm text-white/70">
                <div>Chain ID: {explorer.chain_id}</div>
                <div>Block height: {explorer.block_height}</div>
                <div className="break-all">Best hash: {explorer.best_block_hash}</div>
              </div>
            ) : (
              <p className="mt-3 text-sm text-amber-200">Explorer RPC unavailable</p>
            )}
          </section>
          <RacpOverview compact />
          <TokenomicsSnapshotSection snapshot={tokenomics} />
        </div>
        <div className="mt-8 flex flex-wrap gap-4 text-sm">
          <Link href="/wallet/acp" className="text-emerald-300">
            ACP wallet
          </Link>
          <Link href="/reserves" className="text-emerald-300">
            Reserves dashboard
          </Link>
          <Link href="/explorer" className="text-emerald-300">
            ACP explorer
          </Link>
          <Link href="/status" className="text-emerald-300">
            Platform status
          </Link>
        </div>
      </main>
    </div>
  );
}
