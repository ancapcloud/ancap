import type { Language } from "./translations";

type Copy = {
  title: string; lead: string; spend: string; wallet: string; redeem: string;
  limits: string; legacy: string; legacyBody: string; legacyLink: string;
  markets: string; documents: string; price: string;
  displayNote: string;
};
export const racpTransitionCopy: Record<Language, Copy> = {
  en: {
    displayNote: "Balances are shown as rACP equivalents (×10), not as ERC-20 holdings. Native ACP addresses and transfers remain in ACP. 1 EUR = 100 ACP = 1,000 rACP equivalents.",
    title: "ACP inside. rACP on Robinhood Chain.",
    lead: "ANCAP uses ACP for service balances and prices. rACP is its primary external token on Robinhood Chain: 10 rACP represent 1 ACP.",
    spend: "Use ACP for workflows", wallet: "ACP wallet", redeem: "Redeem rACP for ACP",
    limits: "Check redemption availability before sending tokens. Redemption pays ACP to a native ACP address; it does not automatically credit your service balance. ETH is required for network fees. ACP to rACP issuance is not a public self-service route.",
    legacy: "Existing wACP holders", legacyBody: "wACP on BSC is a legacy asset. Existing balances, reserve records and redemption support remain separate from rACP. There is no automatic wACP to rACP conversion.",
    legacyLink: "Legacy wACP redemption and history", markets: "Official rACP information", documents: "Documents and verification",
    price: "No rACP trading pool or market price is available. The backing ratio is not a USD quote. CoinStats has not returned an ANCAP, wACP or rACP catalog entry in our checks.",
  },
  ru: {
    displayNote: "Балансы показаны в эквиваленте rACP (×10), а не как владение ERC-20. Адреса нативной сети и переводы остаются в ACP. 1 EUR = 100 ACP = 1 000 rACP в эквиваленте.",
    title: "ACP внутри. rACP в Robinhood Chain.",
    lead: "Балансы и цены сервисов ANCAP остаются в ACP. Основной внешний токен — rACP в Robinhood Chain: 10 rACP представляют 1 ACP.",
    spend: "Оплатить workflow в ACP", wallet: "Кошелёк ACP", redeem: "Погасить rACP в ACP",
    limits: "Проверьте доступность погашения до отправки токенов. ACP поступает на адрес нативной сети ACP, а не автоматически на баланс сервисов. Для комиссии нужен ETH. Выпуск rACP за ACP пока не доступен как самостоятельная операция пользователя.",
    legacy: "Держателям wACP", legacyBody: "wACP в BSC — прежний токен. Его балансы, резервы и обслуживание погашений учитываются отдельно от rACP. Автоматической конвертации wACP в rACP нет.",
    legacyLink: "Погашение и история wACP", markets: "Официальные сведения о rACP", documents: "Документы и верификация",
    price: "Торгового пула и рыночной цены rACP пока нет. Курс обеспечения не является ценой в USD. При нашей проверке CoinStats не вернул запись ANCAP, wACP или rACP в каталоге.",
  },
  uk: {
    displayNote: "Баланси показано в еквіваленті rACP (×10), а не як володіння ERC-20. Адреси нативної мережі й перекази залишаються в ACP. 1 EUR = 100 ACP = 1 000 rACP в еквіваленті.",
    title: "ACP усередині. rACP у Robinhood Chain.",
    lead: "Баланси й ціни сервісів ANCAP залишаються в ACP. Основний зовнішній токен — rACP у Robinhood Chain: 10 rACP представляють 1 ACP.",
    spend: "Оплатити workflow в ACP", wallet: "Гаманець ACP", redeem: "Погасити rACP в ACP",
    limits: "Перевірте доступність погашення до надсилання токенів. ACP надходить на адресу нативної мережі ACP, а не автоматично на баланс сервісів. Для комісії потрібен ETH. Самостійний випуск rACP за ACP поки недоступний.",
    legacy: "Власникам wACP", legacyBody: "wACP у BSC — попередній токен. Його баланси, резерви й погашення обліковуються окремо від rACP. Автоматичної конвертації wACP у rACP немає.",
    legacyLink: "Погашення та історія wACP", markets: "Офіційні відомості про rACP", documents: "Документи й верифікація",
    price: "Торгового пулу та ринкової ціни rACP поки немає. Курс забезпечення не є ціною в USD. Під час нашої перевірки CoinStats не повернув запис ANCAP, wACP або rACP у каталозі.",
  },
  de: {
    displayNote: "Guthaben werden als rACP-Gegenwert (×10) angezeigt, nicht als ERC-20-Bestand. Native ACP-Adressen und Überweisungen bleiben in ACP. 1 EUR = 100 ACP = 1.000 rACP-Gegenwert.",
    title: "ACP intern. rACP auf Robinhood Chain.",
    lead: "ANCAP führt Serviceguthaben und Preise weiter in ACP. rACP ist der primäre externe Token auf Robinhood Chain: 10 rACP entsprechen 1 ACP.",
    spend: "Workflows mit ACP nutzen", wallet: "ACP-Wallet", redeem: "rACP gegen ACP einlösen",
    limits: "Verfügbarkeit vor dem Senden prüfen. Die Einlösung zahlt ACP an eine native ACP-Adresse aus und schreibt es nicht automatisch dem Serviceguthaben gut. Netzwerkgebühren erfordern ETH. Die Ausgabe von rACP gegen ACP ist noch kein öffentlicher Selbstbedienungsweg.",
    legacy: "Für bestehende wACP-Inhaber", legacyBody: "wACP auf BSC ist ein Altbestand. Guthaben, Reserven und Einlösungen bleiben von rACP getrennt. Es gibt keinen automatischen Umtausch von wACP in rACP.",
    legacyLink: "wACP-Einlösung und Verlauf", markets: "Offizielle rACP-Informationen", documents: "Dokumente und Verifizierung",
    price: "Es gibt noch keinen rACP-Handelspool oder Marktpreis. Das Deckungsverhältnis ist kein USD-Kurs. Unsere CoinStats-Abfragen lieferten keinen Katalogeintrag für ANCAP, wACP oder rACP.",
  },
  "zh-Hant": {
    displayNote: "餘額以 rACP 等值（×10）顯示，不代表持有 ERC-20。原生 ACP 地址及轉帳仍使用 ACP。1 EUR = 100 ACP = 1,000 rACP 等值。",
    title: "內部使用 ACP，外部使用 Robinhood Chain 上的 rACP。",
    lead: "ANCAP 服務餘額與價格仍以 ACP 計算。rACP 是 Robinhood Chain 上的主要外部代幣：10 rACP 代表 1 ACP。",
    spend: "使用 ACP 執行工作流程", wallet: "ACP 錢包", redeem: "將 rACP 贖回為 ACP",
    limits: "發送代幣前請確認贖回是否開放。贖回將 ACP 轉入原生 ACP 地址，不會自動增加服務餘額。網路費用需使用 ETH。目前尚無公開的 ACP 換發 rACP 自助流程。",
    legacy: "現有 wACP 持有人", legacyBody: "BSC 上的 wACP 為舊有資產，其餘額、儲備及贖回與 rACP 分別處理。目前沒有自動將 wACP 轉為 rACP 的功能。",
    legacyLink: "wACP 贖回與紀錄", markets: "rACP 官方資訊", documents: "文件與驗證",
    price: "目前尚無 rACP 交易池或市場價格。儲備比率不等於美元報價。我們查詢 CoinStats 時，目錄未傳回 ANCAP、wACP 或 rACP 項目。",
  },
};
