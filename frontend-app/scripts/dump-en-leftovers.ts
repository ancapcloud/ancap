import { writeFileSync } from "node:fs";
import { translations } from "../src/locales/translations.ts";

function get(o: any, path: string) {
  return path.split(".").reduce((a, k) => a?.[k], o);
}

const keys = [
  "nav.vision",
  "nav.dashboard",
  "nav.pools",
  "nav.ledger",
  "nav.reputation",
  "nav.listings",
  "nav.flows",
  "nav.sellerDashboard",
  "nav.bridgeAcpBsc",
  "nav.login",
  "nav.logout",
  "nav.system",
  "nav.workflows",
  "nav.webhooks",
  "nav.feed",
  "nav.builder",
  "nav.whitepaper",
  "nav.acpPaper",
  "nav.evolution",
  "nav.bounties",
  "nav.proofCenter",
  "nav.operationsNoc",
  "nav.governance",
  "nav.onboarding",
  "nav.staking",
  "nav.runs",
  "hero.title",
  "hero.acpWalletLink",
  "homePage.liveMap",
  "homePage.proofCenter",
  "homePage.wallet",
  "homePage.freeSnapshot",
  "homePage.offer2Label",
  "homePage.offer2Title",
  "homePage.offer3Title",
  "homePage.launchLabel",
  "homePage.riskLabel",
  "homePage.riskText",
  "homePage.agentApiLabel",
  "homePage.agentApiText",
  "homePage.proofLabel",
  "homePage.proofText",
  "homePage.mcpOpenApiLink",
  "acpLanding.leanSecurity",
  "product.runsSandbox",
  "product.riskKernel",
  "vision.coreLedger",
  "vision.marketLayer",
  "vision.autonomousEconomy",
  "dashboard.title",
  "dashboard.runs",
  "agents.status",
  "agents.reputation",
  "strategies.performance",
  "strategies.status",
  "auth.email",
];

const out: Record<string, string> = {};
for (const k of keys) out[k] = String(get(translations.en, k) ?? "");
writeFileSync("tmp-en-leftovers.json", JSON.stringify(out, null, 2), "utf8");
console.log("wrote", Object.keys(out).length);
