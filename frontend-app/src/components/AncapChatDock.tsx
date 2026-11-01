"use client";

import dynamic from "next/dynamic";
import { useRef } from "react";
import { usePathname } from "next/navigation";
import { useAncapChat } from "./AncapChatProvider";
import { useLanguage } from "./LanguageProvider";
import { homeChatByLang } from "@/locales/homeChat";
import s from "./AncapChatDock.module.css";

const ChatPanel = dynamic(() => import("./HomeChatDialog").then(module => module.HomeChatDialog), { ssr: false });

export function AncapChatDock() {
  const { dockOpen, setDockOpen } = useAncapChat();
  const { lang } = useLanguage();
  const text = homeChatByLang[lang];
  const pathname = usePathname();
  const launcherRef = useRef<HTMLButtonElement>(null);

  function minimize() {
    setDockOpen(false);
    launcherRef.current?.focus();
  }

  return <div className={s.root} data-avoid-support={pathname === "/stardust" || undefined}>
    {dockOpen && <div className={s.panel}>
      <ChatPanel surface="dock" onMinimize={minimize} />
    </div>}
    <button ref={launcherRef} type="button" className={`${s.launcher}${dockOpen ? ` ${s.active}` : ""}`} aria-label={text.dialog} aria-expanded={dockOpen} aria-controls={dockOpen ? "ancap-chat-panel" : undefined} onClick={() => dockOpen ? minimize() : setDockOpen(true)}>
      <svg viewBox="0 0 28 28" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        {dockOpen ? <path d="m7 11 7 7 7-7"/> : <><path d="M5 5h18v13H13l-6 5v-5H5z"/><path d="M10 10h8M10 14h5"/></>}
      </svg>
      <span>{text.dialog}</span>
    </button>
  </div>;
}
