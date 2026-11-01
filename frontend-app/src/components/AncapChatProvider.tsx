"use client";

import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from "react";
import { getApiUrl } from "@/lib/api";
import { homeChatByLang } from "@/locales/homeChat";
import { useLanguage } from "./LanguageProvider";

export type ChatMode = "chat" | "howto" | "workflows" | "earn";
type Message = { role: "user" | "assistant"; content: string };

function useChatState() {
  const { lang } = useLanguage();
  const text = homeChatByLang[lang];
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [mode, setMode] = useState<ChatMode>("chat");
  const [sessionModel, setSessionModel] = useState<string | null>(null);
  const [modelLabel, setModelLabel] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [error, setError] = useState("");
  const [dockOpen, setDockOpen] = useState(false);
  const statusRequest = useRef<Promise<void> | null>(null);
  const requestRef = useRef<AbortController | null>(null);
  const generation = useRef(0);

  const ensureStatus = useCallback(() => {
    if (!statusRequest.current) {
      statusRequest.current = fetch(`${getApiUrl()}/home-chat/status`, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(response => response.json())
        .then(body => setConfigured(Boolean(body?.configured)))
        .catch(() => setConfigured(false));
    }
    return statusRequest.current;
  }, []);

  function resetChat() {
    generation.current += 1;
    requestRef.current?.abort();
    requestRef.current = null;
    setMessages([]);
    setDraft("");
    setMode("chat");
    setSessionModel(null);
    setModelLabel(null);
    setError("");
    setLoading(false);
  }

  async function sendMessage(raw: string, nextMode: ChatMode = mode) {
    const content = raw.trim();
    if (!content || requestRef.current || configured === false) return;
    const controller = new AbortController();
    requestRef.current = controller;
    const version = generation.current;
    const history: Message[] = [...messages, { role: "user", content }];
    setMessages(history);
    setDraft("");
    setError("");
    setLoading(true);
    setMode(nextMode);
    try {
      const response = await fetch(`${getApiUrl()}/home-chat/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" },
        signal: controller.signal,
        body: JSON.stringify({ messages: history.slice(-8), mode: nextMode, lang, session_model: sessionModel || undefined }),
      });
      const body = await response.json().catch(() => ({}));
      if (generation.current !== version) return;
      if (!response.ok) {
        setMessages(messages);
        setDraft(content);
        const code = body?.detail?.code;
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
      if (nextModel.toLowerCase().endsWith(":free")) setSessionModel(nextModel);
      if (body.label) setModelLabel(String(body.label));
    } catch {
      if (generation.current !== version) return;
      setMessages(messages);
      setDraft(content);
      setError(text.failed);
    } finally {
      if (generation.current === version) {
        requestRef.current = null;
        setLoading(false);
      }
    }
  }

  return { draft, setDraft, messages, mode, setMode, sessionModel, label: modelLabel || text.auto, loading, configured, error, setError, ensureStatus, sendMessage, resetChat, dockOpen, setDockOpen };
}

const ChatContext = createContext<ReturnType<typeof useChatState> | null>(null);

export function AncapChatProvider({ children }: { children: ReactNode }) {
  const chat = useChatState();
  return <ChatContext.Provider value={chat}>{children}</ChatContext.Provider>;
}

export function useAncapChat() {
  const chat = useContext(ChatContext);
  if (!chat) throw new Error("Ask ANCAP requires AncapChatProvider");
  return chat;
}
