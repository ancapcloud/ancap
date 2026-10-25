"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { getApiUrl } from "@/lib/api";
import { useLanguage } from "@/components/LanguageProvider";
import type { Language } from "@/locales/translations";
import styles from "./HomeChatDialog.module.css";

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

const copy: Record<Language, {
  placeholder: string;
  send: string;
  newChat: string;
  voice: string;
  auto: string;
  autoHint: string;
  pinnedHint: string;
  thinking: string;
  unavailable: string;
  limited: string;
  failed: string;
  noVoice: string;
  dialog: string;
  workflows: string;
  smartPay: string;
  creators: string;
  howto: string;
  findWorkflow: string;
  earn: string;
  howtoPrompt: string;
  workflowsPrompt: string;
  earnPrompt: string;
}> = {
  en: {
    placeholder: "Ask how ANCAP works, which workflow to buy, or how to earn",
    send: "Send",
    newChat: "New chat",
    voice: "Voice input",
    auto: "Free auto",
    autoHint: "A free OpenRouter model is chosen once and kept for this dialog.",
    pinnedHint: "This free model stays for the whole dialog. Start a new chat to pick another.",
    thinking: "Thinking…",
    unavailable: "The dialog is not available right now.",
    limited: "The free model is busy. Try again in a little while.",
    failed: "The reply did not come through. Try again.",
    noVoice: "Voice input is not available in this browser.",
    dialog: "Ask ANCAP",
    workflows: "Workflows",
    smartPay: "Smart Pay",
    creators: "Creators",
    howto: "How ANCAP works",
    findWorkflow: "Find a workflow",
    earn: "How to earn",
    howtoPrompt: "Explain how ANCAP works in simple terms: buying and selling defined AI workflow outputs with ACP.",
    workflowsPrompt: "Help me choose a workflow on ANCAP for my task. Ask what I need, then suggest where to look in the catalog.",
    earnPrompt: "How can I earn on ANCAP as a creator? What do I publish and where do paid runs settle?",
  },
  ru: {
    placeholder: "Спросите, как работает ANCAP, какой workflow купить или как зарабатывать",
    send: "Отправить",
    newChat: "Новый диалог",
    voice: "Голосовой ввод",
    auto: "Бесплатная",
    autoHint: "Бесплатная модель выбирается один раз и остаётся на весь диалог.",
    pinnedHint: "Эта бесплатная модель закреплена на весь диалог. Новый диалог — другая модель.",
    thinking: "Думаю…",
    unavailable: "Диалог сейчас недоступен.",
    limited: "Бесплатная модель занята. Попробуйте чуть позже.",
    failed: "Ответ не пришёл. Попробуйте ещё раз.",
    noVoice: "Голосовой ввод в этом браузере недоступен.",
    dialog: "Спросить ANCAP",
    workflows: "Workflows",
    smartPay: "Smart Pay",
    creators: "Авторам",
    howto: "Как работает ANCAP",
    findWorkflow: "Найти workflow",
    earn: "Как зарабатывать",
    howtoPrompt: "Объясни простыми словами, как работает ANCAP: покупка и продажа готовых AI workflow за ACP.",
    workflowsPrompt: "Помоги выбрать workflow на ANCAP под мою задачу. Уточни, что нужно, и куда смотреть в каталоге.",
    earnPrompt: "Как зарабатывать на ANCAP как автор? Что публиковать и как проходят оплаченные запуски?",
  },
  uk: {
    placeholder: "Запитайте, як працює ANCAP, який workflow купити або як заробляти",
    send: "Надіслати",
    newChat: "Новий діалог",
    voice: "Голосове введення",
    auto: "Безкоштовна",
    autoHint: "Безкоштовну модель обирають один раз і тримають на весь діалог.",
    pinnedHint: "Ця безкоштовна модель закріплена на весь діалог. Новий діалог — інша модель.",
    thinking: "Думаю…",
    unavailable: "Діалог зараз недоступний.",
    limited: "Безкоштовна модель зайнята. Спробуйте трохи пізніше.",
    failed: "Відповідь не надійшла. Спробуйте ще раз.",
    noVoice: "Голосове введення в цьому браузері недоступне.",
    dialog: "Запитати ANCAP",
    workflows: "Workflows",
    smartPay: "Smart Pay",
    creators: "Авторам",
    howto: "Як працює ANCAP",
    findWorkflow: "Знайти workflow",
    earn: "Як заробляти",
    howtoPrompt: "Поясни простими словами, як працює ANCAP: купівля і продаж готових AI workflow за ACP.",
    workflowsPrompt: "Допоможи обрати workflow на ANCAP під мою задачу. Уточни потребу і куди дивитися в каталозі.",
    earnPrompt: "Як заробляти на ANCAP як автор? Що публікувати і як проходять оплачені запуски?",
  },
  de: {
    placeholder: "Fragen Sie, wie ANCAP funktioniert, welchen Workflow Sie kaufen oder wie Sie verdienen",
    send: "Senden",
    newChat: "Neuer Chat",
    voice: "Spracheingabe",
    auto: "Kostenlos",
    autoHint: "Ein kostenloses Modell wird einmal gewählt und bleibt für diesen Dialog.",
    pinnedHint: "Dieses kostenlose Modell bleibt für den ganzen Dialog. Neuer Chat = neues Modell.",
    thinking: "Denkt nach…",
    unavailable: "Der Dialog ist gerade nicht verfügbar.",
    limited: "Das kostenlose Modell ist ausgelastet. Bitte später erneut versuchen.",
    failed: "Die Antwort ist nicht angekommen. Bitte erneut versuchen.",
    noVoice: "Spracheingabe ist in diesem Browser nicht verfügbar.",
    dialog: "ANCAP fragen",
    workflows: "Workflows",
    smartPay: "Smart Pay",
    creators: "Creator",
    howto: "So funktioniert ANCAP",
    findWorkflow: "Workflow finden",
    earn: "Verdienen",
    howtoPrompt: "Erkläre einfach, wie ANCAP funktioniert: Kauf und Verkauf definierter AI-Workflow-Ergebnisse mit ACP.",
    workflowsPrompt: "Hilf mir, einen Workflow auf ANCAP für meine Aufgabe zu finden. Frage nach dem Bedarf und zeige den Katalog.",
    earnPrompt: "Wie verdiene ich auf ANCAP als Creator? Was veröffentliche ich und wie laufen bezahlte Runs?",
  },
  "zh-Hant": {
    placeholder: "詢問 ANCAP 如何運作、該買哪個 workflow，或如何賺取",
    send: "送出",
    newChat: "新對話",
    voice: "語音輸入",
    auto: "免費",
    autoHint: "免費模型只會選一次，並在這個對話中保持不變。",
    pinnedHint: "這個免費模型會固定用於整段對話。開新對話才會換模型。",
    thinking: "思考中…",
    unavailable: "對話目前無法使用。",
    limited: "免費模型忙碌中，請稍後再試。",
    failed: "沒有收到回覆，請再試一次。",
    noVoice: "這個瀏覽器無法使用語音輸入。",
    dialog: "詢問 ANCAP",
    workflows: "Workflows",
    smartPay: "Smart Pay",
    creators: "創作者",
    howto: "ANCAP 如何運作",
    findWorkflow: "找 workflow",
    earn: "如何賺取",
    howtoPrompt: "用簡單說明解釋 ANCAP：如何用 ACP 買賣已定義的 AI workflow 產出。",
    workflowsPrompt: "幫我在 ANCAP 依需求選 workflow，並指出目錄該怎麼看。",
    earnPrompt: "作為創作者如何在 ANCAP 賺錢？要發布什麼，付費執行怎麼結算？",
  },
};

export function HomeChatDialog() {
  const { lang } = useLanguage();
  const text = copy[lang] ?? copy.en;
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<{ role: Role; content: string }[]>([]);
  const [mode, setMode] = useState<Mode>("chat");
  const [sessionModel, setSessionModel] = useState<string | null>(null);
  const [label, setLabel] = useState(text.auto);
  const [modelOpen, setModelOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [error, setError] = useState("");
  const fieldRef = useRef<HTMLTextAreaElement>(null);
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
    if (!modelOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setModelOpen(false);
    };
    const onPointer = () => setModelOpen(false);
    window.addEventListener("keydown", onKey);
    window.addEventListener("pointerdown", onPointer);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("pointerdown", onPointer);
    };
  }, [modelOpen]);

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
    <section className={styles.root} id="ask" data-testid="home-chat">
      <h2 className={styles.srOnly}>{text.dialog}</h2>
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
        <button type="button" className={styles.pill} aria-pressed={mode === "howto"} disabled={loading} onClick={() => applyStarter("howto", text.howtoPrompt)}>{text.howto}</button>
        <button type="button" className={styles.pill} aria-pressed={mode === "workflows"} disabled={loading} onClick={() => applyStarter("workflows", text.workflowsPrompt)}>{text.findWorkflow}</button>
        <button type="button" className={styles.pill} aria-pressed={mode === "earn"} disabled={loading} onClick={() => applyStarter("earn", text.earnPrompt)}>{text.earn}</button>
      </div>
      {configured === false && !error && <p className={styles.note}>{text.unavailable}</p>}
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
