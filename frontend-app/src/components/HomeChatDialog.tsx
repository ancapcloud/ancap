"use client";

import { useEffect, useRef, useState } from "react";
import { getApiUrl } from "@/lib/api";
import { useLanguage } from "@/components/LanguageProvider";
import type { Language } from "@/locales/translations";
import styles from "./HomeChatDialog.module.css";

type Role = "user" | "assistant";
type Mode = "chat" | "plan" | "multitask" | "cloud";
type Menu = "project" | "page" | "device" | "model";
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

const copy: Record<Language, {
  placeholder: string;
  send: string;
  newChat: string;
  voice: string;
  project: string;
  page: string;
  device: string;
  auto: string;
  autoHint: string;
  thinking: string;
  unavailable: string;
  limited: string;
  failed: string;
  noVoice: string;
  dialog: string;
}> = {
  en: {
    placeholder: "Message ANCAP",
    send: "Send",
    newChat: "New chat",
    voice: "Voice input",
    project: "ancap.cloud",
    page: "home",
    device: "This browser",
    auto: "Free auto",
    autoHint: "A free OpenRouter model is chosen automatically.",
    thinking: "Thinking…",
    unavailable: "The dialog is not available right now.",
    limited: "The free model is busy. Try again in a little while.",
    failed: "The reply did not come through. Try again.",
    noVoice: "Voice input is not available in this browser.",
    dialog: "Ask ANCAP",
  },
  ru: {
    placeholder: "Напишите ANCAP",
    send: "Отправить",
    newChat: "Новый диалог",
    voice: "Голосовой ввод",
    project: "ancap.cloud",
    page: "главная",
    device: "Этот браузер",
    auto: "Бесплатная",
    autoHint: "Бесплатная модель OpenRouter выбирается автоматически.",
    thinking: "Думаю…",
    unavailable: "Диалог сейчас недоступен.",
    limited: "Бесплатная модель занята. Попробуйте чуть позже.",
    failed: "Ответ не пришёл. Попробуйте ещё раз.",
    noVoice: "Голосовой ввод в этом браузере недоступен.",
    dialog: "Спросить ANCAP",
  },
  uk: {
    placeholder: "Напишіть ANCAP",
    send: "Надіслати",
    newChat: "Новий діалог",
    voice: "Голосове введення",
    project: "ancap.cloud",
    page: "головна",
    device: "Цей браузер",
    auto: "Безкоштовна",
    autoHint: "Безкоштовну модель OpenRouter вибрано автоматично.",
    thinking: "Думаю…",
    unavailable: "Діалог зараз недоступний.",
    limited: "Безкоштовна модель зайнята. Спробуйте трохи пізніше.",
    failed: "Відповідь не надійшла. Спробуйте ще раз.",
    noVoice: "Голосове введення в цьому браузері недоступне.",
    dialog: "Запитати ANCAP",
  },
  de: {
    placeholder: "Nachricht an ANCAP",
    send: "Senden",
    newChat: "Neuer Chat",
    voice: "Spracheingabe",
    project: "ancap.cloud",
    page: "Startseite",
    device: "Dieser Browser",
    auto: "Kostenlos",
    autoHint: "Ein kostenloses OpenRouter-Modell wird automatisch gewählt.",
    thinking: "Denkt nach…",
    unavailable: "Der Dialog ist gerade nicht verfügbar.",
    limited: "Das kostenlose Modell ist ausgelastet. Bitte später erneut versuchen.",
    failed: "Die Antwort ist nicht angekommen. Bitte erneut versuchen.",
    noVoice: "Spracheingabe ist in diesem Browser nicht verfügbar.",
    dialog: "ANCAP fragen",
  },
  "zh-Hant": {
    placeholder: "傳訊息給 ANCAP",
    send: "送出",
    newChat: "新對話",
    voice: "語音輸入",
    project: "ancap.cloud",
    page: "首頁",
    device: "這個瀏覽器",
    auto: "免費",
    autoHint: "系統會自動選擇 OpenRouter 的免費模型。",
    thinking: "思考中…",
    unavailable: "對話目前無法使用。",
    limited: "免費模型忙碌中，請稍後再試。",
    failed: "沒有收到回覆，請再試一次。",
    noVoice: "這個瀏覽器無法使用語音輸入。",
    dialog: "詢問 ANCAP",
  },
};

function IconChevron() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
      <path d="M3 4.5 6 7.5 9 4.5" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

export function HomeChatDialog() {
  const { lang } = useLanguage();
  const text = copy[lang] ?? copy.en;
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<{ role: Role; content: string }[]>([]);
  const [mode, setMode] = useState<Mode>("chat");
  const [label, setLabel] = useState(text.auto);
  const [menu, setMenu] = useState<Menu | null>(null);
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [error, setError] = useState("");
  const fieldRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<SpeechRec | null>(null);
  const transcriptRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLabel((current) => (current === copy.en.auto || current === copy.ru.auto || current === copy.uk.auto || current === copy.de.auto || current === copy["zh-Hant"].auto ? text.auto : current));
  }, [text.auto]);

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
    if (!menu) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMenu(null);
    };
    const onPointer = () => setMenu(null);
    window.addEventListener("keydown", onKey);
    window.addEventListener("pointerdown", onPointer);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("pointerdown", onPointer);
    };
  }, [menu]);

  useEffect(() => {
    const node = transcriptRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [messages, loading]);

  useEffect(() => () => recognitionRef.current?.stop(), []);

  function toggleMenu(next: Menu) {
    setMenu((current) => (current === next ? null : next));
  }

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
    setError("");
    setLabel(text.auto);
    fieldRef.current?.focus();
  }

  async function send() {
    const content = draft.trim();
    if (!content || loading) return;
    stopVoice();
    const history = [...messages, { role: "user" as const, content }];
    setMessages(history);
    setDraft("");
    setError("");
    setLoading(true);
    setMenu(null);
    try {
      const response = await fetch(`${getApiUrl()}/home-chat/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" },
        body: JSON.stringify({
          messages: history.slice(-8),
          mode,
          lang,
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
      if (body.label) setLabel(String(body.label));
    } catch {
      setMessages(messages);
      setDraft(content);
      setError(text.failed);
    } finally {
      setLoading(false);
    }
  }

  function pickMode(next: Mode) {
    setMode((current) => (current === next ? "chat" : next));
    fieldRef.current?.focus();
  }

  const chips: { id: Menu; label: string; icon: "project" | "page" | "device" }[] = [
    { id: "project", label: text.project, icon: "project" },
    { id: "page", label: text.page, icon: "page" },
    { id: "device", label: text.device, icon: "device" },
  ];

  return (
    <section className={styles.root} id="ask" data-testid="home-chat" onPointerDown={() => menu && setMenu(null)}>
      <h2 className={styles.srOnly}>{text.dialog}</h2>
      <div className={styles.composer}>
        <div className={styles.top}>
          {chips.map((chip) => (
            <div className={styles.chipWrap} key={chip.id}>
              <button
                type="button"
                className={styles.chip}
                aria-expanded={menu === chip.id}
                onPointerDown={(event) => event.stopPropagation()}
                onClick={() => toggleMenu(chip.id)}
              >
                <ChipIcon name={chip.icon} />
                {chip.label}
                <IconChevron />
              </button>
              {menu === chip.id && (
                <div className={styles.menu} onPointerDown={(event) => event.stopPropagation()}>
                  <button type="button">{chip.label}</button>
                </div>
              )}
            </div>
          ))}
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
          disabled={loading}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void send();
            }
          }}
        />
        <div className={styles.toolbar}>
          <button type="button" className={styles.iconBtn} aria-label={text.newChat} title={text.newChat} onClick={resetChat}>
            <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
              <path d="M8 3.2v9.6M3.2 8h9.6" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
            </svg>
          </button>
          <div className={styles.rightTools}>
            <div className={styles.chipWrap}>
              <button
                type="button"
                className={styles.modelBtn}
                data-testid="home-chat-model"
                aria-expanded={menu === "model"}
                onPointerDown={(event) => event.stopPropagation()}
                onClick={() => toggleMenu("model")}
              >
                <span className={styles.modelLabel}>{label}</span>
                <IconChevron />
              </button>
              {menu === "model" && (
                <div className={`${styles.menu} ${styles.menuRight}`} onPointerDown={(event) => event.stopPropagation()}>
                  <button type="button">{label}</button>
                  <p>{text.autoHint}</p>
                </div>
              )}
            </div>
            <button
              type="button"
              className={styles.iconBtn}
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
              disabled={loading || !draft.trim()}
              onClick={() => void send()}
            >
              <svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true">
                <path d="M8 12.5V3.5M4.5 7 8 3.5 11.5 7" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
        </div>
      </div>
      <div className={styles.pills}>
        <button type="button" className={styles.pill} aria-pressed={mode === "plan"} onClick={() => pickMode("plan")}>Plan New Idea</button>
        <button type="button" className={styles.pill} aria-pressed={mode === "multitask"} onClick={() => pickMode("multitask")}>Multitask</button>
        <button type="button" className={styles.pill} aria-pressed={mode === "cloud"} onClick={() => pickMode("cloud")}>Run in Cloud</button>
      </div>
      {configured === false && !error && <p className={styles.note}>{text.unavailable}</p>}
      {error && <p className={styles.error} role="alert">{error}</p>}
    </section>
  );
}

function ChipIcon({ name }: { name: "project" | "page" | "device" }) {
  if (name === "project") {
    return (
      <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M2 4.5h4l1.2 1.5H14V12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V4.5Z" fill="none" stroke="currentColor" strokeWidth="1.2" />
      </svg>
    );
  }
  if (name === "page") {
    return (
      <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">
        <circle cx="5" cy="8" r="1.6" fill="none" stroke="currentColor" strokeWidth="1.2" />
        <path d="M6.6 8h6M10.2 5.6 12.6 8l-2.4 2.4" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      </svg>
    );
  }
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">
      <rect x="2" y="3" width="12" height="8" rx="1.2" fill="none" stroke="currentColor" strokeWidth="1.2" />
      <path d="M6 13.2h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}
