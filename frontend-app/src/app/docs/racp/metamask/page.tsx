import Link from "next/link";
import { Navigation } from "@/components/Navigation";
import { SiteLegalFooter } from "@/components/legal/LegalViews";
import {
  metamaskDappLink,
  RACP_CHAIN_ID,
  RACP_CONTRACT,
  RACP_DAPP_PATH,
  RACP_EXPLORER,
  RACP_NETWORK,
} from "@/lib/racpToken";

export const metadata = {
  title: "Add rACP in MetaMask on your phone",
  description:
    "Connect MetaMask mobile to Robinhood Chain and import the official ANCAP rACP ERC-20 contract.",
};

export default function RacpMetamaskPage() {
  const openHref = metamaskDappLink(RACP_DAPP_PATH);
  return (
    <div className="relative min-h-screen">
      <Navigation />
      <main className="container" style={{ padding: "48px 24px 72px", maxWidth: 820 }}>
        <div className="section-num">RACP · METAMASK · MOBILE</div>
        <h1 style={{ fontSize: "clamp(1.8rem, 4vw, 2.6rem)", fontWeight: 850, margin: "10px 0 14px" }}>
          rACP in MetaMask on your phone
        </h1>
        <p style={{ color: "var(--text-muted)", lineHeight: 1.7, marginBottom: 20 }}>
          Phone Safari/Chrome does not inject MetaMask. Open the page inside the MetaMask app browser,
          connect the account, approve Robinhood Chain, then import the token. ANCAP never asks for a seed phrase.
        </p>

        <section className="card" style={{ borderRadius: 8, marginBottom: 18 }}>
          <h2 style={{ marginTop: 0, fontSize: "1.15rem" }}>1. Open in MetaMask</h2>
          <ol style={{ color: "var(--text-muted)", lineHeight: 1.75, paddingLeft: 20 }}>
            <li>Install MetaMask from the App Store or Google Play.</li>
            <li>Tap the button below — it uses MetaMask&apos;s universal link.</li>
            <li>Confirm opening <code>ancap.cloud</code> in the MetaMask browser.</li>
          </ol>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 12 }}>
            <a className="btn btn-primary" href={openHref}>
              Open /tokens/racp in MetaMask
            </a>
            <Link className="btn btn-ghost" href="/tokens/racp">
              Token page
            </Link>
          </div>
        </section>

        <section className="card" style={{ borderRadius: 8, marginBottom: 18 }}>
          <h2 style={{ marginTop: 0, fontSize: "1.15rem" }}>2. Network + token</h2>
          <ol style={{ color: "var(--text-muted)", lineHeight: 1.75, paddingLeft: 20 }}>
            <li>In MetaMask, tap <strong>Add rACP to wallet</strong>.</li>
            <li>Approve account connection if prompted.</li>
            <li>Approve adding <strong>{RACP_NETWORK.chainName}</strong> (chain id {RACP_CHAIN_ID}).</li>
            <li>Approve importing token symbol <strong>rACP</strong>, 18 decimals.</li>
          </ol>
          <p className="break-all" style={{ fontFamily: "monospace", fontSize: "0.9rem", marginTop: 12 }}>
            {RACP_CONTRACT}
          </p>
          <ul style={{ color: "var(--text-muted)", lineHeight: 1.75, paddingLeft: 20 }}>
            <li>RPC: {RACP_NETWORK.rpcUrls[0]}</li>
            <li>Explorer: {RACP_EXPLORER}</li>
            <li>Native gas: ETH on Robinhood Chain (you need a small amount for airdrop/redeem txs).</li>
          </ul>
        </section>

        <section className="card" style={{ borderRadius: 8 }}>
          <h2 style={{ marginTop: 0, fontSize: "1.15rem" }}>Manual fallback</h2>
          <ol style={{ color: "var(--text-muted)", lineHeight: 1.75, paddingLeft: 20 }}>
            <li>MetaMask → Networks → Add network → Custom.</li>
            <li>Paste network name, RPC, chain id {RACP_CHAIN_ID}, symbol ETH, explorer above.</li>
            <li>Import tokens → Custom token → paste the contract address character-for-character.</li>
          </ol>
          <p style={{ color: "var(--text-muted)", lineHeight: 1.7, marginBottom: 0 }}>
            Same name/logo with a different address is not official. Compare against{" "}
            <a href="/tokenlist.json">tokenlist.json</a> and{" "}
            <a href="/racp-listings.json">racp-listings.json</a>.
          </p>
        </section>
      </main>
      <SiteLegalFooter />
    </div>
  );
}
