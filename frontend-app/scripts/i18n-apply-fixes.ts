/**
 * Apply correct translations for leftover EN strings + cookie consent keys.
 * Rewrites src/locales/translations.ts
 */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { translations, type Language } from "../src/locales/translations.ts";
import { pageKeys } from "./i18n-page-keys.ts";

type Tree = { [k: string]: string | Tree };

export function setPath(root: Tree, path: string, value: string) {
  const parts = path.split(".");
  for (const part of parts) {
    if (!part || part === "__proto__" || part === "constructor" || part === "prototype") {
      throw new Error("Unsafe translation path");
    }
  }
  let cur: Tree = root;
  for (let i = 0; i < parts.length - 1; i++) {
    const p = parts[i]!;
    // Guard at the property traversal as well, so static analysis can prove
    // that no inherited prototype property reaches the next tree node.
    if (p === "__proto__" || p === "constructor" || p === "prototype") {
      throw new Error("Unsafe translation path");
    }
    if (typeof cur[p] !== "object" || cur[p] === null) cur[p] = {};
    cur = cur[p] as Tree;
  }
  const leaf = parts[parts.length - 1]!;
  if (leaf === "__proto__" || leaf === "constructor" || leaf === "prototype") {
    throw new Error("Unsafe translation path");
  }
  cur[leaf] = value;
}

function emitKey(k: string): string {
  return /^[A-Za-z_$][\w$]*$/.test(k) ? k : JSON.stringify(k);
}

function emit(value: unknown, indent: number): string {
  const pad = "  ".repeat(indent);
  if (typeof value === "string") return JSON.stringify(value);
  const obj = value as Tree;
  const keys = Object.keys(obj);
  const lines = ["{"];
  keys.forEach((k, idx) => {
    const comma = idx < keys.length - 1 ? "," : "";
    lines.push(`${pad}  ${emitKey(k)}: ${emit(obj[k], indent + 1)}${comma}`);
  });
  lines.push(`${pad}}`);
  return lines.join("\n");
}

const patches: Record<Exclude<Language, "en">, Record<string, string>> = {
  ru: {
    "nav.bridgeAcpBsc": "ACP → BSC (wACP)",
    "nav.whitepaper": "Whitepaper",
    "nav.acpPaper": "Документ ACP",
    "nav.proofCenter": "Центр доказательств",
    "hero.title": "ANCAP — платформа AI-native распределения капитала",
    "homePage.liveMap": "Живая карта продукта",
    "homePage.proofCenter": "Центр доказательств",
    "homePage.freeSnapshot": "Бесплатный снимок токена",
    "homePage.offer2Title": "Пакет подачи на листинг биржи",
    "homePage.offer3Title": "Pro-отчёт о рисках токена",
    "homePage.launchLabel": "Запуск",
    "homePage.riskLabel": "Риск",
    "homePage.riskText": "отчёт по токену, флаги держателей/ликвидности, пробелы в доказательствах",
    "homePage.agentApiLabel": "Agent API",
    "homePage.agentApiText": "эндпоинты с оплатой за вызов, лимиты расходов, квитанции",
    "homePage.proofLabel": "Доказательства",
    "homePage.proofText": "URL квитанции, хэш входа, таймлайн запуска, пакет",
    "homePage.mcpOpenApiLink": "OpenAPI / Swagger",
    "auth.email": "Эл. почта",
  },
  uk: {
    "nav.bridgeAcpBsc": "ACP → BSC (wACP)",
    "nav.whitepaper": "Whitepaper",
    "nav.acpPaper": "Документ ACP",
    "nav.proofCenter": "Центр доказів",
    "hero.title": "ANCAP — платформа AI-native розподілу капіталу",
    "homePage.liveMap": "Жива мапа продукту",
    "homePage.proofCenter": "Центр доказів",
    "homePage.freeSnapshot": "Безкоштовний знімок токена",
    "homePage.offer2Title": "Пакет подання на лістинг біржі",
    "homePage.offer3Title": "Pro-звіт про ризики токена",
    "homePage.launchLabel": "Запуск",
    "homePage.riskLabel": "Ризик",
    "homePage.riskText": "звіт по токену, прапорці держателів/ліквідності, прогалини в доказах",
    "homePage.agentApiLabel": "Agent API",
    "homePage.agentApiText": "ендпоінти з оплатою за виклик, ліміти витрат, квитанції",
    "homePage.proofLabel": "Докази",
    "homePage.proofText": "URL квитанції, хеш входу, таймлайн запуску, пакет",
    "homePage.mcpOpenApiLink": "OpenAPI / Swagger",
    "auth.email": "Ел. пошта",
  },
  de: {
    "nav.vision": "Leitbild",
    "nav.dashboard": "Übersicht",
    "nav.pools": "Kapitalpools",
    "nav.ledger": "Hauptbuch",
    "nav.reputation": "Ruf",
    "nav.listings": "Angebote",
    "nav.flows": "Abläufe",
    "nav.sellerDashboard": "Verkäufer",
    "nav.bridgeAcpBsc": "ACP → BSC (wACP)",
    "nav.login": "Anmelden",
    "nav.logout": "Abmelden",
    "nav.system": "Systemstatus",
    "nav.workflows": "Arbeitsabläufe",
    "nav.webhooks": "Webhooks",
    "nav.feed": "Aktivität",
    "nav.builder": "Editor",
    "nav.whitepaper": "Whitepaper",
    "nav.acpPaper": "ACP-Dokument",
    "nav.evolution": "Entwicklung",
    "nav.bounties": "Belohnungen",
    "nav.proofCenter": "Nachweiszentrum",
    "nav.operationsNoc": "Betriebs-NOC",
    "nav.governance": "Verwaltung",
    "nav.onboarding": "Einstieg",
    "nav.staking": "Staking",
    "nav.runs": "Läufe",
    "hero.title": "ANCAP — KI-native Plattform für Kapitalallokation",
    "hero.acpWalletLink": "Geldbörse",
    "homePage.liveMap": "Live-Produktkarte",
    "homePage.proofCenter": "Nachweiszentrum",
    "homePage.wallet": "Geldbörse",
    "homePage.freeSnapshot": "Kostenloser Token-Snapshot",
    "homePage.offer2Label": "Börsenlisting",
    "homePage.offer2Title": "Paket zur Börsen-Listing-Einreichung",
    "homePage.offer3Title": "Token-Risikobericht Pro",
    "homePage.launchLabel": "Start",
    "homePage.riskLabel": "Risiko",
    "homePage.agentApiLabel": "Agent-API",
    "homePage.proofLabel": "Nachweis",
    "homePage.mcpOpenApiLink": "OpenAPI / Swagger",
    "acpLanding.leanSecurity": "Hybrid Ed25519 + Dilithium2 (PQC-bereit)",
    "product.runsSandbox": "Läufe & Sandbox",
    "product.riskKernel": "Risiko-Kern",
    "vision.coreLedger": "Kern-Hauptbuch & prüfbare Ausführung",
    "vision.marketLayer": "Marktschicht",
    "vision.autonomousEconomy": "Autonome Wirtschaft",
    "dashboard.title": "Übersicht",
    "dashboard.runs": "Läufe",
    "agents.status": "Zustand",
    "agents.reputation": "Ruf",
    "strategies.performance": "Leistung",
    "strategies.status": "Zustand",
    "auth.email": "E-Mail",
  },
  "zh-Hant": {
    "nav.bridgeAcpBsc": "ACP → BSC (wACP)",
    "nav.webhooks": "Webhooks",
    "homePage.offer3Title": "代幣風險報告 Pro",
    "homePage.mcpOpenApiLink": "OpenAPI / Swagger",
  },
};

const cookieKeys: Record<Language, Record<string, string>> = {
  en: {
    "cookies.badge": "Privacy",
    "cookies.title": "Cookie preferences",
    "cookies.body":
      "ANCAP uses necessary cookies and local storage for login, wallet security, language, theme, and consent memory. Optional analytics or marketing storage is used only after consent.",
    "cookies.policy": "Cookie Policy",
    "cookies.privacy": "Privacy Notice",
    "cookies.terms": "User Agreement",
    "cookies.necessary": "Necessary",
    "cookies.necessaryHint": "Required for security and core site features.",
    "cookies.analytics": "Analytics",
    "cookies.analyticsHint": "Helps improve funnels, stability, and UX.",
    "cookies.marketing": "Marketing",
    "cookies.marketingHint": "Used for campaign attribution only when enabled.",
    "cookies.save": "Save choices",
    "cookies.acceptAll": "Accept all",
    "cookies.necessaryOnly": "Necessary only",
    "cookies.customize": "Customize",
    "nav.aeterna": "AETERNA",
  },
  ru: {
    "cookies.badge": "Конфиденциальность",
    "cookies.title": "Настройки cookie",
    "cookies.body":
      "ANCAP использует необходимые cookie и локальное хранилище для входа, безопасности кошелька, языка, темы и согласия. Аналитика и маркетинг — только после согласия.",
    "cookies.policy": "Политика cookie",
    "cookies.privacy": "Уведомление о конфиденциальности",
    "cookies.terms": "Пользовательское соглашение",
    "cookies.necessary": "Необходимые",
    "cookies.necessaryHint": "Нужны для безопасности и базовых функций сайта.",
    "cookies.analytics": "Аналитика",
    "cookies.analyticsHint": "Помогает улучшать воронки, стабильность и UX.",
    "cookies.marketing": "Маркетинг",
    "cookies.marketingHint": "Для атрибуции кампаний — только если включено.",
    "cookies.save": "Сохранить выбор",
    "cookies.acceptAll": "Принять все",
    "cookies.necessaryOnly": "Только необходимые",
    "cookies.customize": "Настроить",
    "nav.aeterna": "AETERNA",
  },
  uk: {
    "cookies.badge": "Конфіденційність",
    "cookies.title": "Налаштування cookie",
    "cookies.body":
      "ANCAP використовує необхідні cookie та локальне сховище для входу, безпеки гаманця, мови, теми та згоди. Аналітика й маркетинг — лише після згоди.",
    "cookies.policy": "Політика cookie",
    "cookies.privacy": "Повідомлення про конфіденційність",
    "cookies.terms": "Угода користувача",
    "cookies.necessary": "Необхідні",
    "cookies.necessaryHint": "Потрібні для безпеки та базових функцій сайту.",
    "cookies.analytics": "Аналітика",
    "cookies.analyticsHint": "Допомагає покращувати воронки, стабільність і UX.",
    "cookies.marketing": "Маркетинг",
    "cookies.marketingHint": "Для атрибуції кампаній — лише якщо ввімкнено.",
    "cookies.save": "Зберегти вибір",
    "cookies.acceptAll": "Прийняти всі",
    "cookies.necessaryOnly": "Лише необхідні",
    "cookies.customize": "Налаштувати",
    "nav.aeterna": "AETERNA",
  },
  de: {
    "cookies.badge": "Datenschutz",
    "cookies.title": "Cookie-Einstellungen",
    "cookies.body":
      "ANCAP verwendet notwendige Cookies und lokalen Speicher für Login, Wallet-Sicherheit, Sprache, Theme und Einwilligung. Optionale Analyse- oder Marketing-Speicherung nur nach Zustimmung.",
    "cookies.policy": "Cookie-Richtlinie",
    "cookies.privacy": "Datenschutzhinweis",
    "cookies.terms": "Nutzungsvereinbarung",
    "cookies.necessary": "Notwendig",
    "cookies.necessaryHint": "Erforderlich für Sicherheit und Kernfunktionen.",
    "cookies.analytics": "Analyse",
    "cookies.analyticsHint": "Hilft, Funnels, Stabilität und UX zu verbessern.",
    "cookies.marketing": "Werbung",
    "cookies.marketingHint": "Nur bei Aktivierung für Kampagnen-Attribution.",
    "cookies.save": "Auswahl speichern",
    "cookies.acceptAll": "Alle akzeptieren",
    "cookies.necessaryOnly": "Nur notwendige",
    "cookies.customize": "Anpassen",
    "nav.aeterna": "AETERNA",
  },
  "zh-Hant": {
    "cookies.badge": "隱私",
    "cookies.title": "Cookie 偏好設定",
    "cookies.body":
      "ANCAP 使用必要的 Cookie 與本機儲存，以支援登入、錢包安全、語言、主題與同意紀錄。分析或行銷儲存僅在同意後使用。",
    "cookies.policy": "Cookie 政策",
    "cookies.privacy": "隱私權聲明",
    "cookies.terms": "使用者協議",
    "cookies.necessary": "必要",
    "cookies.necessaryHint": "安全與核心網站功能所需。",
    "cookies.analytics": "分析",
    "cookies.analyticsHint": "協助改善漏斗、穩定性與使用體驗。",
    "cookies.marketing": "行銷",
    "cookies.marketingHint": "僅在啟用時用於活動歸因。",
    "cookies.save": "儲存選擇",
    "cookies.acceptAll": "全部接受",
    "cookies.necessaryOnly": "僅必要項目",
    "cookies.customize": "自訂",
    "nav.aeterna": "AETERNA",
  },
};

const next = structuredClone(translations) as Record<Language, Tree>;

for (const [lang, map] of Object.entries(patches) as [Exclude<Language, "en">, Record<string, string>][]) {
  for (const [path, value] of Object.entries(map)) setPath(next[lang], path, value);
}
for (const [lang, map] of Object.entries(cookieKeys) as [Language, Record<string, string>][]) {
  for (const [path, value] of Object.entries(map)) setPath(next[lang], path, value);
}
for (const [lang, map] of Object.entries(pageKeys) as [Language, Record<string, string>][]) {
  for (const [path, value] of Object.entries(map)) setPath(next[lang], path, value);
}

// Keep the real resolver, module imports and English fallback when regenerating.
const sourcePath = new URL("../src/locales/translations.ts", import.meta.url);
export function generateTranslationSource(): string {
  const source = readFileSync(sourcePath, "utf8");
  const declaration = "export const translations: Record<Language, TranslationTree> = ";
  const boundary = source.indexOf(declaration);
  if (boundary < 0) throw new Error("Translation declaration missing; refusing to overwrite module");
  return source.slice(0, boundary) + declaration + emit(next, 0) + ";\n";
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  writeFileSync(sourcePath, generateTranslationSource(), "utf8");
  console.log("rewrote translations.ts");
}
