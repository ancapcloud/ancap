import type { Language } from "./translations";

type Copy = {
  title: string;
  lead: string;
  ratio: string;
  fees: string;
  amount: string;
  acpAddress: string;
  connect: string;
  redeem: string;
  busy: string;
  pending: string;
  payout: string;
  success: string;
  error: string;
  disabled: string;
  refresh: string;
  reserve: string;
  status: string;
};

export const racpRedeemCopy: Record<Language, Copy> = {
  en: {
    title: "Redeem rACP for ACP",
    lead: "Burn rACP on Robinhood Chain to request ACP from the exclusive reserve. This is a supervised payout, not a market swap.",
    ratio: "1 ACP = 10 rACP",
    fees: "You pay ETH network gas on Robinhood Chain. ACP is sent later from the reserve after the burn is indexed.",
    amount: "rACP amount",
    acpAddress: "ACP destination (acp1…)",
    connect: "Connect wallet",
    redeem: "Burn and redeem",
    busy: "Waiting for wallet…",
    pending: "Burn submitted. Waiting for confirmation…",
    payout: "Burn confirmed. Waiting for ACP payout…",
    success: "ACP payout completed.",
    error: "Could not complete redemption. Check amount alignment, ACP address, network and ETH for gas.",
    disabled: "Automated redemption is not enabled on the API yet.",
    refresh: "Refresh status",
    reserve: "Reserve ACP",
    status: "Service status",
  },
  ru: {
    title: "Обмен rACP на ACP",
    lead: "Сожгите rACP в сети Robinhood Chain, чтобы запросить ACP из exclusive-резерва. Это supervised payout, а не рыночный своп.",
    ratio: "1 ACP = 10 rACP",
    fees: "Комиссию в ETH платите вы. ACP придёт из резерва после индексации burn.",
    amount: "Сумма rACP",
    acpAddress: "Адрес ACP (acp1…)",
    connect: "Подключить кошелёк",
    redeem: "Сжечь и обменять",
    busy: "Ожидаем кошелёк…",
    pending: "Burn отправлен. Ждём подтверждение…",
    payout: "Burn подтверждён. Ждём выплату ACP…",
    success: "Выплата ACP завершена.",
    error: "Не удалось завершить обмен. Проверьте сумму, адрес ACP, сеть и ETH для газа.",
    disabled: "Автоматический обмен на API пока выключен.",
    refresh: "Обновить статус",
    reserve: "Резерв ACP",
    status: "Статус сервиса",
  },
  uk: {
    title: "Обмін rACP на ACP",
    lead: "Спаліть rACP у мережі Robinhood Chain, щоб запросити ACP з exclusive-резерву. Це supervised payout, не ринковий своп.",
    ratio: "1 ACP = 10 rACP",
    fees: "Комісію в ETH сплачуєте ви. ACP надійде з резерву після індексації burn.",
    amount: "Сума rACP",
    acpAddress: "Адреса ACP (acp1…)",
    connect: "Підключити гаманець",
    redeem: "Спалити й обміняти",
    busy: "Очікуємо гаманець…",
    pending: "Burn надіслано. Чекаємо підтвердження…",
    payout: "Burn підтверджено. Чекаємо виплату ACP…",
    success: "Виплату ACP завершено.",
    error: "Не вдалося завершити обмін. Перевірте суму, адресу ACP, мережу та ETH для газу.",
    disabled: "Автоматичний обмін на API поки вимкнено.",
    refresh: "Оновити статус",
    reserve: "Резерв ACP",
    status: "Статус сервісу",
  },
  de: {
    title: "rACP gegen ACP einlösen",
    lead: "Verbrennen Sie rACP auf Robinhood Chain, um ACP aus der exklusiven Reserve anzufordern. Supervised payout, kein Marktswap.",
    ratio: "1 ACP = 10 rACP",
    fees: "Sie zahlen ETH-Netzgebühren. ACP kommt später aus der Reserve nach Indexierung des Burns.",
    amount: "rACP-Betrag",
    acpAddress: "ACP-Zieladresse (acp1…)",
    connect: "Wallet verbinden",
    redeem: "Verbrennen und einlösen",
    busy: "Warten auf Wallet…",
    pending: "Burn gesendet. Warte auf Bestätigung…",
    payout: "Burn bestätigt. Warte auf ACP-Auszahlung…",
    success: "ACP-Auszahlung abgeschlossen.",
    error: "Einlösung fehlgeschlagen. Betrag, ACP-Adresse, Netzwerk und ETH prüfen.",
    disabled: "Automatische Einlösung ist auf der API noch nicht aktiv.",
    refresh: "Status aktualisieren",
    reserve: "ACP-Reserve",
    status: "Dienststatus",
  },
  "zh-Hant": {
    title: "將 rACP 兌回 ACP",
    lead: "在 Robinhood Chain 銷毀 rACP，向專屬儲備申請 ACP。此為托管式撥付，非市場兌換。",
    ratio: "1 ACP = 10 rACP",
    fees: "您需支付 Robinhood Chain 的 ETH 網路費。燒幣被索引後，ACP 會從儲備匯出。",
    amount: "rACP 數量",
    acpAddress: "ACP 收款地址（acp1…）",
    connect: "連接錢包",
    redeem: "銷毀並兌換",
    busy: "等待錢包…",
    pending: "銷毀交易已送出，等待確認…",
    payout: "銷毀已確認，等待 ACP 撥付…",
    success: "ACP 撥付完成。",
    error: "無法完成兌換。請檢查數量對齊、ACP 地址、網路與 ETH 手續費。",
    disabled: "API 尚未啟用自動兌換。",
    refresh: "重新整理狀態",
    reserve: "ACP 儲備",
    status: "服務狀態",
  },
};
