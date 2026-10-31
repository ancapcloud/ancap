"use client";

import { useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";

const messages = {
  en: { title: "Your expertise. Your AI. One workspace.", lead: "Explore ANCAP with ChatGPT, build integrations in Cursor, or give OpenClaw a workflow to help with.", command: "Read https://ancap.cloud/connect.md and help me get started with ANCAP.", copy: "Copy starter prompt", copied: "Copied", error: "Select and copy the prompt above.", api: "Connect via API", note: "Paste into an AI chat with web access. API actions need your own ANCAP key; review any paid run before starting.", chat: "Discover workflows", cursor: "Build your integration", claw: "Assist your workflow" },
  ru: { title: "Ваш опыт. Ваш ИИ. Одно рабочее пространство.", lead: "Находите возможности ANCAP с ChatGPT, создавайте интеграции в Cursor и поручайте OpenClaw помощь с рабочими процессами.", command: "Прочитай https://ancap.cloud/connect.md и помоги мне начать работу с ANCAP.", copy: "Скопировать команду для ИИ", copied: "Скопировано", error: "Выделите и скопируйте команду выше.", api: "Подключиться через API", note: "Вставьте в чат ИИ с веб-доступом. Для действий через API нужен ваш ключ ANCAP; проверяйте платные запуски перед подтверждением.", chat: "Найдите подходящий workflow", cursor: "Создайте интеграцию", claw: "Помощь с рабочими процессами" },
  uk: { title: "Ваш досвід. Ваш ШІ. Єдиний робочий простір.", lead: "Відкривайте ANCAP із ChatGPT, створюйте інтеграції в Cursor і доручайте OpenClaw допомогу з процесами.", command: "Прочитай https://ancap.cloud/connect.md і допоможи мені почати роботу з ANCAP.", copy: "Скопіювати команду для ШІ", copied: "Скопійовано", error: "Виділіть і скопіюйте команду вище.", api: "Підключитися через API", note: "Вставте в чат ШІ з вебдоступом. Для дій через API потрібен ваш ключ ANCAP; перевіряйте платні запуски перед підтвердженням.", chat: "Знайдіть потрібний workflow", cursor: "Створіть інтеграцію", claw: "Допомога з процесами" },
  de: { title: "Dein Wissen. Deine KI. Ein Workspace.", lead: "Entdecke ANCAP mit ChatGPT, baue Integrationen in Cursor und nutze OpenClaw zur Unterstützung deiner Workflows.", command: "Lies https://ancap.cloud/connect.md und hilf mir beim Einstieg in ANCAP.", copy: "Startanweisung kopieren", copied: "Kopiert", error: "Die Anweisung oben markieren und kopieren.", api: "Per API verbinden", note: "In einen KI-Chat mit Webzugriff einfügen. API-Aktionen benötigen deinen ANCAP-Schlüssel; kostenpflichtige Läufe vorher prüfen.", chat: "Workflows entdecken", cursor: "Integration entwickeln", claw: "Workflows unterstützen" },
  "zh-Hant": { title: "你的專業。你的 AI。同一個工作空間。", lead: "透過 ChatGPT 探索 ANCAP、在 Cursor 建立整合，並讓 OpenClaw 協助工作流程。", command: "閱讀 https://ancap.cloud/connect.md 並協助我開始使用 ANCAP。", copy: "複製入門指令", copied: "已複製", error: "請選取並複製上方指令。", api: "透過 API 連接", note: "貼到可存取網路的 AI 對話中。API 操作需要你的 ANCAP 金鑰；執行付費流程前請先確認。", chat: "探索工作流程", cursor: "建立整合", claw: "協助工作流程" },
};

export function CreatorAiConnect() {
  const { lang } = useLanguage();
  const c = messages[lang];
  const [status, setStatus] = useState("");
  return <aside className="relative overflow-hidden rounded-3xl border border-emerald-300/20 bg-gradient-to-br from-emerald-400/[0.09] via-sky-400/[0.04] to-transparent p-6 sm:p-8" aria-labelledby="creator-ai-title">
    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-300">ANCAP × AI</p>
    <h3 id="creator-ai-title" className="mt-3 text-2xl font-semibold tracking-tight">{c.title}</h3>
    <p className="mt-3 text-sm leading-6 text-[var(--text-secondary)]">{c.lead}</p>
    <div className="my-6 grid grid-cols-3 gap-2">
      {[["ChatGPT", c.chat], ["Cursor", c.cursor], ["OpenClaw", c.claw]].map(([name, text]) => <div key={name} className="rounded-2xl border border-white/10 bg-black/15 p-3"><strong className="text-sm">{name}</strong><p className="mt-1 text-xs leading-5 text-[var(--text-secondary)]">{text}</p></div>)}
    </div>
    <pre className="whitespace-pre-wrap break-words rounded-2xl border border-white/10 bg-black/20 p-4 text-xs leading-6"><code>{c.command}</code></pre>
    <div className="mt-4 flex flex-wrap gap-3">
      <button type="button" className="btn btn-primary" onClick={async () => { try { await navigator.clipboard.writeText(c.command); setStatus(c.copied); } catch { setStatus(c.error); } }}>{c.copy}</button>
      <Link href="/developers/connect" className="btn btn-ghost">{c.api} →</Link>
    </div>
    <p role="status" className="mt-2 text-xs text-emerald-300">{status}</p>
    <p className="mt-3 text-xs leading-5 text-[var(--text-secondary)]">{c.note}</p>
    <div className="mt-4 flex gap-5 text-sm text-emerald-300"><Link href="/developers">API</Link><Link href="/mcp">MCP</Link><Link href="/proof-center">Proof →</Link></div>
  </aside>;
}
