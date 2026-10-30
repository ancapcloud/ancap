"use client";
import { formatRacpEquivalent } from "@/lib/racpDisplay";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Navigation } from "@/components/Navigation";
import { useLanguage } from "@/components/LanguageProvider";
import { fieldServicesDesk } from "@/lib/api";
import { SiteLegalFooter } from "@/components/legal/LegalViews";

type Group = {
  id: string;
  label: string;
  blurb: string;
};

type Service = {
  id: string;
  group_id: string;
  review_target_id: string;
  label: string;
  price_eur: string;
  blurb: string;
  workflow_slug?: string | null;
  regions?: string[];
};

type Region = {
  id: string;
  label: string;
  blurb: string;
};

type Catalog = {
  title: string;
  tagline: string;
  compliance_note: string;
  groups: Group[];
  services: Service[];
  regions: Region[];
  legal_href: string;
  service_fee_eur?: string;
};

type Quote = {
  service_id: string;
  label: string;
  installation_fee_eur: string;
  service_fee_eur: string;
  total_eur: string;
  total_usdt: string;
  amount_acp: string;
  amount_wacp: string;
  payment_currency: string;
  pay_amount: string;
  workflow_slug: string;
  provider_label: string;
  provider_location: string;
  escrow_note: string;
};

type PayChoice = "ACP" | "wACP" | "USDT";

const VALID_GROUPS = new Set(["starlink", "it", "cameras", "solar", "space"]);

function FieldServicesInner() {
  const { t } = useLanguage();
  const searchParams = useSearchParams();
  const initialGroup = useMemo(() => {
    const g = (searchParams?.get("group") || "").trim().toLowerCase();
    return VALID_GROUPS.has(g) ? g : "all";
  }, [searchParams]);

  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [error, setError] = useState("");
  const [groupFilter, setGroupFilter] = useState<string>(initialGroup);
  const [regionFilter, setRegionFilter] = useState<string>("de-nrw");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [payChoice, setPayChoice] = useState<PayChoice>("ACP");
  const [quote, setQuote] = useState<Quote | null>(null);
  const [quoteBusy, setQuoteBusy] = useState(false);

  useEffect(() => {
    setGroupFilter(initialGroup);
  }, [initialGroup]);

  const load = useCallback(async () => {
    try {
      const data = (await fieldServicesDesk.catalog()) as Catalog;
      setCatalog(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("fieldServicesPage.loadError"));
    }
  }, [t]);

  useEffect(() => {
    void load();
    document.title = `ANCAP — ${t("fieldServicesPage.title")}`;
  }, [load, t]);

  const services = (catalog?.services || []).filter((svc) => {
    if (groupFilter !== "all" && svc.group_id !== groupFilter) return false;
    if (regionFilter === "all") return true;
    return (svc.regions || []).includes(regionFilter);
  });

  const buildQuote = async (serviceId: string, currency: PayChoice = payChoice) => {
    setSelectedId(serviceId);
    setQuoteBusy(true);
    setQuote(null);
    try {
      const region = regionFilter === "all" ? "de-nrw" : regionFilter;
      const data = (await fieldServicesDesk.quote({
        service_id: serviceId,
        region,
        payment_currency: currency === "USDT" ? "ACP" : currency,
      })) as Quote;
      setQuote({ ...data, payment_currency: currency === "USDT" ? "USDT" : data.payment_currency });
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("fieldServicesPage.quoteError"));
    } finally {
      setQuoteBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0e14] text-[#e8eef7]">
      <Navigation />
      <main>
        <section
          className="relative overflow-hidden border-b border-white/10"
          style={{
            background:
              "radial-gradient(ellipse at 20% 0%, rgba(56,189,248,0.16), transparent 52%), linear-gradient(165deg, #071018 0%, #0a0e14 55%, #0f1a22 100%)",
          }}
        >
          <div className="container" style={{ padding: "64px 24px 40px" }}>
            <p className="section-num" style={{ letterSpacing: "0.18em", color: "#7dd3fc" }}>
              {t("fieldServicesPage.kicker")}
            </p>
            <h1
              className="section-title"
              style={{
                marginTop: 12,
                marginBottom: 14,
                maxWidth: 920,
                fontFamily: "var(--font-display, Georgia, 'Times New Roman', serif)",
              }}
            >
              {t("fieldServicesPage.title")}
            </h1>
            <p className="section-subtitle" style={{ maxWidth: 720, marginBottom: 16 }}>
              {catalog?.tagline || t("fieldServicesPage.lead")}
            </p>
            <p style={{ maxWidth: 760, color: "rgba(226,232,240,0.55)", lineHeight: 1.7, fontSize: "0.95rem" }}>
              {catalog?.compliance_note || t("fieldServicesPage.compliance")}
            </p>
            {groupFilter === "starlink" ? (
              <p style={{ maxWidth: 760, marginTop: 12, color: "#bae6fd", fontSize: "0.9rem" }}>
                {t("fieldServicesPage.starlinkHubHint")}
              </p>
            ) : null}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 24 }}>
              <Link href="#services" className="btn btn-primary">
                {t("fieldServicesPage.servicesCta")}
              </Link>
              <Link
                href={
                  groupFilter === "space"
                    ? "/legal/space-ai-datacenter"
                    : catalog?.legal_href || "/legal/field-services"
                }
                className="btn btn-ghost"
              >
                {t("fieldServicesPage.legalCta")}
              </Link>
              <Link href="/buy-acp" className="btn btn-ghost">
                {t("fieldServicesPage.buyAcpCta")}
              </Link>
            </div>
          </div>
        </section>

        <section className="container" style={{ padding: "36px 24px 12px" }}>
          <h2 className="section-title" style={{ fontSize: "1.35rem", marginBottom: 14 }}>
            {t("fieldServicesPage.groupsTitle")}
          </h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 24 }}>
            <button
              type="button"
              className={groupFilter === "all" ? "btn btn-primary" : "btn btn-ghost"}
              onClick={() => setGroupFilter("all")}
            >
              {t("fieldServicesPage.groupAll")}
            </button>
            {(catalog?.groups || []).map((group) => (
              <button
                key={group.id}
                type="button"
                className={groupFilter === group.id ? "btn btn-primary" : "btn btn-ghost"}
                onClick={() => setGroupFilter(group.id)}
                title={group.blurb}
              >
                {group.label}
              </button>
            ))}
          </div>

          <h2 className="section-title" style={{ fontSize: "1.35rem", marginBottom: 14 }}>
            {t("fieldServicesPage.regionsTitle")}
          </h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 28 }}>
            <button
              type="button"
              className={regionFilter === "all" ? "btn btn-primary" : "btn btn-ghost"}
              onClick={() => setRegionFilter("all")}
            >
              {t("fieldServicesPage.allRegions")}
            </button>
            {(catalog?.regions || []).map((region) => (
              <button
                key={region.id}
                type="button"
                className={regionFilter === region.id ? "btn btn-primary" : "btn btn-ghost"}
                onClick={() => setRegionFilter(region.id)}
                title={region.blurb}
              >
                {region.label}
              </button>
            ))}
          </div>
          {error ? <p style={{ color: "#fbbf24", marginBottom: 16 }}>{error}</p> : null}
        </section>

        <section id="services" className="container" style={{ padding: "0 24px 40px" }}>
          <h2 className="section-title" style={{ fontSize: "1.5rem", marginBottom: 8 }}>
            {t("fieldServicesPage.servicesTitle")}
          </h2>
          <p style={{ color: "var(--text-muted)", marginBottom: 28, maxWidth: 720 }}>
            {t("fieldServicesPage.servicesLead")}
          </p>
          <div className="responsive-grid responsive-grid-2">
            {services.map((svc) => (
              <article
                key={svc.id}
                className="card"
                style={{
                  borderRadius: 12,
                  background: "rgba(16, 24, 40, 0.92)",
                  border:
                    selectedId === svc.id
                      ? "1px solid rgba(125, 211, 252, 0.55)"
                      : "1px solid rgba(125, 211, 252, 0.14)",
                }}
              >
                <div className="card-header">
                  <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: 0 }}>{svc.label}</h3>
                  <strong style={{ color: "#7dd3fc", whiteSpace: "nowrap" }}>
                    €{Number(svc.price_eur).toLocaleString()}
                  </strong>
                </div>
                <p style={{ color: "var(--text-muted)", lineHeight: 1.65, minHeight: 72 }}>{svc.blurb}</p>
                <div className="action-cluster" style={{ marginTop: 14 }}>
                  <button
                    type="button"
                    className="btn btn-primary"
                    disabled={quoteBusy}
                    onClick={() => void buildQuote(svc.id)}
                  >
                    {t("fieldServicesPage.quoteCta")}
                  </button>
                </div>
              </article>
            ))}
          </div>
          {!services.length && !error ? (
            <p style={{ color: "var(--text-muted)" }}>{t("fieldServicesPage.emptyFilter")}</p>
          ) : null}
        </section>

        {quote ? (
          <section className="container" style={{ padding: "0 24px 72px" }} id="order">
            <article
              className="card"
              style={{
                maxWidth: 520,
                borderRadius: 14,
                background: "rgba(12, 20, 32, 0.95)",
                border: "1px solid rgba(125, 211, 252, 0.22)",
                padding: 24,
              }}
            >
              <h2 style={{ fontSize: "1.25rem", marginTop: 0 }}>{t("fieldServicesPage.orderTitle")}</h2>
              <p style={{ color: "#7dd3fc", fontWeight: 600, marginBottom: 16 }}>{quote.label}</p>
              <div style={{ display: "grid", gap: 8, fontFamily: "ui-monospace, monospace", fontSize: "0.95rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>{t("fieldServicesPage.installFee")}</span>
                  <span>€{quote.installation_fee_eur}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>{t("fieldServicesPage.serviceFee")}</span>
                  <span>€{quote.service_fee_eur}</span>
                </div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    borderTop: "1px solid rgba(255,255,255,0.12)",
                    paddingTop: 8,
                    fontWeight: 700,
                  }}
                >
                  <span>{t("fieldServicesPage.total")}</span>
                  <span>€{quote.total_eur}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", color: "#bae6fd" }}>
                  <span>rACP equiv.</span>
                  <span>{formatRacpEquivalent(quote.amount_acp)} rACP equiv.</span>
                </div>

              </div>

              <p style={{ marginTop: 18, marginBottom: 8, fontWeight: 600 }}>{t("fieldServicesPage.payment")}</p>
              <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 16 }}>
                {(["ACP"] as PayChoice[]).map((choice) => (
                  <label key={choice} style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }}>
                    <input
                      type="radio"
                      name="pay"
                      checked={payChoice === choice}
                      onChange={() => {
                        setPayChoice(choice);
                        if (selectedId) void buildQuote(selectedId, choice);
                      }}
                    />
                    <span>
                      {choice === "ACP"
                        ? t("fieldServicesPage.payAcp")
                        : choice === "wACP"
                          ? t("fieldServicesPage.payWacp")
                          : t("fieldServicesPage.payUsdt")}
                    </span>
                  </label>
                ))}
              </div>

              <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", lineHeight: 1.6 }}>
                {t("fieldServicesPage.provider")}: {quote.provider_label} · {quote.provider_location}
              </p>
              <p style={{ color: "#86efac", fontWeight: 600 }}>{t("fieldServicesPage.escrow")}</p>
              <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", lineHeight: 1.6 }}>{quote.escrow_note}</p>

              <div className="action-cluster" style={{ marginTop: 20 }}>
                {payChoice === "USDT" ? (
                  <>
                    <Link href="/buy-acp" className="btn btn-primary">
                      {t("fieldServicesPage.buyAcpCta")}
                    </Link>
                    <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", width: "100%" }}>
                      {t("fieldServicesPage.usdtHint")}
                    </p>
                  </>
                ) : (
                  <Link href={`/ai/run/${quote.workflow_slug}`} className="btn btn-primary">
                    {t("fieldServicesPage.payCreate")}
                  </Link>
                )}
                <Link href={`/ai/run/${quote.workflow_slug}`} className="btn btn-ghost">
                  {t("fieldServicesPage.openWorkflow")}
                </Link>
              </div>
              <p style={{ marginTop: 14, color: "#86efac", fontSize: "0.9rem" }}>{t("fieldServicesPage.confirmed")}</p>
            </article>
          </section>
        ) : null}

        <section className="container" style={{ padding: "0 24px 72px" }}>
          <p style={{ color: "var(--text-muted)", maxWidth: 820, lineHeight: 1.7 }}>{t("fieldServicesPage.footerNote")}</p>
        </section>
      </main>
      <SiteLegalFooter />
    </div>
  );
}

export default function FieldServicesPage() {
  return (
    <Suspense fallback={null}>
      <FieldServicesInner />
    </Suspense>
  );
}
