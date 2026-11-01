"use client";

import { useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";
import { creatorAiConnectByLang } from "@/locales/creatorAiConnect";
import s from "./CreatorAiConnect.module.css";

export function CreatorAiConnect() {
  const { lang } = useLanguage();
  const c = creatorAiConnectByLang[lang];
  const [copyStatus, setCopyStatus] = useState<"copied" | "error" | null>(null);
  const tools = [
    { name: "ChatGPT", description: c.chat, path: "M6 6h20v15H14l-6 5v-5H6zM11 11h10M11 16h7" },
    { name: "Cursor", description: c.cursor, path: "m8 5 17 11-9 2-4 9zM16 18l6 9" },
    { name: "OpenClaw", description: c.claw, path: "m11 8-8 8 8 8M21 8l8 8-8 8M18 5l-4 22" },
  ];

  async function copyPrompt() {
    try {
      await navigator.clipboard.writeText(c.command);
      setCopyStatus("copied");
    } catch {
      setCopyStatus("error");
    }
  }

  return <section className={s.section} id="connect-ai" aria-labelledby="creator-ai-title">
    <div className={s.intro}>
      <p className={s.eyebrow}><span aria-hidden="true">✦</span> ANCAP × AI</p>
      <h2 id="creator-ai-title">{c.title}</h2>
      <p className={s.lead}>{c.lead}</p>
      <ul className={s.tools}>
        {tools.map(tool => <li key={tool.name}>
          <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={tool.path}/></svg>
          <div><h3>{tool.name}</h3><p>{tool.description}</p></div>
        </li>)}
      </ul>
    </div>
    <div className={s.setup}>
      <div className={s.promptPanel}>
        <div className={s.promptBar}><span className={s.promptTitle}><span aria-hidden="true">↳</span> ANCAP / connect.md</span><span className={s.promptDots} aria-hidden="true">•••</span></div>
        <div className={s.promptContent}>
          <p className={s.promptLabel}>{c.copy}</p>
          <pre><code>{c.command}</code></pre>
          <button type="button" className={s.copyButton} onClick={copyPrompt}>
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4" aria-hidden="true"><rect x="7" y="6" width="9" height="11" rx="2"/><path d="M12 6V3H3v11h4"/></svg>
            {copyStatus === "copied" ? c.copied : c.copy}<span aria-hidden="true">{copyStatus === "copied" ? "✓" : "↗"}</span>
          </button>
        </div>
        <div className={s.apiRow}><Link href="/developers/connect">{c.api}<span aria-hidden="true">→</span></Link><div><Link href="/developers">API</Link><Link href="/mcp">MCP</Link><Link href="/proof-center">{c.proof}<span aria-hidden="true">↗</span></Link></div></div>
      </div>
      <p className={s.note}>{c.note}</p>
      <p className={s.status} role="status">{copyStatus === "error" ? c.error : copyStatus === "copied" ? c.copied : ""}</p>
    </div>
  </section>;
}
