"use client";

import { useEffect, useId, useRef } from "react";

declare global {
  interface Window {
    turnstile?: {
      render: (container: string | HTMLElement, options: Record<string, unknown>) => string;
      remove?: (widgetId: string) => void;
      reset?: (widgetId?: string) => void;
    };
    __ancapTurnstileScriptLoading?: Promise<void>;
  }
}

type Props = {
  siteKey: string;
  action: "login" | "register" | "racp_airdrop";
  onTokenChange: (token: string) => void;
  resetSignal?: string | number;
};

function ensureScript(): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();
  if (window.turnstile) return Promise.resolve();
  if (window.__ancapTurnstileScriptLoading) return window.__ancapTurnstileScriptLoading;

  window.__ancapTurnstileScriptLoading = new Promise<void>((resolve, reject) => {
    const existing = document.querySelector('script[data-turnstile="ancap"]') as HTMLScriptElement | null;
    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error("Turnstile script failed to load")), { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
    script.async = true;
    script.defer = true;
    script.dataset.turnstile = "ancap";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Turnstile script failed to load"));
    document.head.appendChild(script);
  });

  return window.__ancapTurnstileScriptLoading;
}

export function TurnstileWidget({ siteKey, action, onTokenChange, resetSignal }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const widgetIdRef = useRef<string | null>(null);
  const domId = useId().replace(/:/g, "_");

  useEffect(() => {
    onTokenChange("");
  }, [action, onTokenChange]);

  useEffect(() => {
    if (!siteKey || !containerRef.current) return;
    let cancelled = false;

    ensureScript()
      .then(() => {
        if (cancelled || !containerRef.current || !window.turnstile) return;
        containerRef.current.innerHTML = "";
        widgetIdRef.current = window.turnstile.render(containerRef.current, {
          sitekey: siteKey,
          action,
          theme: "dark",
          callback: (token: string) => onTokenChange(token || ""),
          "expired-callback": () => onTokenChange(""),
          "error-callback": () => onTokenChange(""),
        });
      })
      .catch(() => {
        onTokenChange("");
      });

    return () => {
      cancelled = true;
      if (widgetIdRef.current && window.turnstile?.remove) {
        window.turnstile.remove(widgetIdRef.current);
      }
      widgetIdRef.current = null;
    };
  }, [action, onTokenChange, resetSignal, siteKey]);

  if (!siteKey) return null;

  return (
    <div className="turnstile-shell">
      <div id={`turnstile_${domId}`} ref={containerRef} className="turnstile-inner" style={{ minHeight: 65 }} />
    </div>
  );
}
