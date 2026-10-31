"use client";

import { useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";
import { presentationStyles as s } from "@/components/WorkflowPresentation";

const copy = {
  en: { title: "Bring your AI to ANCAP", lead: "Paste this short instruction into ChatGPT, Cursor or OpenClaw.", command: "Read https://ancap.cloud/connect.txt and help me get started with ANCAP.", chat: "Paste into a chat with web access.", cursor: "Paste into Agent chat and allow it to read the link.", claw: "Send to your agent with web access enabled.", note: "This loads public instructions, not an account connection. Account operations require your ANCAP API key, configured locally. Review paid actions before running them.", button: "Copy instruction", done: "Copied", failed: "Select and copy the instruction above.", docs: "API & MCP setup" },
  ru: { title: "Подключите свой ИИ к ANCAP", lead: "Вставьте короткую команду в ChatGPT, Cursor или OpenClaw.", command: "Прочитай https://ancap.cloud/connect.txt и помоги мне начать работу с ANCAP.", chat: "Вставьте в чат с доступом к интернету.", cursor: "Вставьте в чат Agent и разрешите прочитать ссылку.", claw: "Отправьте своему агенту с включённым веб-доступом.", note: "Команда загружает публичную инструкцию. Для операций с аккаунтом нужен ваш API-ключ ANCAP, настроенный локально. Проверяйте платные действия перед запуском.", button: "Скопировать команду", done: "Скопировано", failed: "Выделите и скопируйте команду выше.", docs: "Настройка API и MCP" },
  uk: { title: "Підключіть свій ШІ до ANCAP", lead: "Вставте коротку команду в ChatGPT, Cursor або OpenClaw.", command: "Прочитай https://ancap.cloud/connect.txt і допоможи мені почати роботу з ANCAP.", chat: "Вставте в чат із доступом до інтернету.", cursor: "Вставте в чат Agent і дозвольте прочитати посилання.", claw: "Надішліть агенту з увімкненим вебдоступом.", note: "Команда завантажує публічну інструкцію. Для операцій з акаунтом потрібен ваш API-ключ ANCAP, налаштований локально. Перевіряйте платні дії перед запуском.", button: "Скопіювати команду", done: "Скопійовано", failed: "Виділіть і скопіюйте команду вище.", docs: "Налаштування API та MCP" },
  de: { title: "Deine KI mit ANCAP verbinden", lead: "Füge diese kurze Anweisung in ChatGPT, Cursor oder OpenClaw ein.", command: "Lies https://ancap.cloud/connect.txt und hilf mir beim Einstieg in ANCAP.", chat: "In einen Chat mit Webzugriff einfügen.", cursor: "In den Agent-Chat einfügen und das Lesen des Links erlauben.", claw: "An deinen Agenten mit aktiviertem Webzugriff senden.", note: "Die Anweisung lädt öffentliche Informationen. Kontoaktionen erfordern deinen lokal eingerichteten ANCAP-API-Schlüssel. Kostenpflichtige Aktionen vor dem Start prüfen.", button: "Anweisung kopieren", done: "Kopiert", failed: "Die Anweisung oben markieren und kopieren.", docs: "API & MCP einrichten" },
  "zh-TW": { title: "將你的 AI 連接至 ANCAP", lead: "將這段簡短指令貼到 ChatGPT、Cursor 或 OpenClaw。", command: "閱讀 https://ancap.cloud/connect.txt 並協助我開始使用 ANCAP。", chat: "貼到可存取網路的對話中。", cursor: "貼到 Agent 對話並允許讀取連結。", claw: "傳送給已啟用網路存取的代理。", note: "此指令會載入公開說明。帳戶操作需要在本機設定你的 ANCAP API 金鑰。執行付費操作前請先確認。", button: "複製指令", done: "已複製", failed: "請選取並複製上方指令。", docs: "API 與 MCP 設定" },
};

export function AgentQuickStart() {
  const { lang } = useLanguage();
  const c = copy[lang === "zh-Hant" ? "zh-TW" : lang];
  const [selected, setSelected] = useState("ChatGPT");
  const [message, setMessage] = useState("");
  async function copyCommand() {
    try {
      await navigator.clipboard.writeText(c.command);
      setMessage(c.done);
    } catch {
      setMessage(c.failed);
    }
  }
  return (
    <section className={s.section} id="connect-ai" aria-labelledby="connect-ai-title">
      <p className={s.eyebrow}>ChatGPT · Cursor · OpenClaw</p>
      <h2 className={s.heading} id="connect-ai-title">{c.title}</h2>
      <p className={s.lead}>{c.lead}</p>
      <div className={s.grid} role="group" aria-label="ChatGPT / Cursor / OpenClaw">
        {[["ChatGPT", c.chat], ["Cursor", c.cursor], ["OpenClaw", c.claw]].map(([name, text], index) => (
          <button type="button" key={name} aria-pressed={selected === name} onClick={() => { setSelected(name); setMessage(""); }}
            className={s.card} style={{ textAlign: "left", cursor: "pointer", color: "var(--text)", borderColor: selected === name ? "var(--accent)" : undefined }}>
            <span className={s.eyebrow}>0{index + 1} / {selected === name ? "●" : "○"}</span>
            <h3>{name} ↗</h3><p>{text}</p>
          </button>
        ))}
      </div>
      <pre className="my-5 whitespace-pre-wrap break-words rounded-2xl border border-[var(--border)] p-5 text-sm"><code>{c.command}</code></pre>
      <div className={s.actions}>
        <button type="button" className={s.primary} onClick={copyCommand}>{c.button} · {selected}</button>
        {selected === "ChatGPT" && <a className={s.secondary} href="https://chatgpt.com/" target="_blank" rel="noopener noreferrer">ChatGPT ↗</a>}
        {selected === "Cursor" && <Link className={s.secondary} href="/mcp">Cursor · MCP →</Link>}
        {selected === "OpenClaw" && <a className={s.secondary} href="/connect.txt" target="_blank" rel="noopener noreferrer">OpenClaw · connect.txt ↗</a>}
        <Link className={s.secondary} href="/mcp">{c.docs} →</Link>
      </div>
      <p role="status" aria-live="polite" style={{ minHeight: 24, marginTop: 12, fontSize: 13 }}>{message}</p>
      <p className={s.note}>{c.note}</p>
    </section>
  );
}
