"use client";
import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import { apiFetch } from "@/lib/api";

const copy = {
  en: ["Street QR stickers", "Total visits", "Today", "Refresh", "Date", "Visits", "Link opens, not unique people. Repeat scans count. Known bots and prefetches are excluded; other bots may count. Berlin time.", "Loading…", "Could not load QR statistics."],
  ru: ["Уличные QR-наклейки", "Всего переходов", "Сегодня", "Обновить", "Дата", "Переходы", "Открытия ссылки, не уникальные люди. Повторные сканирования учитываются. Известные боты и предзагрузка исключены; другие боты могут учитываться. Время Берлина.", "Загрузка…", "Не удалось загрузить статистику QR."],
  uk: ["Вуличні QR-наліпки", "Усього переходів", "Сьогодні", "Оновити", "Дата", "Переходи", "Відкриття посилання, не унікальні люди. Повторні сканування враховуються. Відомі боти й попередні завантаження виключені; інші боти можуть враховуватися. Час Берліна.", "Завантаження…", "Не вдалося завантажити статистику QR."],
  de: ["QR-Aufkleber: Straße", "Aufrufe insgesamt", "Heute", "Aktualisieren", "Datum", "Aufrufe", "Linkaufrufe, keine eindeutigen Personen. Wiederholte Scans zählen. Bekannte Bots und Vorabrufe sind ausgeschlossen; andere Bots können zählen. Berliner Zeit.", "Wird geladen…", "QR-Statistik konnte nicht geladen werden."],
  "zh-Hant": ["街頭 QR 貼紙", "總開啟次數", "今天", "重新整理", "日期", "次數", "計算連結開啟次數，非不重複人數。重複掃描會計入。排除已知機器人與預先載入；其他機器人仍可能計入。柏林時間。", "載入中…", "無法載入 QR 統計。"],
};
type Stats = { total: number; today: number; days: {day: string; visits: number}[] };
export default function QrCampaignStats() {
  const { lang } = useLanguage();
  const c = copy[lang as keyof typeof copy] || copy.en;
  const [data, setData] = useState<Stats | null>(null);
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);
  async function load() {
    setBusy(true); setError(false);
    try { setData(await apiFetch("/qr/street/stats?days=30")); }
    catch { setError(true); setData(null); }
    finally { setBusy(false); }
  }
  useEffect(() => { void load(); }, []);
  return <section className="rounded-2xl border border-emerald-400/20 p-5 space-y-4" aria-label={c[0]}>
    <div className="flex flex-wrap justify-between gap-3"><h2 className="text-lg font-medium">{c[0]}</h2>
      <button type="button" onClick={() => void load()} disabled={busy} className="rounded-lg border border-white/20 px-3 py-1 disabled:opacity-50">{c[3]}</button></div>
    <p className="break-all text-emerald-300">https://ancap.cloud/q/street</p>
    <p className="text-sm text-white/60">{c[6]}</p>
    <div aria-live="polite">{busy ? c[7] : error ? <p role="alert">{c[8]}</p> : data && <>
      <div className="flex flex-wrap gap-8"><p>{c[1]}: <strong className="text-2xl">{data.total}</strong></p><p>{c[2]}: <strong className="text-2xl">{data.today}</strong></p></div>
      <div className="mt-4 max-h-64 overflow-auto"><table className="w-full text-left text-sm"><thead><tr><th scope="col">{c[4]}</th><th scope="col">{c[5]}</th></tr></thead><tbody>{data.days.map(d => <tr key={d.day}><td>{d.day}</td><td>{d.visits}</td></tr>)}</tbody></table></div>
    </>}</div>
  </section>;
}
