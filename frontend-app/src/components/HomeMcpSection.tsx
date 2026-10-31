"use client";

import type { CSSProperties } from "react";
import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";

const MCP_TOOLS = [
  "ancap.token_snapshot",
  "ancap.create_risk_report",
  "ancap.create_payment_link",
  "ancap.create_invoice",
  "ancap.check_payment_status",
  "ancap.create_claim_code",
  "ancap.redeem_claim_code",
  "ancap.quote_smart_pay",
  "ancap.run_workflow",
];

const MCP_LINKS = [
  { href: "/mcp", labelKey: "homePage.mcpDocsLink" },
  { href: "/developers", labelKey: "homePage.mcpApiKeysLink" },
  { href: "/api/docs", labelKey: "homePage.mcpOpenApiLink", external: true },
  { href: "/ai/workflows", labelKey: "homePage.mcpWorkflowsLink" },
  { href: "/pay/create", labelKey: "homePage.mcpPayLink" },
  { href: "/token-snapshot", labelKey: "homePage.mcpSnapshotLink" },
] as const;

const cardBodyStyle: CSSProperties = {
  color: "var(--text-muted)",
  lineHeight: 1.65,
  margin: 0,
  overflowWrap: "anywhere",
  wordBreak: "break-word",
};

const cardStyle: CSSProperties = {
  borderRadius: 8,
  minWidth: 0,
  overflow: "hidden",
};

export function HomeMcpSection() {
  const { t } = useLanguage();

  return (
    <section
      id="mcp"
      className="container"
      style={{ padding: "62px 24px", borderTop: "1px solid var(--border)" }}
      aria-labelledby="home-mcp-title"
    >
      <span className="section-num">{t("homePage.mcpKicker")}</span>
      <h2 id="home-mcp-title" className="section-title" style={{ maxWidth: 720, marginBottom: 14 }}>
        {t("homePage.mcpTitle")}
      </h2>
      <p className="section-subtitle" style={{ maxWidth: 820, marginBottom: 28 }}>
        {t("homePage.mcpLead")}
      </p>

      <div className="responsive-grid responsive-grid-3" style={{ marginBottom: 28 }}>
        {[1, 2, 3].map((idx) => (
          <div key={idx} className="card" style={cardStyle}>
            <h3 style={{ fontSize: "1.05rem", fontWeight: 800, marginBottom: 10 }}>
              {t(`homePage.mcpStep${idx}Title`)}
            </h3>
            <p style={cardBodyStyle}>{t(`homePage.mcpStep${idx}Text`)}</p>
          </div>
        ))}
      </div>

      <div
        className="home-split-grid"
        style={{
          display: "grid",
          gap: 24,
          alignItems: "start",
          minWidth: 0,
        }}
      >
        <div className="card" style={cardStyle}>
          <h3 style={{ fontSize: "1.05rem", fontWeight: 800, marginBottom: 12 }}>
            {t("homePage.mcpConfigTitle")}
          </h3>
          <p
            style={{
              color: "var(--text-muted)",
              lineHeight: 1.65,
              marginBottom: 14,
              fontSize: "0.92rem",
              overflowWrap: "anywhere",
              wordBreak: "break-word",
            }}
          >
            {t("homePage.mcpConfigLead")}
          </p>
          <pre
            className="overflow-x-auto rounded-xl border border-white/10 bg-black/30 p-4 text-xs leading-6"
            style={{ margin: 0, maxWidth: "100%", whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}
          >
{`ChatGPT Server URL:
https://ancap.cloud/api/v1/mcp

Cursor / Claude Desktop (stdio):
{
  "mcpServers": {
    "ancap": {
      "command": "python",
      "args": ["path/to/ancap/mcp-server/ancap_mcp_server.py"],
      "env": {
        "ANCAP_API_KEY": "ancap_your_key",
        "ANCAP_API_BASE": "https://ancap.cloud/api/v1"
      }
    }
  }
}`}
          </pre>
          <p style={{ color: "var(--text-muted)", lineHeight: 1.6, marginTop: 12, fontSize: "0.88rem" }}>
            {t("homePage.mcpCliNote")}
          </p>
          <pre
            className="mt-3 overflow-x-auto rounded-xl border border-white/10 bg-black/30 p-4 text-xs leading-6"
            style={{ margin: 0, maxWidth: "100%", whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}
          >
{`export ANCAP_API_KEY=ancap_...
export ANCAP_API_BASE=https://ancap.cloud/api/v1
python mcp-server/ancap_mcp_server.py`}
          </pre>
        </div>

        <div style={{ display: "grid", gap: 16, minWidth: 0 }}>
          <div className="card" style={cardStyle}>
            <h3 style={{ fontSize: "1.05rem", fontWeight: 800, marginBottom: 12 }}>
              {t("homePage.mcpToolsTitle")}
            </h3>
            <ul style={{ display: "grid", gap: 8, margin: 0, padding: 0, listStyle: "none" }}>
              {MCP_TOOLS.map((tool) => (
                <li
                  key={tool}
                  style={{
                    borderRadius: 8,
                    border: "1px solid var(--border)",
                    background: "rgba(255,255,255,0.03)",
                    padding: "8px 12px",
                    fontFamily: "monospace",
                    fontSize: "0.78rem",
                    color: "var(--text-muted)",
                    overflowWrap: "anywhere",
                    wordBreak: "break-word",
                  }}
                >
                  {tool}
                </li>
              ))}
            </ul>
          </div>

          <div className="card" style={cardStyle}>
            <h3 style={{ fontSize: "1.05rem", fontWeight: 800, marginBottom: 12 }}>
              {t("homePage.mcpLinksTitle")}
            </h3>
            <div className="action-cluster" style={{ flexWrap: "wrap" }}>
              {MCP_LINKS.map((link) =>
                "external" in link && link.external ? (
                  <a
                    key={link.href}
                    href={link.href}
                    className="btn btn-ghost"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {t(link.labelKey)}
                  </a>
                ) : (
                  <Link key={link.href} href={link.href} className="btn btn-ghost">
                    {t(link.labelKey)}
                  </Link>
                ),
              )}
            </div>
            <div className="action-cluster" style={{ marginTop: 14 }}>
              <Link href="/mcp" className="btn btn-primary">
                {t("homePage.mcpCta")}
              </Link>
              <Link href="/developers" className="btn btn-ghost">
                {t("homePage.mcpApiKeysLink")}
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
