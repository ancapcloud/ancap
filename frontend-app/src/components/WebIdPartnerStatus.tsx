"use client";

import { useEffect, useState } from "react";
import { getApiUrl } from "@/lib/api";

type WebIdStatus = {
  configured: boolean;
  enabled: boolean;
  sessions_ready?: boolean;
  issues_cards: boolean;
  apple_pay_ready: boolean;
  partner_url?: string;
  product_hint?: string;
  notes?: string[];
};

export function WebIdPartnerStatus() {
  const [status, setStatus] = useState<WebIdStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${getApiUrl()}/commerce/webid/status`, {
          headers: { "X-Requested-With": "XMLHttpRequest" },
          credentials: "include",
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(typeof body?.detail === "string" ? body.detail : `Status ${res.status}`);
        }
        if (!cancelled) setStatus(body as WebIdStatus);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Could not load WebID status");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return <p className="mt-4 text-xs text-amber-200/80">{error}</p>;
  }
  if (!status) {
    return <p className="mt-4 text-xs text-white/40">Loading WebID partner status…</p>;
  }

  const sessions = Boolean(status.sessions_ready);
  const label = sessions
    ? "Sandbox session path ready (credentials present)"
    : status.enabled
      ? "Enabled but incomplete credentials — fail-closed"
      : "Partner slot reserved — IDV off until commercial WebID account";

  return (
    <div className="mt-6 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm leading-6 text-white/65">
      <p>
        <strong className="text-white/85">WebID status:</strong> {label}
      </p>
      <p className="mt-1 text-xs text-white/45">
        Product hint: {status.product_hint || "VideoID"} · issues_cards=
        {String(status.issues_cards)} · apple_pay_ready={String(status.apple_pay_ready)}
      </p>
      <p className="mt-2 text-xs">
        Partner:{" "}
        <a
          href={status.partner_url || "https://webid-solutions.com/en/"}
          className="underline"
          target="_blank"
          rel="noreferrer"
        >
          webid-solutions.com
        </a>
      </p>
    </div>
  );
}
