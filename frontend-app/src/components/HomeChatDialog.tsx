"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { getApiUrl } from "@/lib/api";
import { useLanguage } from "@/components/LanguageProvider";
import type { Language } from "@/locales/translations";
import styles from "./HomeChatDialog.module.css";
import { homeChatByLang } from "@/locales/homeChat";

type Role = "user" | "assistant";
type Mode = "chat" | "howto" | "workflows" | "earn";
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



export function HomeChatDialog() {
  const { lang } = useLanguage();
  const text = homeChatByLang[lang];
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<{ role: Role; content: string }[]>([]);
  const [mode, setMode] = useState<Mode>("chat");
  const [sessionModel, setSessionModel] = useState<string | null>(null);
  const [label, setLabel] = useState(text.auto);
  const [modelOpen, setModelOpen] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [error, setError] = useState("");
  const fieldRef = useRef<HTMLTextAreaElement>(null);
  const rootRef = useRef<HTMLElement>(null);
  const recognitionRef = useRef<SpeechRec | null>(null);
  const transcriptRef = useRef<HTMLDivElement>(null);
  const sessionModelRef = useRef<string | null>(null);

  useEffect(() => {
    sessionModelRef.current = sessionModel;
  }, [sessionModel]);

  useEffect(() => {
    if (!sessionModel) setLabel(text.auto);
  }, [text.auto, sessionModel]);

  useEffect(() => {
    let cancelled = false;
    fetch(`${getApiUrl()}/home-chat/status`, { headers: { "X-Requested-With": "XMLHttpRequest" } })
      .then((response) => response.json())
      .then((body) => {
        if (!cancelled) setConfigured(Boolean(body?.configured));
      })
      .catch(() => {
        if (!cancelled) setConfigured(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

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
    setMessages([]);
    setDraft("");
    setMode("chat");
    setSessionModel(null);
    sessionModelRef.current = null;
    setError("");
    setLabel(text.auto);
    setModelOpen(false);
    fieldRef.current?.focus();
  }

  async function sendMessage(raw: string, nextMode: Mode = mode) {
    const content = raw.trim();
    if (!content || loading) return;
    stopVoice();
    const history = [...messages, { role: "user" as const, content }];
    setMessages(history);
    setDraft("");
    setError("");
    setLoading(true);
    setModelOpen(false);
    setMode(nextMode);
    try {
      const response = await fetch(`${getApiUrl()}/home-chat/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" },
        body: JSON.stringify({
          messages: history.slice(-8),
          mode: nextMode,
          lang,
          session_model: sessionModelRef.current || undefined,
        }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        const code = body?.detail?.code as string | undefined;
        setMessages(messages);
        setDraft(content);
        if (response.status === 429 || code === "RATE_LIMITED") setError(text.limited);
        else if (response.status === 503 || code === "NOT_CONFIGURED" || code === "DISABLED") {
          setConfigured(false);
          setError(text.unavailable);
        } else setError(text.failed);
        return;
      }
      const reply = String(body.reply || "").trim();
      if (!reply) {
        setMessages(messages);
        setDraft(content);
        setError(text.failed);
        return;
      }
      setMessages([...history, { role: "assistant", content: reply }]);
      const nextModel = String(body.model || "").trim();
      if (nextModel.toLowerCase().endsWith(":free")) {
        setSessionModel(nextModel);
        sessionModelRef.current = nextModel;
      }
      if (body.label) setLabel(String(body.label));
    } catch {
      setMessages(messages);
      setDraft(content);
      setError(text.failed);
    } finally {
      setLoading(false);
    }
  }

  function applyStarter(nextMode: Mode, prompt: string) {
    setMode(nextMode);
    void sendMessage(prompt, nextMode);
  }

  return (
    <section
      ref={rootRef}
      className={`${styles.root}${fullscreen ? ` ${styles.fullscreen}` : ""}`}
      id="ask"
      data-testid="home-chat"
      data-fullscreen={fullscreen ? "true" : "false"}
      aria-labelledby="home-chat-title"
      role={fullscreen ? "dialog" : undefined}
      aria-modal={fullscreen || undefined}
      tabIndex={fullscreen ? -1 : undefined}
    >
      <div className={styles.heading}>
        <div className={styles.assistantMark} aria-hidden="true"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M6 7h20v14H15l-7 5v-5H6zM11 12h10M11 16h6"/></svg></div>
        <div><h2 id="home-chat-title">{text.dialog}</h2><p>{text.intro}</p></div>
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
            data-testid="home-chat-fullscreen"
            aria-label={fullscreen ? text.collapse : text.expand}
            aria-pressed={fullscreen}
            title={fullscreen ? text.collapse : text.expand}
            onClick={() => setFullscreen((open) => !open)}
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
        <label className={styles.srOnly} htmlFor="home-chat-input">{text.placeholder}</label>
        <textarea
          id="home-chat-input"
          ref={fieldRef}
          className={styles.field}
          data-testid="home-chat-input"
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
                data-testid="home-chat-model"
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
              data-testid="home-chat-send"
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
