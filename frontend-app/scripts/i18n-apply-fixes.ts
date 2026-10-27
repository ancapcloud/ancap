/**
 * Apply correct translations for leftover EN strings + cookie consent keys.
 * Rewrites src/locales/translations.ts
 */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { type Language } from "../src/locales/translations.ts";
import { pageKeys } from "./i18n-page-keys.ts";

import { applyTranslationPatch } from "../src/locales/translationPatch";
export { applyTranslationPatch as setPath } from "../src/locales/translationPatch";

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

const sourcePath = new URL("../src/locales/translations.ts", import.meta.url);
const beginMarker = "// BEGIN ANCAP generated translation patches";
const endMarker = "// END ANCAP generated translation patches";
const patchImport = 'import { applyTranslationPatch } from "./translationPatch";';

export function generateTranslationSource(source = readFileSync(sourcePath, "utf8")): string {
  if (!source.includes("export const translations: Record<Language, TranslationTree> = ")) {
    throw new Error("Translation declaration missing; refusing to overwrite module");
  }
  const start = source.indexOf(beginMarker);
  if (start >= 0) {
    const end = source.indexOf(endMarker, start);
    if (end < 0) throw new Error("Incomplete generated patch block; refusing to overwrite module");
    source = source.slice(0, start) + source.slice(end + endMarker.length);
  }
  source = source.replace(patchImport + "\r\n", "").replace(patchImport + "\n", "").trimEnd();
  const statements: string[] = [];
  for (const maps of [patches, cookieKeys, pageKeys]) {
    for (const [lang, map] of Object.entries(maps)) {
      for (const [path, value] of Object.entries(map)) {
        applyTranslationPatch({}, path, value);
        statements.push(`applyTranslationPatch(translations[${JSON.stringify(lang)}], ${JSON.stringify(path)}, ${JSON.stringify(value)});`);
      }
    }
  }
  // Keep the entire initializer, including legalByLang.en and all other live
  // domain references. Only the explicitly requested leaf keys are overridden.
  return `${patchImport}\n${source}\n\n${beginMarker}\n${statements.join("\n")}\n${endMarker}\n`;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  writeFileSync(sourcePath, generateTranslationSource(), "utf8");
  console.log("rewrote translations.ts");
}
