"use client";

import { useEffect, useState } from "react";
import { useLanguage } from "./LanguageProvider";
import { apiFetch } from "@/lib/api";
import { resolveEvmProvider } from "@/lib/metamaskConnect";
import {
  ACP_ADDRESS_RE,
  ensureRobinhoodChain,
  parseRacpHumanToWei,
  redeemTransaction,
  RACP_CHAIN_HEX,
  RACP_EXPLORER,
  RACP_RESERVE,
} from "@/lib/racpToken";
import { racpRedeemCopy } from "@/locales/racpRedeem";

type ServiceStatus = {
  enabled: boolean;
  paused: boolean;
  dry_run: boolean;
  reserve_balance_acp?: string | null;
  open_liability_count?: number;
  completed_count?: number;
};

type RedemptionRow = {
  status: string;
  acp_tx_hash?: string | null;
  amount_acp?: string;
};

export function RacpRedeem() {
  const { lang } = useLanguage();
  const c = racpRedeemCopy[lang];
  const [service, setService] = useState<ServiceStatus | null>(null);
  const [amount, setAmount] = useState("10");
  const [acpAddress, setAcpAddress] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [txHash, setTxHash] = useState("");
  const [row, setRow] = useState<RedemptionRow | null>(null);

  async function refreshService() {
    try {
      setService(await apiFetch("/racp/redeem/status"));
    } catch {
      setService(null);
    }
  }

  useEffect(() => {
    void refreshService();
  }, []);

  async function pollByTx(hash: string) {
    for (let i = 0; i < 40; i++) {
      try {
        const found = (await apiFetch(`/racp/redeem/by-tx/${hash}`)) as RedemptionRow;
        setRow(found);
        if (found.status === "COMPLETED") {
          setMessage(c.success);
          await refreshService();
          return;
        }
        if (found.status === "ACP_PAYOUT_SENT" || found.status === "BURN_CONFIRMED") {
          setMessage(c.payout);
        }
      } catch {
        /* not indexed yet */
      }
      await new Promise((r) => setTimeout(r, 3000));
    }
  }

  async function perform() {
    setBusy(true);
    setMessage("");
    setRow(null);
    try {
      if (!service?.enabled) throw new Error(c.disabled);
      if (!ACP_ADDRESS_RE.test(acpAddress.trim())) throw new Error(c.error);
      const wei = parseRacpHumanToWei(amount);
      const provider = await resolveEvmProvider([RACP_CHAIN_HEX]);
      await ensureRobinhoodChain(provider);
      const accounts = await provider.request({ method: "eth_requestAccounts" });
      const account = Array.isArray(accounts) && typeof accounts[0] === "string" ? accounts[0] : "";
      if (!account) throw new Error(c.error);
      const tx = redeemTransaction(account, wei, acpAddress.trim());
      const hash = await provider.request({ method: "eth_sendTransaction", params: [tx] });
      if (typeof hash !== "string" || !/^0x[0-9a-f]{64}$/i.test(hash)) throw new Error(c.error);
      setTxHash(hash);
      setMessage(c.pending);
      for (let i = 0; i < 20; i++) {
        const receipt = (await provider.request({
          method: "eth_getTransactionReceipt",
          params: [hash],
        })) as { status?: string } | null;
        if (receipt) {
          if (receipt.status !== "0x1") throw new Error(c.error);
          setMessage(c.payout);
          break;
        }
        await new Promise((r) => setTimeout(r, 2000));
      }
      await pollByTx(hash);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : c.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card" style={{ padding: "clamp(20px, 4vw, 36px)", margin: "24px 0" }}>
      <p className="section-num">rACP · REDEEM · ROBINHOOD CHAIN</p>
      <h1 style={{ fontSize: "clamp(2rem,5vw,3rem)", margin: "16px 0" }}>{c.title}</h1>
      <p style={{ lineHeight: 1.8 }}>{c.lead}</p>
      <p style={{ fontWeight: 700, lineHeight: 1.8 }}>{c.ratio}</p>
      <p style={{ color: "var(--text-muted)", lineHeight: 1.8 }}>{c.fees}</p>

      <dl className="responsive-grid responsive-grid-3" style={{ gap: 20, margin: "24px 0" }}>
        <div>
          <dt style={{ color: "var(--text-muted)", fontSize: ".85rem" }}>{c.status}</dt>
          <dd style={{ margin: "8px 0 0", fontWeight: 750 }}>
            {service?.enabled ? (service.paused ? "paused" : "enabled") : "disabled"}
            {service?.dry_run ? " · dry-run" : ""}
          </dd>
        </div>
        <div>
          <dt style={{ color: "var(--text-muted)", fontSize: ".85rem" }}>{c.reserve}</dt>
          <dd style={{ margin: "8px 0 0", fontWeight: 750 }}>
            {service?.reserve_balance_acp ?? "—"}
          </dd>
        </div>
        <div>
          <dt style={{ color: "var(--text-muted)", fontSize: ".85rem" }}>Completed</dt>
          <dd style={{ margin: "8px 0 0", fontWeight: 750 }}>{service?.completed_count ?? "—"}</dd>
        </div>
      </dl>

      <label style={{ display: "block", marginBottom: 12 }}>
        <span style={{ fontSize: ".85rem", color: "var(--text-muted)" }}>{c.amount}</span>
        <input
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          inputMode="decimal"
          style={{ display: "block", width: "100%", marginTop: 6, padding: 12, borderRadius: 8 }}
        />
      </label>
      <label style={{ display: "block", marginBottom: 12 }}>
        <span style={{ fontSize: ".85rem", color: "var(--text-muted)" }}>{c.acpAddress}</span>
        <input
          value={acpAddress}
          onChange={(e) => setAcpAddress(e.target.value)}
          placeholder="acp1…"
          style={{ display: "block", width: "100%", marginTop: 6, padding: 12, borderRadius: 8 }}
        />
      </label>

      <div className="action-cluster" style={{ marginTop: 20 }}>
        <button
          className="btn btn-primary"
          type="button"
          disabled={busy || !service?.enabled || !!txHash}
          onClick={() => void perform()}
        >
          {busy ? c.busy : c.redeem}
        </button>
        <button className="btn btn-ghost" type="button" onClick={() => void refreshService()}>
          {c.refresh}
        </button>
        <a className="btn btn-ghost" href={`/api/v1/acp/address/${RACP_RESERVE}/balance`} target="_blank" rel="noopener noreferrer">
          Reserve ↗
        </a>
      </div>

      {!service?.enabled && <p style={{ marginTop: 12 }}>{c.disabled}</p>}
      <p role="status" aria-live="polite" style={{ overflowWrap: "anywhere", marginTop: 12 }}>
        {message}
        {row?.status ? ` · ${row.status}` : ""}
        {row?.acp_tx_hash ? ` · ACP ${row.acp_tx_hash}` : ""}
      </p>
      {txHash && (
        <a href={`${RACP_EXPLORER}/tx/${txHash}`} target="_blank" rel="noopener noreferrer">
          {txHash}
        </a>
      )}
      <p style={{ overflowWrap: "anywhere", fontSize: ".85rem", marginTop: 20, color: "var(--text-muted)" }}>
        Reserve: <code>{RACP_RESERVE}</code>
      </p>
    </section>
  );
}
