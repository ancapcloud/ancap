"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Navigation } from "@/components/Navigation";
import { WacpPublicActions } from "@/components/WacpPublicActions";
import { RacpOverview } from "@/components/RacpOverview";
import { SiteLegalFooter } from "@/components/legal/LegalViews";
import {
  WACP_BSC_CONTRACT,
  WACP_SYMBOL,
  WACP_USDT_BSC,
  WACP_V2_POOL,
  WACP_V3_POOL,
  getWacpLogoUrl,
} from "@/lib/wacpToken";

type Placement = {
  id: string;
  name: string;
  status: string;
  fee: string;
  url: string;
  how: string;
};

type ListingsPayload = {
  official_asset?: { address?: string; pool_wacp_usdt_v2?: string };
  placements?: Placement[];
};

const FALLBACK: Placement[] = [
  {
    id: "pancakeswap_v3",
    name: "PancakeSwap V3 (bootstrap)",
    status: "live",
    fee: "free",
    url: `https://pancakeswap.finance/liquidity/pool/bsc/${WACP_V3_POOL}`,
    how: "Shallow concentrated wACP/USDT 0.25% — discovery only; checkout oracle stays on V2",
  },
  {
    id: "dextools",
    name: "DexTools",
    status: "live",
    fee: "free_index_paid_profile",
    url: `https://www.dextools.io/app/en/bnb/pair-explorer/${WACP_V2_POOL.toLowerCase()}`,
    how: "Auto-indexed — use CA in Coin/DexTools promo forms",
  },
  {
    id: "pancakeswap",
    name: "PancakeSwap V2 (reference / oracle)",
    status: "live",
    fee: "free",
    url: `https://pancakeswap.finance/swap?inputCurrency=${WACP_USDT_BSC}&outputCurrency=${WACP_BSC_CONTRACT}`,
    how: "Thin canonical micro-market; platform USD oracle reference",
  },
  {
    id: "geckoterminal",
    name: "GeckoTerminal",
    status: "live",
    fee: "free",
    url: `https://www.geckoterminal.com/bsc/pools/${WACP_V2_POOL.toLowerCase()}`,
    how: "CoinGecko DEX terminal (V2 reference)",
  },
  {
    id: "geckoterminal_v3",
    name: "GeckoTerminal V3",
    status: "live",
    fee: "free",
    url: `https://www.geckoterminal.com/bsc/pools/${WACP_V3_POOL}`,
    how: "V3 bootstrap pool chart",
  },
  {
    id: "bscscan",
    name: "BscScan",
    status: "live",
    fee: "free",
    url: `https://bscscan.com/token/${WACP_BSC_CONTRACT}`,
    how: "Explorer token page",
  },
  {
    id: "goplus",
    name: "GoPlus Security",
    status: "live",
    fee: "free",
    url: `https://gopluslabs.io/token-security/56/${WACP_BSC_CONTRACT}`,
    how: "Security index; is_in_dex=true",
  },
  {
    id: "ancap_tokenlist",
    name: "ANCAP token list",
    status: "live",
    fee: "free",
    url: "/tokenlist.json",
    how: "Self-hosted Uniswap token list",
  },
];

function badgeFor(status: string): string {
  if (status === "live") return "badge badge-success";
  if (status.startsWith("pending") || status.includes("pack")) return "badge";
  return "badge";
}

export default function MarketsPage() {
  const [placements, setPlacements] = useState<Placement[]>(FALLBACK);

  useEffect(() => {
    void (async () => {
      try {
        const res = await fetch("/listings.json", { cache: "no-store" });
        if (!res.ok) return;
        const data = (await res.json()) as ListingsPayload;
        if (Array.isArray(data.placements) && data.placements.length) {
          setPlacements(data.placements);
        }
      } catch {
        /* keep fallback */
      }
    })();
  }, []);

  const live = placements.filter((p) => p.status === "live");
  const later = placements.filter((p) => p.status !== "live");

  return (
    <div className="relative min-h-screen">
      <Navigation />
      <main className="container" style={{ padding: "48px 24px 72px" }}>
        <RacpOverview compact />
        <div className="section-num">PUBLIC MARKETS</div>
        <h1
          style={{
            fontSize: "clamp(1.9rem, 4vw, 2.9rem)",
            fontWeight: 850,
            margin: "10px 0 14px",
            maxWidth: 900,
          }}
        >
          Place wACP everywhere that does not need a gatekeeper
        </h1>
        <p style={{ color: "var(--text-muted)", lineHeight: 1.7, maxWidth: 820, marginBottom: 12 }}>
          Full internet spam is impossible: CoinGecko, CMC, DexScreener and CEX lists need liquidity or paid
          profiles. Below is every free surface we can verify or self-host for{" "}
          <strong>{WACP_SYMBOL}</strong>.
        </p>
        <p style={{ color: "var(--text-muted)", lineHeight: 1.7, maxWidth: 820, marginBottom: 12 }}>
          Three different numbers people confuse: <strong>wACP DEX spot</strong> (GeckoTerminal / PancakeSwap),
          the <strong>USDT→ACP desk quote</strong> inside the product, and <strong>promotional credit labels</strong>{" "}
          (welcome grant / faucet — not a retail sale price). Dust LP depth is not an ACP unit price.
        </p>
        <p
          style={{
            color: "var(--accent-strong)",
            lineHeight: 1.65,
            maxWidth: 820,
            marginBottom: 28,
            fontSize: "0.95rem",
          }}
        >
          Promo forms that require CoinGecko <em>or</em> DexTools: paste{" "}
          <code style={{ wordBreak: "break-all" }}>{WACP_BSC_CONTRACT}</code> — search{" "}
          <strong>wACP</strong>, never “ANCAP” / “ACP”.
        </p>

        <div
          className="card"
          style={{
            marginBottom: 28,
            borderRadius: 8,
            background: "rgba(18, 26, 45, 0.82)",
          }}
        >
          <div style={{ display: "flex", flexWrap: "wrap", gap: 18, alignItems: "center" }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={getWacpLogoUrl()}
              alt="wACP"
              width={56}
              height={56}
              style={{ borderRadius: 12, background: "#000" }}
            />
            <div style={{ flex: "1 1 240px" }}>
              <div style={{ fontWeight: 800, fontSize: "1.15rem" }}>Wrapped ACP · {WACP_SYMBOL}</div>
              <div className="break-all" style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: 6 }}>
                {WACP_BSC_CONTRACT}
              </div>
            </div>
            <WacpPublicActions layout="home" />
          </div>
          <div style={{ marginTop: 16, display: "flex", flexWrap: "wrap", gap: 10 }}>
            <a href="/listings.json" className="btn btn-ghost">
              listings.json
            </a>
            <a href="/tokenlist.json" className="btn btn-ghost">
              tokenlist.json
            </a>
            <Link href="/docs/wacp" className="btn btn-ghost">
              Docs
            </Link>
            <Link href="/docs/wacp/metamask" className="btn btn-ghost">
              MetaMask guide
            </Link>
            <Link href="/buy-acp" className="btn btn-ghost">
              Buy → spend ACP
            </Link>
            <Link href="/ai/workflows" className="btn btn-ghost">
              Workflows
            </Link>
            <Link href="/developers" className="btn btn-ghost">
              Paid API
            </Link>
            <Link href="/marketplace" className="btn btn-ghost">
              Marketplace
            </Link>
          </div>
        </div>

        <h2 style={{ fontSize: "1.25rem", fontWeight: 800, marginBottom: 14 }}>
          Live ({live.length})
        </h2>
        <div className="responsive-grid responsive-grid-2" style={{ gap: 14, marginBottom: 36 }}>
          {live.map((item) => (
            <div key={item.id} className="card" style={{ borderRadius: 8, minWidth: 0 }}>
              <div className={badgeFor(item.status)} style={{ marginBottom: 12 }}>
                {item.status} · {item.fee}
              </div>
              <h3 style={{ margin: "0 0 10px", fontSize: "1.05rem" }}>{item.name}</h3>
              <p style={{ margin: "0 0 14px", color: "var(--text-muted)", lineHeight: 1.65 }}>{item.how}</p>
              {item.url.startsWith("http") ? (
                <a href={item.url} className="btn btn-ghost" target="_blank" rel="noopener noreferrer">
                  Open
                </a>
              ) : (
                <Link href={item.url} className="btn btn-ghost">
                  Open
                </Link>
              )}
            </div>
          ))}
        </div>

        <h2 style={{ fontSize: "1.25rem", fontWeight: 800, marginBottom: 14 }}>
          Pending / blocked ({later.length})
        </h2>
        <div className="responsive-grid responsive-grid-2" style={{ gap: 14, marginBottom: 36 }}>
          {later.map((item) => (
            <div key={item.id} className="card" style={{ borderRadius: 8, minWidth: 0 }}>
              <div className={badgeFor(item.status)} style={{ marginBottom: 12 }}>
                {item.status} · {item.fee}
              </div>
              <h3 style={{ margin: "0 0 10px", fontSize: "1.05rem" }}>{item.name}</h3>
              <p style={{ margin: "0 0 14px", color: "var(--text-muted)", lineHeight: 1.65 }}>{item.how}</p>
              <a href={item.url} className="btn btn-ghost" target="_blank" rel="noopener noreferrer">
                Details
              </a>
            </div>
          ))}
        </div>

        <div className="card" style={{ borderRadius: 8 }}>
          <h2 style={{ marginTop: 0, fontSize: "1.15rem" }}>What unlocks the rest</h2>
          <ol style={{ color: "var(--text-muted)", lineHeight: 1.75, paddingLeft: 20, margin: 0 }}>
            <li>Seed real PancakeSwap wACP/USDT liquidity (not dust).</li>
            <li>Make a few round-trip swaps → DexScreener usually appears.</li>
            <li>Submit CoinGecko Partners as <strong>wACP</strong> (playbook in repo).</li>
            <li>Optional paid DexTools/DexScreener profile updates for logo/socials.</li>
          </ol>
        </div>
      </main>
      <SiteLegalFooter />
    </div>
  );
}
