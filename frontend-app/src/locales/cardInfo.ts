import type { Language } from "./translations";

type CardCopy = { badge: string; title: string; lead: string; status: string; benefits: string[]; rewardsTitle: string; rewards: string; rewardsStatus: string; bonuses: string; transparency: string; cta: string; concept: string; model: string };
export const cardInfoByLang: Record<Language, CardCopy> = {
  en: {
    badge: "ANCAP Card · Waitlist", title: "From cryptoassets to everyday purchases.",
    lead: "We plan a card for in-store and online payments through a licensed partner, with clear conversion terms and rewards that are easy to track.",
    status: "The card is not available yet. Joining the waitlist is free and does not guarantee issuance. Countries, assets, fees and rewards will be announced after agreement with a partner. Apple Pay is not confirmed; no launch date is promised.",
    benefits: ["Everyday payments through a licensed partner", "Purchases, conversions, fees and rewards shown separately", "No mandatory ACP staking in the proposed model", "Service bonuses for selected AI tools and workflows are under consideration"],
    rewardsTitle: "A limited pilot, with clear limits", rewards: "We are considering 1% welcome cashback on the first €500 of eligible purchases, capped at €5 during the first 30 days after activation.",
    rewardsStatus: "Preliminary concept. This promotion is not active. No rewards are being accrued now.",
    bonuses: "Cashback would be paid in euros under the promotion rules. Service bonuses would be discounts on selected ANCAP services, with no withdrawal, transfer or exchange for money or ACP. Merchant offers would have separate terms.",
    transparency: "Issuer, identity checks, supported countries and assets, fees, limits and refunds must be disclosed before applications open. Crypto conversion may have tax consequences. Cryptoassets and stablecoins carry risks; rewards do not guarantee a net benefit. Direct ACP spending and an ACP/EUR rate are not confirmed.",
    cta: "Notify me about launch", concept: "Explore the concept", model: "Concept. Not an issued card"
  },
  ru: {
    badge: "ANCAP Card · Предзапись", title: "Из криптоактивов — в повседневные покупки.",
    lead: "Планируем карту для оплаты в магазинах и онлайн через лицензированного партнёра. С понятными условиями конвертации и вознаграждениями, которые удобно отслеживать.",
    status: "Карта пока недоступна. Предзапись бесплатна и не гарантирует выпуск. Страны, активы, комиссии и программа вознаграждений будут объявлены после согласования с партнёром. Apple Pay не подтверждён; дата запуска не обещана.",
    benefits: ["Привычная оплата через лицензированного партнёра", "Покупки, конвертация, комиссии и награды — раздельно", "Без обязательного стейкинга ACP в предлагаемой модели", "Рассматриваем сервисные бонусы на выбранные AI-инструменты и workflows"],
    rewardsTitle: "Ограниченный пилот с понятными лимитами", rewards: "Рассматриваем приветственный кешбэк 1% на первые €500 подходящих покупок — максимум €5 за первые 30 дней после активации.",
    rewardsStatus: "Предварительная концепция. Акция не действует. Вознаграждения сейчас не начисляются.",
    bonuses: "Денежный кешбэк — сумма в евро по правилам акции. Сервисные бонусы — скидки на выбранные услуги ANCAP, без вывода, передачи и обмена на деньги или ACP. Партнёрские предложения — с отдельными условиями.",
    transparency: "До оформления должны быть раскрыты эмитент, проверка личности, страны, активы, комиссии, лимиты и возвраты. Конвертация может иметь налоговые последствия. Криптоактивы и стейблкоины несут риски; кешбэк не гарантирует итоговую выгоду. Прямое расходование ACP и курс ACP/EUR не подтверждены.",
    cta: "Сообщить мне о запуске", concept: "Посмотреть концепцию", model: "Концепт. Не выпущенная карта"
  },
  uk: {
    badge: "ANCAP Card · Попередній запис", title: "Із криптоактивів — у повсякденні покупки.",
    lead: "Плануємо картку для оплати в магазинах та онлайн через ліцензованого партнера. Із зрозумілими умовами конвертації та винагородами, які зручно відстежувати.",
    status: "Картка поки недоступна. Попередній запис безкоштовний і не гарантує випуск. Країни, активи, комісії та винагороди оголосимо після узгодження з партнером. Apple Pay не підтверджено; дату запуску не обіцяно.",
    benefits: ["Звична оплата через ліцензованого партнера", "Покупки, конвертація, комісії та винагороди — окремо", "Без обов’язкового стейкінгу ACP у запропонованій моделі", "Розглядаємо сервісні бонуси на вибрані AI-інструменти та workflows"],
    rewardsTitle: "Обмежений пілот зі зрозумілими лімітами", rewards: "Розглядаємо вітальний кешбек 1% на перші €500 відповідних покупок — максимум €5 за перші 30 днів після активації.",
    rewardsStatus: "Попередня концепція. Акція не діє. Винагороди зараз не нараховуються.",
    bonuses: "Грошовий кешбек — сума в євро за правилами акції. Сервісні бонуси — знижки на вибрані послуги ANCAP, без виведення, передачі та обміну на гроші або ACP. Партнерські пропозиції матимуть окремі умови.",
    transparency: "До оформлення мають бути розкриті емітент, перевірка особи, країни, активи, комісії, ліміти та повернення. Конвертація може мати податкові наслідки. Криптоактиви та стейблкоїни несуть ризики; кешбек не гарантує підсумкової вигоди. Прямі витрати ACP та курс ACP/EUR не підтверджені.",
    cta: "Повідомити про запуск", concept: "Переглянути концепцію", model: "Концепт. Картку не випущено"
  },
  de: {
    badge: "ANCAP Card · Warteliste", title: "Von Kryptowerten zu alltäglichen Einkäufen.",
    lead: "Wir planen eine Karte für Zahlungen im Geschäft und online über einen lizenzierten Partner. Mit verständlichen Umrechnungsbedingungen und nachvollziehbaren Prämien.",
    status: "Die Karte ist noch nicht verfügbar. Die Warteliste ist kostenlos und garantiert keine Ausgabe. Länder, Vermögenswerte, Gebühren und Prämien werden nach Abstimmung mit einem Partner bekannt gegeben. Apple Pay ist nicht bestätigt; ein Starttermin wird nicht zugesagt.",
    benefits: ["Gewohnte Zahlungen über einen lizenzierten Partner", "Einkäufe, Umrechnungen, Gebühren und Prämien getrennt dargestellt", "Kein verpflichtendes ACP-Staking im vorgeschlagenen Modell", "Serviceboni für ausgewählte KI-Werkzeuge und Workflows werden geprüft"],
    rewardsTitle: "Begrenzter Pilot mit klaren Obergrenzen", rewards: "Wir erwägen 1% Willkommens-Cashback auf die ersten €500 berechtigten Einkäufe, höchstens €5 in den ersten 30 Tagen nach Aktivierung.",
    rewardsStatus: "Vorläufiges Konzept. Die Aktion ist nicht aktiv. Aktuell werden keine Prämien gutgeschrieben.",
    bonuses: "Cashback wäre ein Eurobetrag nach den Aktionsregeln. Serviceboni wären Rabatte auf ausgewählte ANCAP-Dienste, ohne Auszahlung, Übertragung oder Umtausch in Geld oder ACP. Händlerangebote hätten eigene Bedingungen.",
    transparency: "Vor Antragstellung müssen Herausgeber, Identitätsprüfung, Länder, Vermögenswerte, Gebühren, Limits und Erstattungen offengelegt werden. Umrechnungen können steuerliche Folgen haben. Kryptowerte und Stablecoins bergen Risiken; Cashback garantiert keinen Nettovorteil. Direkte ACP-Ausgaben und ein ACP/EUR-Kurs sind nicht bestätigt.",
    cta: "Über den Start informieren", concept: "Konzept ansehen", model: "Konzept. Keine ausgegebene Karte"
  },
  "zh-Hant": {
    badge: "ANCAP Card · 候補登記", title: "從加密資產到日常消費。",
    lead: "我們計畫透過持牌合作夥伴提供可於實體商店及網上付款的卡片，並清楚呈現兌換條件與獎勵。",
    status: "卡片尚未推出。候補登記免費，並不保證發卡。支援國家、資產、費用及獎勵將於合作條件確認後公布。Apple Pay 尚未確認，亦未承諾推出日期。",
    benefits: ["透過持牌合作夥伴進行日常付款", "分別顯示購買、兌換、費用與獎勵", "擬議模式不強制質押 ACP", "正考慮提供指定 AI 工具及工作流程的服務優惠"],
    rewardsTitle: "設有明確上限的有限試行方案", rewards: "我們正考慮提供迎新回饋：啟用後首 30 天內，首 €500 合資格消費享 1% 回饋，上限為 €5。",
    rewardsStatus: "初步概念。活動尚未生效，目前不會累積或發放獎勵。",
    bonuses: "現金回饋將依活動規則以歐元計算。服務優惠為指定 ANCAP 服務的折扣，不可提領、轉讓或兌換為金錢或 ACP。合作商戶優惠另有條款。",
    transparency: "開放申請前須公布發卡機構、身分驗證、支援國家及資產、費用、限額與退款規則。加密資產兌換可能涉及稅務。加密資產與穩定幣具有風險，回饋不保證淨收益。直接使用 ACP 消費及 ACP/EUR 匯率尚未確認。",
    cta: "通知我推出消息", concept: "查看概念", model: "概念設計。尚未發行的卡片"
  }
};
