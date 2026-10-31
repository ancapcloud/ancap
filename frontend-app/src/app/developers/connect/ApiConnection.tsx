"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Navigation } from "@/components/Navigation";
import { useAuth } from "@/components/AuthProvider";
import { useLanguage } from "@/components/LanguageProvider";
import { agents, apiFetch } from "@/lib/api";

const labels = {
  en: ["Connect to ANCAP API", "Create a key, save it locally and send your first request.", "Sign in to create an API key", "Choose your agent", "Register an agent", "Create API key", "Save this key now. It is shown only once. Keep it out of chats and source control.", "Copy key", "Copied", "Connection examples", "Store ANCAP_API_KEY in your local environment. The examples use a placeholder, never your actual key.", "This example runs a paid check and debits your balance. Check current prices before running it.", "Loading…", "No agents yet. Register one, then return here.", "Could not complete the request. Please try again.", "Select and copy the key manually.", "API base URL", "API usage", "Choose an agent", "Refresh agents", "Hide key"],
  ru: ["Подключение к API ANCAP", "Создайте ключ, сохраните его локально и отправьте первый запрос.", "Войти для создания API-ключа", "Выберите своего агента", "Зарегистрировать агента", "Создать API-ключ", "Сохраните ключ сейчас: он показывается только один раз. Не отправляйте его в чаты и не добавляйте в репозиторий.", "Скопировать ключ", "Скопировано", "Примеры подключения", "Сохраните ANCAP_API_KEY в локальном окружении. В примерах используется переменная, а не ваш ключ.", "Пример запускает платную проверку со списанием баланса. Перед запуском проверьте актуальную цену.", "Загрузка…", "Агентов пока нет. Зарегистрируйте агента и вернитесь сюда.", "Не удалось выполнить запрос. Попробуйте ещё раз.", "Выделите и скопируйте ключ вручную.", "Базовый URL API", "Использование API", "Выберите агента", "Обновить список", "Скрыть ключ"],
  uk: ["Підключення до API ANCAP", "Створіть ключ, збережіть локально й надішліть перший запит.", "Увійти для створення API-ключа", "Виберіть свого агента", "Зареєструвати агента", "Створити API-ключ", "Збережіть ключ зараз: він показується лише один раз. Не надсилайте його в чати й не додавайте до репозиторію.", "Скопіювати ключ", "Скопійовано", "Приклади підключення", "Збережіть ANCAP_API_KEY у локальному середовищі. Приклади використовують змінну, а не ваш ключ.", "Приклад запускає платну перевірку зі списанням балансу. Перед запуском перевірте ціну.", "Завантаження…", "Агентів поки немає. Зареєструйте агента й поверніться сюди.", "Не вдалося виконати запит. Спробуйте ще раз.", "Виділіть і скопіюйте ключ вручну.", "Базова URL API", "Використання API", "Виберіть агента", "Оновити список", "Приховати ключ"],
  de: ["Mit der ANCAP API verbinden", "Schlüssel erstellen, lokal speichern und die erste Anfrage senden.", "Zum Erstellen eines API-Schlüssels anmelden", "Eigenen Agenten auswählen", "Agent registrieren", "API-Schlüssel erstellen", "Jetzt speichern: Der Schlüssel wird nur einmal angezeigt. Nicht in Chats oder im Repository speichern.", "Schlüssel kopieren", "Kopiert", "Verbindungsbeispiele", "ANCAP_API_KEY lokal als Umgebungsvariable speichern. Beispiele verwenden eine Variable statt deines Schlüssels.", "Dieses Beispiel führt eine kostenpflichtige Prüfung aus. Vorher den aktuellen Preis prüfen.", "Laden…", "Noch keine Agenten. Agent registrieren und hierher zurückkehren.", "Anfrage fehlgeschlagen. Bitte erneut versuchen.", "Schlüssel markieren und manuell kopieren.", "API-Basis-URL", "API-Nutzung", "Agent auswählen", "Agenten aktualisieren", "Schlüssel ausblenden"],
  "zh-Hant": ["連接 ANCAP API", "建立金鑰、儲存在本機並傳送第一個請求。", "登入以建立 API 金鑰", "選擇你的代理", "註冊代理", "建立 API 金鑰", "請立即儲存：金鑰僅顯示一次。請勿貼到對話或提交到程式碼庫。", "複製金鑰", "已複製", "連接範例", "將 ANCAP_API_KEY 設為本機環境變數。範例使用變數，不會顯示你的金鑰。", "此範例會執行付費檢查並扣除餘額。執行前請確認最新價格。", "載入中…", "尚無代理。請先註冊代理後返回。", "請求失敗，請再試一次。", "請選取並手動複製金鑰。", "API 基本網址", "API 使用紀錄", "選擇代理", "重新整理代理", "隱藏金鑰"],
};

const curl = `curl -X POST https://api.ancap.cloud/v1/paid-api/token-risk \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: $ANCAP_API_KEY" \\
  -d '{"subject":"TOKEN","chain":"Base","signals":{}}'`;
const python = `import json, os, urllib.request

request = urllib.request.Request(
    "https://api.ancap.cloud/v1/paid-api/token-risk",
    data=json.dumps({"subject": "TOKEN", "chain": "Base", "signals": {}}).encode(),
    headers={"Content-Type": "application/json",
             "X-API-Key": os.environ["ANCAP_API_KEY"]},
    method="POST",
)
with urllib.request.urlopen(request, timeout=30) as response:
    print(json.load(response))`;

export function ApiConnection() {
  const { lang } = useLanguage();
  const c = labels[lang];
  const { isAuthenticated, isLoading } = useAuth();
  const [items, setItems] = useState<{ id: string; display_name: string }[]>([]);
  const [agentId, setAgentId] = useState("");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [key, setKey] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  async function loadAgents() {
    setLoading(true); setError("");
    try {
      const data = await agents.listMine(200);
      setItems(data.items || []);
    } catch { setError(c[14]); }
    finally { setLoading(false); }
  }
  useEffect(() => {
    if (!isLoading && isAuthenticated) void loadAgents();
    if (!isAuthenticated) { setItems([]); setAgentId(""); setKey(""); }
    // Fetch only when authentication changes; language changes do not reload secrets.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, isLoading]);
  async function createKey(event: React.FormEvent) {
    event.preventDefault();
    if (!agentId || busy || key) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const result = await apiFetch("/keys", { method: "POST", body: JSON.stringify({ agent_id: agentId }) });
      setKey(result.key);
    } catch { setError(c[14]); }
    finally { setBusy(false); }
  }
  return <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
    <Navigation />
    <main className="mx-auto max-w-4xl px-4 py-10">
      <Link href="/developers" className="text-sm text-emerald-300">← Developers</Link>
      <h1 className="mt-5 text-3xl font-semibold sm:text-5xl">{c[0]}</h1>
      <p className="mt-4 text-[var(--text-secondary)]">{c[1]}</p>
      <section className="my-8 rounded-3xl border border-emerald-400/20 bg-emerald-400/[0.06] p-6">
        <h2 className="text-xl font-semibold">1. {c[5]}</h2>
        {isLoading ? <p className="mt-4">{c[12]}</p> : !isAuthenticated ? <Link href="/login" className="btn btn-primary mt-4">{c[2]}</Link> : <>
          <form onSubmit={createKey} className="mt-4 grid gap-4">
            <label htmlFor="api-agent">{c[3]}</label>
            <select id="api-agent" value={agentId} onChange={e => setAgentId(e.target.value)} disabled={loading || busy || !!key} className="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-3" required>
              <option value="">{c[18]}</option>
              {items.map(agent => <option key={agent.id} value={agent.id}>{agent.display_name}</option>)}
            </select>
            {loading ? <p>{c[12]}</p> : !items.length && !error ? <p>{c[13]}</p> : null}
            <div className="flex flex-wrap gap-3">
              <button className="btn btn-primary" disabled={!agentId || loading || busy || !!key}>{busy ? c[12] : c[5]}</button>
              <Link href="/agents" className="btn btn-ghost">{c[4]}</Link>
              <button type="button" className="btn btn-ghost" disabled={loading || busy} onClick={() => void loadAgents()}>{c[19]}</button>
            </div>
          </form>
          {key && <div className="mt-6 rounded-xl border border-emerald-400/30 p-4">
            <p>{c[6]}</p>
            <code className="my-4 block break-all select-all">{key}</code>
            <button className="btn btn-primary" onClick={async () => { try { await navigator.clipboard.writeText(key); setNotice(c[8]); } catch { setNotice(c[15]); } }}>{c[7]}</button>
            <button className="btn btn-ghost" onClick={() => { setKey(""); setNotice(""); }}>{c[20]}</button>
          </div>}
        </>}
        {error && <p role="alert" className="mt-4 text-red-300">{error}</p>}
        <p role="status" className="mt-3 text-sm">{notice}</p>
      </section>
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">2. {c[9]}</h2>
        <p>{c[10]}</p>
        <p className="text-sm text-[var(--text-secondary)]">{c[16]}: <code>https://api.ancap.cloud/v1</code></p>
        <p className="rounded-xl border border-amber-300/20 p-4 text-sm">{c[11]} <Link href="/developers" className="underline">API</Link></p>
        {[['curl · Bash / zsh', curl], ['Python', python]].map(([title, code]) => <article key={title} className="rounded-2xl border border-[var(--border)] p-5"><h3 className="font-semibold">{title}</h3><pre className="mt-4 overflow-x-auto text-sm"><code>{code}</code></pre></article>)}
        <div className="flex gap-5"><Link href="/developers/usage" className="text-emerald-300">{c[17]} →</Link><Link href="/mcp" className="text-emerald-300">MCP →</Link></div>
      </section>
    </main>
  </div>;
}
