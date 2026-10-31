import Link from "next/link";
import { Navigation } from "@/components/Navigation";

export const metadata = {
  title: "ANCAP MCP Server | AI agent tools",
  description: "Model Context Protocol tools for token snapshots, payment links, claim codes, and workflows.",
};

const tools = [
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

export default function McpDocsPage() {
  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <Navigation />
      <main className="mx-auto max-w-4xl px-4 py-10">
        <h1 className="text-3xl font-semibold">ANCAP MCP Server</h1>
        <p className="mt-3 text-sm leading-7 text-white/68">
          Connect ChatGPT, Claude, or Cursor to ANCAP commerce tools using an API key. Server package: <code className="text-emerald-300">mcp-server/ancap_mcp_server.py</code>
        </p>
        <pre className="mt-6 overflow-x-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs">
{`export ANCAP_API_KEY=ancap_...
export ANCAP_API_BASE=https://ancap.cloud/api/v1
python mcp-server/ancap_mcp_server.py`}
        </pre>
        <h2 className="mt-8 text-lg font-semibold">Tools</h2>
        <ul className="mt-4 space-y-2 text-sm text-white/75">
          {tools.map((tool) => (
            <li key={tool} className="rounded-lg border border-white/10 bg-white/[0.03] px-4 py-2 font-mono text-xs">
              {tool}
            </li>
          ))}
        </ul>
        <div className="mt-8 flex gap-3">
          <Link href="/developers/connect" className="rounded-full bg-emerald-400 px-5 py-2.5 text-sm font-semibold text-slate-950">
            API keys
          </Link>
          <Link href="/api/docs" className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white/85">
            OpenAPI docs
          </Link>
        </div>
      </main>
    </div>
  );
}
