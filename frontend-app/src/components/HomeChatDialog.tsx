"use client";

import Link from "next/link";
import { useEffect, useId, useRef, useState } from "react";
import { useAncapChat, type ChatMode } from "./AncapChatProvider";
import { useLanguage } from "@/components/LanguageProvider";
import type { Language } from "@/locales/translations";
import styles from "./HomeChatDialog.module.css";
import { homeChatByLang } from "@/locales/homeChat";

type Role = "user" | "assistant";
type Mode = ChatMode;
type SpeechResult = { results: ArrayLike<ArrayLike<{ transcript: string }>> };
type SpeechRec = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: SpeechResult) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

const speechLang: Record<Language, string> = {
  en: "en-US",
  ru: "ru-RU",
  uk: "uk-UA",
  de: "de-DE",
  "zh-Hant": "zh-TW",
};

export function HomeChatDialog({ surface = "inline", onMinimize }: { surface?: "inline" | "dock"; onMinimize?: () => void }) {
  const { lang } = useLanguage();
  const text = homeChatByLang[lang];
  const chat = useAncapChat();
  const { draft, setDraft, messages, mode, setMode, sessionModel, label, loading, configured, error, setError, ensureStatus } = chat;
  const [modelOpen, setModelOpen] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [listening, setListening] = useState(false);
  const instanceId = useId();
  const inputId = `ancap-chat-input-${instanceId}`;
  const headingId = `ancap-chat-title-${instanceId}`;
  const docked = surface === "dock";
  const fieldRef = useRef<HTMLTextAreaElement>(null);
  const rootRef = useRef<HTMLElement>(null);
  const recognitionRef = useRef<SpeechRec | null>(null);
  const transcriptRef = useRef<HTMLDivElement>(null);
  useEffect(() => { void ensureStatus(); }, [ensureStatus]);

  useEffect(() => {
    if (docked) rootRef.current?.focus();
  }, [docked]);

  useEffect(() => {
    if (!modelOpen && !fullscreen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (modelOpen) setModelOpen(false);
      else if (fullscreen) setFullscreen(false);
    };
    const onPointer = () => {
      if (modelOpen) setModelOpen(false);
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("pointerdown", onPointer);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("pointerdown", onPointer);
    };
  }, [modelOpen, fullscreen]);

  useEffect(() => {
    if (!fullscreen) return;
    const previous = document.body.style.overflow;
    const previousFocus = document.activeElement as HTMLElement | null;
    document.body.style.overflow = "hidden";
    rootRef.current?.focus();
    const trapFocus = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;
      const controls = rootRef.current?.querySelectorAll<HTMLElement>('a[href], button:not([disabled]), textarea:not([disabled])');
      if (!controls?.length) return;
      const first = controls[0];
      const last = controls[controls.length - 1];
      if (event.shiftKey && (document.activeElement === first || document.activeElement === rootRef.current)) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", trapFocus);
    return () => {
      document.body.style.overflow = previous;
      document.removeEventListener("keydown", trapFocus);
      previousFocus?.focus();
    };
  }, [fullscreen]);

  useEffect(() => {
    const node = transcriptRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [messages, loading]);

  useEffect(() => () => recognitionRef.current?.stop(), []);

  function stopVoice() {
    recognitionRef.current?.stop();
    setListening(false);
  }

  function toggleVoice() {
    if (listening) {
      stopVoice();
      return;
    }
    const host = window as Window & {
      SpeechRecognition?: new () => SpeechRec;
      webkitSpeechRecognition?: new () => SpeechRec;
    };
    const Ctor = host.SpeechRecognition || host.webkitSpeechRecognition;
    if (!Ctor) {
      setError(text.noVoice);
      return;
    }
    const rec = new Ctor();
    const base = draft.trim();
    rec.lang = speechLang[lang] ?? "en-US";
    rec.interimResults = true;
    rec.continuous = false;
    rec.onresult = (event) => {
      let spoken = "";
      for (let i = 0; i < event.results.length; i += 1) spoken += event.results[i][0]?.transcript ?? "";
      const next = spoken.trim();
      setDraft(base && next ? `${base} ${next}` : next || base);
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);
    recognitionRef.current = rec;
    setError("");
    setListening(true);
    try {
      rec.start();
    } catch {
      setListening(false);
      setError(text.noVoice);
    }
  }

  function resetChat() {
    stopVoice();
    chat.resetChat();
    setModelOpen(false);
    fieldRef.current?.focus();
  }

  async function sendMessage(raw: string, nextMode: Mode = mode) {
    stopVoice();
    setModelOpen(false);
    await chat.sendMessage(raw, nextMode);
  }

  function applyStarter(nextMode: Mode, prompt: string) {
    setMode(nextMode);
    void sendMessage(prompt, nextMode);
  }

  return (
    <section
      ref={rootRef}
      className={`${styles.root}${docked ? ` ${styles.docked}` : ""}${fullscreen ? ` ${styles.fullscreen}` : ""}`}
      id={docked ? "ancap-chat-panel" : "ask"}
      data-testid={docked ? "dock-chat" : "home-chat"}
      data-fullscreen={fullscreen ? "true" : "false"}
      aria-labelledby={headingId}
      role={fullscreen || docked ? "dialog" : undefined}
      aria-modal={fullscreen || undefined}
      tabIndex={fullscreen || docked ? -1 : undefined}
      onKeyDown={event => {
        if (event.key === "Escape" && docked && !modelOpen && !fullscreen) {
          event.stopPropagation();
          onMinimize?.();
        }
      }}
    >
      <div className={styles.heading}>
        <div className={styles.assistantMark} aria-hidden="true"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M6 7h20v14H15l-7 5v-5H6zM11 12h10M11 16h6"/></svg></div>
        <div><h2 id={headingId}>{text.dialog}</h2><p>{text.intro}</p></div>
        {docked && <div className={styles.windowActions}>
          <button type="button" aria-label={text.minimize} onClick={onMinimize}>−</button>
          <button type="button" aria-label={text.close} onClick={onMinimize}>×</button>
        </div>}
      </div>
      <div className={styles.composer}>
        <div className={styles.top}>
          <Link className={styles.chip} href="/ai/workflows">
            <ChipIcon name="workflows" />
            {text.workflows}
          </Link>
          <Link className={styles.chip} href="/payment-scanner">
            <ChipIcon name="pay" />
            {text.smartPay}
          </Link>
          <Link className={styles.chip} href="/dashboard/seller">
            <ChipIcon name="creators" />
            {text.creators}
          </Link>
          <button
            type="button"
            className={`${styles.iconBtn} ${styles.expandBtn}`}
            data-testid={docked ? "dock-chat-fullscreen" : "home-chat-fullscreen"}
            aria-label={fullscreen ? text.collapse : text.expand}
            aria-pressed={fullscreen}
            title={fullscreen ? text.collapse : text.expand}
            onClick={() => { if (!docked) chat.setDockOpen(false); setFullscreen((open) => !open); }}
          >
            {fullscreen ? (
              <svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true">
                <path d="M5.5 2.5H3.5v2M10.5 2.5h2v2M5.5 13.5H3.5v-2M10.5 13.5h2v-2" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
              </svg>
            ) : (
              <svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true">
                <path d="M3 6V3h3M13 6V3h-3M3 10v3h3M13 10v3h-3" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
          </button>
        </div>
        {docked && messages.length === 0 && !loading && <div className={styles.dockWelcome}>
          <svg viewBox="0 0 40 38" aria-hidden="true"><path d="M4 32 19 6h6l13 26H28L20 17 11 32Z" fill="currentColor"/></svg>
          <strong>{text.dialog}</strong><p>{text.intro}</p>
        </div>}
        {messages.length > 0 || loading ? (
          <div className={styles.transcript} ref={transcriptRef} aria-live="polite">
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={`${styles.bubble} ${message.role === "user" ? styles.user : styles.assistant}`}>
                {message.content}
              </div>
            ))}
            {loading && <div className={`${styles.bubble} ${styles.assistant} ${styles.pending}`}>{text.thinking}</div>}
          </div>
        ) : null}
        <label className={styles.srOnly} htmlFor={inputId}>{text.placeholder}</label>
        <textarea
          id={inputId}
          ref={fieldRef}
          className={styles.field}
          data-testid={docked ? "dock-chat-input" : "home-chat-input"}
          rows={3}
          value={draft}
          placeholder={text.placeholder}
          disabled={loading || configured === false}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void sendMessage(draft);
            }
          }}
        />
        <div className={styles.toolbar}>
          <button type="button" className={styles.iconBtn} aria-label={text.newChat} title={text.newChat} onClick={resetChat}>
            <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
              <path d="M8 3.2v9.6M3.2 8h9.6" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
            </svg>
          </button>
          <span className={styles.newChatLabel}>{text.newChat}</span>
          <div className={styles.rightTools}>
            <div className={styles.chipWrap}>
              <button
                type="button"
                className={styles.modelBtn}
                data-testid={docked ? "dock-chat-model" : "home-chat-model"}
                aria-expanded={modelOpen}
                onPointerDown={(event) => event.stopPropagation()}
                onClick={() => setModelOpen((open) => !open)}
              >
                <span className={styles.modelLabel}>{label}</span>
                <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
                  <path d="M3 4.5 6 7.5 9 4.5" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
                </svg>
              </button>
              {modelOpen && (
                <div className={`${styles.menu} ${styles.menuRight}`} onPointerDown={(event) => event.stopPropagation()}>
                  <button type="button">{label}</button>
                  <p>{sessionModel ? text.pinnedHint : text.autoHint}</p>
                </div>
              )}
            </div>
            <button
              type="button"
              className={`${styles.iconBtn}${listening ? ` ${styles.listening}` : ""}`}
              aria-label={text.voice}
              aria-pressed={listening}
              title={text.voice}
              onClick={toggleVoice}
            >
              <svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true">
                <rect x="6" y="1.5" width="4" height="8" rx="2" fill="none" stroke="currentColor" strokeWidth="1.3" />
                <path d="M4 7.5a4 4 0 0 0 8 0M8 11.5V14" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
              </svg>
            </button>
            <button
              type="button"
              className={styles.send}
              data-testid={docked ? "dock-chat-send" : "home-chat-send"}
              aria-label={text.send}
              disabled={loading || configured === false || !draft.trim()}
              onClick={() => void sendMessage(draft)}
            >
              <svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true">
                <path d="M8 12.5V3.5M4.5 7 8 3.5 11.5 7" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
        </div>
      </div>
      <div className={styles.pills}>
        {[
          { mode: "howto" as const, label: text.howto, prompt: text.howtoPrompt, href: "/projects" },
          { mode: "workflows" as const, label: text.findWorkflow, prompt: text.workflowsPrompt, href: "/ai/workflows" },
          { mode: "earn" as const, label: text.earn, prompt: text.earnPrompt, href: "/creators" },
        ].map((item, index) => configured === false
          ? <Link key={item.mode} className={styles.pill} href={item.href}><span>0{index + 1}</span>{item.label}<span aria-hidden="true">↗</span></Link>
          : <button key={item.mode} type="button" className={styles.pill} aria-pressed={mode === item.mode} disabled={loading} onClick={() => applyStarter(item.mode, item.prompt)}><span>0{index + 1}</span>{item.label}<span aria-hidden="true">↗</span></button>)}
      </div>
      {configured === false && !error && <p className={styles.note} role="status"><span aria-hidden="true" />{text.unavailable}</p>}
      {error && <p className={styles.error} role="alert">{error}</p>}
    </section>
  );
}

function ChipIcon({ name }: { name: "workflows" | "pay" | "creators" }) {
  if (name === "workflows") {
    return (
      <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M3 4h4v3H3V4Zm6 5h4v3H9V9ZM5.5 7v2.5H9" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      </svg>
    );
  }
  if (name === "pay") {
    return (
      <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">
        <rect x="2.5" y="4" width="11" height="8" rx="1.4" fill="none" stroke="currentColor" strokeWidth="1.2" />
        <path d="M2.5 7h11" stroke="currentColor" strokeWidth="1.2" />
      </svg>
    );
  }
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">
      <circle cx="8" cy="5.2" r="2.2" fill="none" stroke="currentColor" strokeWidth="1.2" />
      <path d="M3.5 13c.8-2.2 2.4-3.3 4.5-3.3S11.7 10.8 12.5 13" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}
