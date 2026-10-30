"use client";
import Link from "next/link";
import { Navigation } from "./Navigation";
import { useLanguage } from "./LanguageProvider";

const copy = {
  en: ["Archived token test", "wACP was an ANCAP test release on BSC. It is no longer promoted as the project's external token. The current external token is rACP on Robinhood Chain. Historical contracts, transactions and recorded obligations remain separate; this notice does not convert or cancel balances."],
  ru: ["Архив тестового выпуска", "wACP был тестовым выпуском ANCAP в BSC и больше не продвигается как внешний токен проекта. Основной внешний токен — rACP в Robinhood Chain. Исторические контракты, транзакции и учтённые обязательства сохраняются отдельно; эта пометка не конвертирует и не аннулирует балансы."],
  uk: ["Архів тестового випуску", "wACP був тестовим випуском ANCAP у BSC і більше не просувається як зовнішній токен проєкту. Основний зовнішній токен — rACP у Robinhood Chain. Історичні контракти, транзакції й обліковані зобов'язання зберігаються окремо; ця позначка не конвертує та не анулює баланси."],
  de: ["Archivierter Token-Test", "wACP war eine ANCAP-Testveröffentlichung auf BSC und wird nicht mehr als externer Projekttoken beworben. Der primäre externe Token ist rACP auf Robinhood Chain. Historische Verträge, Transaktionen und erfasste Verpflichtungen bleiben getrennt; dieser Hinweis wandelt Guthaben weder um noch löscht er sie."],
  "zh-Hant": ["代幣測試封存", "wACP 為 ANCAP 在 BSC 上的測試發行，目前已停止作為專案外部代幣推廣。主要外部代幣為 Robinhood Chain 上的 rACP。歷史合約、交易及已記錄的義務仍分開保留；此註記不會轉換或取消餘額。"],
};
export function TokenTestArchive() {
  const { lang } = useLanguage();
  const [title, body] = copy[lang];
  return <><Navigation /><main className="container" style={{ padding: "48px 24px" }}>
    <h1>{title}</h1><p style={{ lineHeight: 1.8, maxWidth: 850 }}>{body}</p>
    <Link href="/tokens/racp" className="btn btn-primary">rACP · Robinhood Chain</Link>
  </main></>;
}
