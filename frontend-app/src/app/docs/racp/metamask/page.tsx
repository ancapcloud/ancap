import Link from "next/link";
import { Navigation } from "@/components/Navigation";
import { SiteLegalFooter } from "@/components/legal/LegalViews";
import {
  RACP_CHAIN_ID,
  RACP_CONTRACT,
  RACP_EXPLORER,
  RACP_NETWORK,
} from "@/lib/racpToken";

export const metadata = {
  title: "Connect MetaMask from Chrome on iPhone",
  description:
    "Use Chrome on iPhone with MetaMask Connect: approve in the MetaMask app, return to Chrome, then add Robinhood Chain and rACP.",
};

export default function RacpMetamaskPage() {
  return (
    <div className="relative min-h-screen">
      <Navigation />
      <main className="container" style={{ padding: "48px 24px 72px", maxWidth: 820 }}>
        <div className="section-num">RACP · CHROME · METAMASK</div>
        <h1 style={{ fontSize: "clamp(1.8rem, 4vw, 2.6rem)", fontWeight: 850, margin: "10px 0 14px" }}>
          MetaMask from Chrome on iPhone
        </h1>
        <p style={{ color: "var(--text-muted)", lineHeight: 1.7, marginBottom: 20 }}>
          Chrome on iPhone cannot inject a wallet extension. ANCAP uses MetaMask Connect: Chrome opens the MetaMask app
          for approval, then you return to Chrome with a live session. This is not the same as browsing the site inside MetaMask.
        </p>

        <section className="card" style={{ borderRadius: 8, marginBottom: 18 }}>
          <h2 style={{ marginTop: 0, fontSize: "1.15rem" }}>Steps</h2>
          <ol style={{ color: "var(--text-muted)", lineHeight: 1.75, paddingLeft: 20 }}>
            <li>Install <strong>MetaMask</strong> from the App Store and finish wallet setup.</li>
            <li>Open <strong>Chrome</strong> on the iPhone (not Safari-only restriction — Chrome works the same pattern).</li>
            <li>
              Go to{" "}
              <Link href="/tokens/racp">ancap.cloud/tokens/racp</Link>.
            </li>
            <li>Tap <strong>Connect MetaMask from Chrome</strong> (or Add rACP to wallet).</li>
            <li>iOS switches to MetaMask — approve the connection.</li>
            <li>Return to Chrome when prompted.</li>
            <li>Approve adding <strong>{RACP_NETWORK.chainName}</strong> (id {RACP_CHAIN_ID}) and importing <strong>rACP</strong>.</li>
          </ol>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 12 }}>
            <Link className="btn btn-primary" href="/tokens/racp">
              Open rACP page
            </Link>
            <a
              className="btn btn-ghost"
              href="https://apps.apple.com/app/metamask-blockchain-wallet/id1438144202"
              target="_blank"
              rel="noopener noreferrer"
            >
              MetaMask on App Store
            </a>
          </div>
        </section>

        <section className="card" style={{ borderRadius: 8, marginBottom: 18 }}>
          <h2 style={{ marginTop: 0, fontSize: "1.15rem" }}>Official token</h2>
          <p className="break-all" style={{ fontFamily: "monospace", fontSize: "0.9rem" }}>
            {RACP_CONTRACT}
          </p>
          <ul style={{ color: "var(--text-muted)", lineHeight: 1.75, paddingLeft: 20 }}>
            <li>Symbol: rACP · decimals 18</li>
            <li>RPC: {RACP_NETWORK.rpcUrls[0]}</li>
            <li>Explorer: {RACP_EXPLORER}</li>
          </ul>
        </section>

        <section className="card" style={{ borderRadius: 8 }}>
          <h2 style={{ marginTop: 0, fontSize: "1.15rem" }}>If connect fails</h2>
          <ul style={{ color: "var(--text-muted)", lineHeight: 1.75, paddingLeft: 20, marginBottom: 0 }}>
            <li>MetaMask must be installed and unlocked once.</li>
            <li>Allow Chrome → MetaMask handoff when iOS asks.</li>
            <li>After approving in MetaMask, manually switch back to Chrome if iOS did not return.</li>
            <li>ANCAP never asks for a seed phrase.</li>
          </ul>
        </section>
      </main>
      <SiteLegalFooter />
    </div>
  );
}