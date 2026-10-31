"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Navigation } from "@/components/Navigation";
import { useAuth } from "@/components/AuthProvider";
import { useLanguage } from "@/components/LanguageProvider";
import { apiFetch } from "@/lib/api";

const messages = {
  en: { title: "One API key for your ANCAP account", lead: "Connect your app or AI without selecting an agent. Account permissions and balances still apply.", login: "Sign in to manage your API key", create: "Create API key", rotate: "Replace key", remove: "Delete key", refresh: "Refresh statistics", save: "Save this key now. It is shown only once. Never share it in chats or commit it to source control.", copy: "Copy key", copied: "Copied", manual: "Select and copy the key manually.", hide: "Hide key", active: "Active key", inactive: "No active key", requests: "Requests", success: "Successful", failed: "Failed", last: "Last used", created: "Created", history: "Statistics include this account key and its previous versions. Replacing or deleting the key preserves history.", examples: "Test your connection", environment: "Set ANCAP_API_KEY in your local environment. These examples read your profile without starting a paid workflow.", scope: "Your ownership checks, spending rules, operator permissions and wallet-signature requirements remain in force.", rotation: "Replace this key? The current key will stop working immediately. Save the replacement and update your integrations.", deletion: "Delete this key? Integrations will lose access immediately. You can create a new key later.", confirm: "Confirm", cancel: "Cancel", loading: "Loading…", error: "Request failed. Refresh and try again.", usage: "Paid API usage" },
  ru: { title: "Один API-ключ для аккаунта ANCAP", lead: "Подключайте приложение или ИИ без выбора агента. Действуют права и баланс вашего аккаунта.", login: "Войти для управления API-ключом", create: "Создать API-ключ", rotate: "Заменить ключ", remove: "Удалить ключ", refresh: "Обновить статистику", save: "Сохраните ключ сейчас: он показывается только один раз. Не отправляйте его в чаты и не добавляйте в репозиторий.", copy: "Скопировать ключ", copied: "Скопировано", manual: "Выделите и скопируйте ключ вручную.", hide: "Скрыть ключ", active: "Активный ключ", inactive: "Нет активного ключа", requests: "Запросы", success: "Успешные", failed: "Ошибки", last: "Последнее использование", created: "Создан", history: "Статистика учитывает ключ аккаунта и его предыдущие версии. Замена и удаление сохраняют историю.", examples: "Проверьте подключение", environment: "Задайте ANCAP_API_KEY в локальном окружении. Примеры читают ваш профиль без запуска платных процессов.", scope: "Проверки владельца, лимиты расходов, права оператора и требования подписи кошелька сохраняются.", rotation: "Заменить ключ? Текущий ключ сразу перестанет работать. Сохраните новый и обновите интеграции.", deletion: "Удалить ключ? Интеграции сразу потеряют доступ. Позже можно создать новый.", confirm: "Подтвердить", cancel: "Отмена", loading: "Загрузка…", error: "Запрос не выполнен. Обновите данные и повторите.", usage: "Расходы платного API" },
  uk: { title: "Один API-ключ для акаунта ANCAP", lead: "Підключайте застосунок або ШІ без вибору агента. Діють права й баланс вашого акаунта.", login: "Увійти для керування API-ключем", create: "Створити API-ключ", rotate: "Замінити ключ", remove: "Видалити ключ", refresh: "Оновити статистику", save: "Збережіть ключ зараз: він показується лише один раз. Не надсилайте його в чати й не додавайте до репозиторію.", copy: "Скопіювати ключ", copied: "Скопійовано", manual: "Виділіть і скопіюйте ключ вручну.", hide: "Приховати ключ", active: "Активний ключ", inactive: "Немає активного ключа", requests: "Запити", success: "Успішні", failed: "Помилки", last: "Останнє використання", created: "Створено", history: "Статистика враховує ключ акаунта та попередні версії. Заміна й видалення зберігають історію.", examples: "Перевірте підключення", environment: "Задайте ANCAP_API_KEY у локальному середовищі. Приклади читають профіль без платних запусків.", scope: "Перевірки власника, ліміти витрат, права оператора й підпис гаманця зберігаються.", rotation: "Замінити ключ? Поточний ключ одразу перестане працювати. Збережіть новий і оновіть інтеграції.", deletion: "Видалити ключ? Інтеграції одразу втратять доступ. Пізніше можна створити новий.", confirm: "Підтвердити", cancel: "Скасувати", loading: "Завантаження…", error: "Запит не виконано. Оновіть дані й повторіть.", usage: "Витрати платного API" },
  de: { title: "Ein API-Schlüssel für dein ANCAP-Konto", lead: "App oder KI ohne Agentenauswahl verbinden. Kontorechte und Guthaben gelten weiterhin.", login: "Zur API-Schlüsselverwaltung anmelden", create: "API-Schlüssel erstellen", rotate: "Schlüssel ersetzen", remove: "Schlüssel löschen", refresh: "Statistik aktualisieren", save: "Jetzt speichern: Der Schlüssel wird nur einmal angezeigt. Nicht in Chats oder im Repository speichern.", copy: "Schlüssel kopieren", copied: "Kopiert", manual: "Schlüssel markieren und manuell kopieren.", hide: "Schlüssel ausblenden", active: "Aktiver Schlüssel", inactive: "Kein aktiver Schlüssel", requests: "Anfragen", success: "Erfolgreich", failed: "Fehler", last: "Zuletzt verwendet", created: "Erstellt", history: "Statistik einschließlich früherer Schlüsselversionen. Löschen und Ersetzen behalten den Verlauf.", examples: "Verbindung testen", environment: "ANCAP_API_KEY lokal setzen. Diese Beispiele lesen dein Profil ohne kostenpflichtigen Workflow.", scope: "Eigentumsprüfungen, Ausgabenlimits, Betreiberrechte und Wallet-Signaturen bleiben erforderlich.", rotation: "Schlüssel ersetzen? Der bisherige Schlüssel wird sofort ungültig. Neuen speichern und Integrationen aktualisieren.", deletion: "Schlüssel löschen? Integrationen verlieren sofort den Zugriff. Später kannst du einen neuen erstellen.", confirm: "Bestätigen", cancel: "Abbrechen", loading: "Laden…", error: "Anfrage fehlgeschlagen. Aktualisieren und erneut versuchen.", usage: "Kostenpflichtige API-Nutzung" },
  "zh-Hant": { title: "一組 API 金鑰，存取你的 ANCAP 帳戶", lead: "連接應用程式或 AI，不必選擇代理。帳戶權限與餘額仍適用。", login: "登入以管理 API 金鑰", create: "建立 API 金鑰", rotate: "更換金鑰", remove: "刪除金鑰", refresh: "更新統計", save: "請立即儲存：金鑰僅顯示一次。請勿貼到對話或提交到程式碼庫。", copy: "複製金鑰", copied: "已複製", manual: "請選取並手動複製金鑰。", hide: "隱藏金鑰", active: "有效金鑰", inactive: "尚無有效金鑰", requests: "請求", success: "成功", failed: "失敗", last: "最後使用", created: "建立時間", history: "統計包含帳戶金鑰及歷代版本，更換或刪除不會清除紀錄。", examples: "測試連線", environment: "在本機設定 ANCAP_API_KEY。範例讀取個人資料，不啟動付費流程。", scope: "仍受所有權、支出限制、操作員權限與錢包簽署規則約束。", rotation: "更換金鑰？舊金鑰將立即失效。請儲存新金鑰並更新整合。", deletion: "刪除金鑰？整合將立即失去存取權。之後可建立新金鑰。", confirm: "確認", cancel: "取消", loading: "載入中…", error: "請求失敗，請更新後再試一次。", usage: "付費 API 使用紀錄" },
};
type KeyStatus = { active: boolean; key_prefix: string | null; created_at: string | null; last_used_at: string | null; requests: number; successful_requests: number; failed_requests: number };
const examples = [
  ["curl · Bash / zsh", 'curl https://api.ancap.cloud/v1/users/me \\\n  -H "X-API-Key: $ANCAP_API_KEY"'],
  ["Python", 'import json, os, urllib.request\n\nrequest = urllib.request.Request(\n    "https://api.ancap.cloud/v1/users/me",\n    headers={"X-API-Key": os.environ["ANCAP_API_KEY"]},\n)\nwith urllib.request.urlopen(request, timeout=30) as response:\n    print(json.load(response))'],
];

export function ApiConnection() {
  const { lang } = useLanguage();
  const c = messages[lang];
  const { isAuthenticated, isLoading } = useAuth();
  const [status, setStatus] = useState<KeyStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [key, setKey] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [confirmation, setConfirmation] = useState<"rotate" | "delete" | null>(null);
  async function load() {
    setBusy(true); setError(""); setKey(""); setNotice("");
    try { setStatus(await apiFetch("/keys/account")); }
    catch { setError(c.error); }
    finally { setBusy(false); }
  }
  useEffect(() => {
    if (!isLoading && isAuthenticated) void load();
    if (!isAuthenticated) { setStatus(null); setKey(""); setConfirmation(null); }
    // Authentication changes reset secrets; language changes never issue keys.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, isLoading]);
  async function mutate(action: "create" | "rotate" | "delete") {
    if (busy) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const result = await apiFetch(action === "rotate" ? "/keys/account/rotate" : "/keys/account", { method: action === "delete" ? "DELETE" : "POST" });
      if (action === "delete") { setKey(""); setStatus(await apiFetch("/keys/account")); }
      else { setStatus(result); setKey(result.key); }
      setConfirmation(null);
    } catch { setError(c.error); }
    finally { setBusy(false); }
  }
  return <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]"><Navigation />
    <main className="mx-auto max-w-4xl px-4 py-10">
      <Link href="/developers" className="text-sm text-emerald-300">← API</Link>
      <h1 className="mt-5 text-3xl font-semibold sm:text-5xl">{c.title}</h1>
      <p className="mt-4 text-[var(--text-secondary)]">{c.lead}</p>
      <section className="my-8 rounded-3xl border border-emerald-400/20 bg-emerald-400/[0.06] p-6">
        {isLoading ? <p>{c.loading}</p> : !isAuthenticated ? <Link href="/login" className="btn btn-primary">{c.login}</Link> : <>
          <h2 className="text-xl font-semibold">{status?.active ? c.active : c.inactive}</h2>
          {status?.active && <code className="mt-3 block">{status.key_prefix}••••••••</code>}
          {status?.created_at && <p className="mt-2 text-sm">{c.created}: {new Date(status.created_at).toLocaleString()}</p>}
          <div className="my-5 flex flex-wrap gap-3">
            {status && !status.active && <button className="btn btn-primary" disabled={busy} onClick={() => void mutate("create")}>{c.create}</button>}
            {status?.active && <><button className="btn btn-primary" disabled={busy} onClick={() => setConfirmation("rotate")}>{c.rotate}</button><button className="btn btn-ghost" disabled={busy} onClick={() => setConfirmation("delete")}>{c.remove}</button></>}
            <button className="btn btn-ghost" disabled={busy} onClick={() => void load()}>{busy ? c.loading : c.refresh}</button>
          </div>
          {confirmation && <div className="my-5 rounded-xl border border-amber-300/25 p-4"><p>{confirmation === "rotate" ? c.rotation : c.deletion}</p><div className="mt-3 flex gap-3"><button className="btn btn-primary" disabled={busy} onClick={() => void mutate(confirmation)}>{c.confirm}</button><button className="btn btn-ghost" disabled={busy} onClick={() => setConfirmation(null)}>{c.cancel}</button></div></div>}
          {key && <div className="my-5 rounded-xl border border-emerald-400/30 p-4"><p>{c.save}</p><code className="my-4 block select-all break-all">{key}</code><button className="btn btn-primary" onClick={async () => { try { await navigator.clipboard.writeText(key); setNotice(c.copied); } catch { setNotice(c.manual); } }}>{c.copy}</button><button className="btn btn-ghost" onClick={() => { setKey(""); setNotice(""); }}>{c.hide}</button></div>}
          {status && <><dl className="grid grid-cols-3 gap-3" aria-label="API statistics">{[[c.requests, status.requests], [c.success, status.successful_requests], [c.failed, status.failed_requests]].map(([label, value]) => <div key={label} className="rounded-xl border border-white/10 p-3"><dt className="text-sm text-[var(--text-secondary)]">{label}</dt><dd className="mt-2 text-2xl font-semibold">{value}</dd></div>)}</dl><p className="mt-4 text-sm">{c.last}: {status.last_used_at ? new Date(status.last_used_at).toLocaleString() : "—"}</p><p className="mt-3 text-xs text-[var(--text-secondary)]">{c.history}</p></>}
        </>}
        {error && <p role="alert" className="mt-4 text-red-300">{error}</p>}<p role="status" className="mt-3 text-sm">{notice}</p>
      </section>
      <section className="space-y-4"><h2 className="text-xl font-semibold">{c.examples}</h2><p>{c.environment}</p><p className="text-sm text-[var(--text-secondary)]">{c.scope}</p>
        {examples.map(([title, code]) => <article key={title} className="rounded-2xl border border-[var(--border)] p-5"><h3 className="font-semibold">{title}</h3><pre className="mt-4 overflow-x-auto text-sm"><code>{code}</code></pre></article>)}
        <div className="flex gap-5"><Link href="/developers/usage" className="text-emerald-300">{c.usage} →</Link><Link href="/mcp" className="text-emerald-300">MCP →</Link></div>
      </section>
    </main>
  </div>;
}
