"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import { marketData } from "@/lib/api";
import { racpTransitionCopy } from "@/locales/racpTransition";

type MarketRow = {
  id?: string;
  symbol?: string;
  price?: string | null;
  vs_currency?: string;
};

export function HomeMarketTicker() {
  const { t, lang } = useLanguage();
  const [rows, setRows] = useState<MarketRow[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const payload = await marketData.prices("eur");
        if (cancelled) return;
        const list = Array.isArray(payload?.prices) ? payload.prices : [];
        setRows(list.filter((row: MarketRow) => row?.symbol && row?.price && !["acp", "wacp", "sacp", "racp"].includes(row.symbol.toLowerCase())));
      } catch {
        if (!cancelled) setRows([]);
      } finally {
        if (!cancelled) setReady(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!ready || rows.length === 0) return null;

  const items = [...rows, ...rows];

  return (
    <section
      className="home-market-ticker"
      aria-labelledby="home-market-ticker-title"
      aria-live="off"
    >
      <div className="home-market-ticker__bar">
        <div className="home-market-ticker__meta">
          <h2 id="home-market-ticker-title" className="home-market-ticker__title">
            {t("homePage.marketTickerTitle")}
          </h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "baseline" }}>
            <Link href="/legal/market-data" className="home-market-ticker__legal">
              {t("homePage.marketTickerLegal")}
            </Link>
            <Link href="/markets" className="home-market-ticker__legal">
              Markets
            </Link>
          </div>
        </div>
        <div className="home-market-ticker__viewport">
          <div className="home-market-ticker__track">
            {items.map((row, idx) => (
              <span
                key={`${row.id || row.symbol}-${idx}`}
                className="home-market-ticker__item"
              >
                <strong>{row.symbol}</strong>
                <span>{new Intl.NumberFormat(lang, { style: "currency", currency: "EUR", maximumFractionDigits: 8 }).format(Number(row.price))}</span>
              </span>
            ))}
          </div>
        </div>
        <p className="home-market-ticker__note">{racpTransitionCopy[lang].price}</p>
      </div>
    </section>
  );
}
