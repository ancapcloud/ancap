import { translations, type Language } from "../src/locales/translations.ts";
import { writeFileSync } from "node:fs";

function flat(o: Record<string, unknown>, p = ""): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(o)) {
    const nk = p ? `${p}.${k}` : k;
    if (typeof v === "string") out[nk] = v;
    else Object.assign(out, flat(v as Record<string, unknown>, nk));
  }
  return out;
}

const ALLOW = new Set([
  "ANCAP",
  "ACP",
  "wACP",
  "BSC",
  "USD",
  "USDT",
  "API",
  "SDK",
  "CLI",
  "OK",
  "NOC",
  "DEX",
  "OTC",
  "KYC",
  "AML",
  "LLM",
  "AI",
  "MVP",
  "URL",
  "ID",
  "JSON",
  "HTTP",
  "RPC",
  "Pro Launch Pack",
  "ANCAP Chain Protocol (ACP)",
  "Whitepaper",
  "Webhooks",
  "Staking",
  "Agent API",
  "OpenAPI / Swagger",
  "ACP â†’ BSC (wACP)",
  "ACP -> BSC (wACP)",
  "AETERNA",
  "Pro",
  "Swagger API",
]);

const en = flat(translations.en as Record<string, unknown>);
type LocaleAudit = { keys: number; missing: string[]; extra: string[]; sameAsEn: string[]; sameCount: number };
const report: { enKeys: number; locales: Partial<Record<Language, LocaleAudit>> } = {
  enKeys: Object.keys(en).length, locales: {},
};

for (const loc of ["ru", "uk", "de", "zh-Hant"] as Language[]) {
  const f = flat(translations[loc] as Record<string, unknown>);
  const missing = Object.keys(en).filter((k) => !(k in f));
  const extra = Object.keys(f).filter((k) => !(k in en));
  const same = Object.keys(en).filter((k) => {
    const v = f[k];
    if (v !== en[k]) return false;
    // allow pure brands / very short identical
    if (ALLOW.has(v)) return false;
    if (/^[A-Z0-9 ._()/-]+$/.test(v) && v.length <= 40 && !/[a-z]{4,}/.test(v)) return false;
    return true;
  });
  report.locales[loc] = {
    keys: Object.keys(f).length,
    missing,
    extra,
    sameAsEn: same,
    sameCount: same.length,
  };
}

writeFileSync("tmp-i18n-audit.json", JSON.stringify(report, null, 2), "utf8");
console.log(
  JSON.stringify(
    {
      enKeys: report.enKeys,
      summary: Object.fromEntries(
        Object.entries(report.locales as Record<string, { sameCount: number; missing: string[] }>).map(
          ([k, v]) => [k, { sameCount: v.sameCount, missing: v.missing.length }],
        ),
      ),
    },
    null,
    2,
  ),
);
