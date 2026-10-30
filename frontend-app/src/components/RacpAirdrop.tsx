"use client";
import { useEffect, useState } from "react";
import { useAuth } from "./AuthProvider";
import { useLanguage } from "./LanguageProvider";
import { TurnstileWidget } from "./TurnstileWidget";
import { TURNSTILE_SITE_KEY } from "@/lib/turnstile";
import { apiFetch } from "@/lib/api";
import { getPreferredEvmProvider } from "@/lib/evmProvider";
import { ensureRobinhoodChain, metamaskDappLink, openRacpInMetaMaskApp, RACP_EXPLORER, isLikelyMobileBrowser } from "@/lib/racpToken";
import { claimTransaction, RACP_AIRDROP, type AirdropVoucher } from "@/lib/racpAirdrop";
import { racpAirdropCopy } from "@/locales/racpAirdrop";

type Status = { enabled: boolean; distributed: string; remaining_claims: number; airdrop_contract: string | null };
export function RacpAirdrop() {
  const { lang } = useLanguage(); const c = racpAirdropCopy[lang];
  const { user, isAuthenticated, loginWithWallet, linkWallet } = useAuth();
  const [status, setStatus] = useState<Status | null>(null);
  const [address, setAddress] = useState(""); const [busy, setBusy] = useState(false);
  const [captcha, setCaptcha] = useState(""); const [reset, setReset] = useState(0);
  const [message, setMessage] = useState(""); const [txHash, setTxHash] = useState("");
  const ready = isAuthenticated && !!address && user?.wallet_address?.toLowerCase() === address.toLowerCase();
  async function refresh() {
    try { setStatus(await apiFetch("/racp/airdrop/status")); } catch { setStatus(null); }
  }
  useEffect(() => { void refresh(); }, []);
  async function perform() {
    setBusy(true); setMessage("");
    try {
      if (TURNSTILE_SITE_KEY && !captcha) throw new Error(c.verify);
      const provider = getPreferredEvmProvider();
      if (!provider) {
        if (isLikelyMobileBrowser() && openRacpInMetaMaskApp("/tokens/racp/airdrop")) {
          setMessage("Opening MetaMask… Continue the claim inside the MetaMask browser.");
          return;
        }
        throw new Error(c.error);
      }
      await ensureRobinhoodChain(provider);
      const accounts = await provider.request({ method: "eth_requestAccounts" });
      const account = Array.isArray(accounts) && typeof accounts[0] === "string" ? accounts[0] : "";
      if (!account) throw new Error(c.error);
      if (!ready) {
        if (isAuthenticated) await linkWallet(account, 4663, captcha); else await loginWithWallet(account, 4663, captcha);
        setAddress(account); await refresh();
      } else {
        if (account.toLowerCase() !== address.toLowerCase() || status?.airdrop_contract?.toLowerCase() !== RACP_AIRDROP.toLowerCase()) throw new Error(c.error);
        const voucher = await apiFetch("/racp/airdrop/voucher", { method: "POST", body: JSON.stringify({ address: account, turnstile_token: captcha }) }) as AirdropVoucher;
        const tx = await provider.request({ method: "eth_sendTransaction", params: [claimTransaction(voucher, account)] });
        if (typeof tx !== "string" || !/^0x[0-9a-f]{64}$/i.test(tx)) throw new Error(c.error);
        setTxHash(tx); setMessage(c.pending);
        for (let i = 0; i < 15; i++) {
          const receipt = await provider.request({ method: "eth_getTransactionReceipt", params: [tx] }) as {status?: string} | null;
          if (receipt) { if (receipt.status !== "0x1") throw new Error(c.error); setMessage(c.success); await refresh(); break; }
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
      }
    } catch (e) { setMessage(e instanceof Error ? e.message : c.error); }
    finally { setBusy(false); setCaptcha(""); setReset(n => n + 1); }
  }
  return <section className="card" style={{ padding: "clamp(20px, 4vw, 36px)", margin: "24px 0" }}>
    <p className="section-num">rACP · AIRDROP · ROBINHOOD CHAIN</p><h1 style={{ fontSize: "clamp(2rem,5vw,3rem)", margin: "16px 0" }}>{c.title}</h1>
    <p style={{ lineHeight: 1.8 }}>{c.lead}</p><p style={{ fontWeight: 700, lineHeight: 1.8 }}>{c.rules}</p>
    <div className="responsive-grid responsive-grid-2" style={{ gap: 20, margin: "24px 0" }}>
      <div>{c.distributed}<strong style={{ display: "block", fontSize: "1.7rem" }}>{status ? new Intl.NumberFormat(lang).format(Number(status.distributed)) : "—"}</strong></div>
      <div>{c.remaining}<strong style={{ display: "block", fontSize: "1.7rem" }}>{status ? new Intl.NumberFormat(lang).format(status.remaining_claims) : "—"}</strong></div>
    </div>
    <p style={{ color: "var(--text-muted)", lineHeight: 1.8 }}>{c.fees}</p><p style={{ color: "var(--text-muted)", lineHeight: 1.8 }}>{c.identity}</p>
    {ready && <p style={{ overflowWrap: "anywhere" }}>{c.wallet}: <code>{address}</code></p>}
    <TurnstileWidget key={ready ? "claim" : "login"} siteKey={TURNSTILE_SITE_KEY} action={ready ? "racp_airdrop" : "login"} onTokenChange={setCaptcha} resetSignal={reset} />
    <div className="action-cluster" style={{ marginTop: 20 }}>
      <button className="btn btn-primary" type="button" onClick={() => void perform()} disabled={busy || !status?.enabled || !!txHash || (!!TURNSTILE_SITE_KEY && !captcha)}>{busy ? c.busy : ready ? c.claim : c.connect}</button>
      <a className="btn btn-primary" href={metamaskDappLink("/tokens/racp/airdrop")} onClick={(event) => { event.preventDefault(); openRacpInMetaMaskApp("/tokens/racp/airdrop"); }}>Open in MetaMask</a>
      <button className="btn btn-ghost" type="button" onClick={() => void refresh()}>{c.refresh}</button>
      <a className="btn btn-ghost" href={`${RACP_EXPLORER}/address/${RACP_AIRDROP}`} target="_blank" rel="noopener noreferrer">Airdrop ↗</a>
      <a className="btn btn-ghost" href="/docs/racp/metamask">Phone guide</a>
    </div>
    {!status?.enabled && <p>{c.paused}</p>}<p role="status" aria-live="polite" style={{ overflowWrap: "anywhere" }}>{message}</p>
    {txHash && <a href={`${RACP_EXPLORER}/tx/${txHash}`} target="_blank" rel="noopener noreferrer">{txHash}</a>}
  </section>;
}
