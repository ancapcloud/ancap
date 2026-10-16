import type { Language } from "./translations";

type EconomyCopy = {
  title: string; lead: string; badge: string; limits: string; explore: string; tests: string;
  authorPrefix: string; home: string;
  steps: [string, string, string, string, string];
  stepNotes: [string, string, string, string, string];
  earnings: string; earningsLead: string; assumptions: string; price: string; orders: string;
  feePercent: string; variableCost: string; fixedCost: string; gross: string; fee: string; costs: string;
  net: string; loss: string; invalid: string; formula: string; disclaimer: string; creator: string; browse: string;
};

export const economyByLang: Record<Language, EconomyCopy> = {
  en: {
    title: "People + AI. A shared project, a defined result.",
    lead: "Authors publish applications with a defined result; people check inputs and AI prepares drafts for review. The first five catalog cards are demo projects by 3n3rgy. Earn on paid workflow runs today while this shared catalog stays in preview.",
    badge: "Proposed project model", limits: "Community create/apply and participant payouts for shared projects are not open yet. Existing paid workflows keep their own availability and terms. Earnings are not guaranteed.",
    explore: "Explore the project model", tests: "See AI test projects",
    authorPrefix: "Author", home: "ANCAP home",
    steps: ["Publish a project", "Find participants", "Agree an order and payment", "Review the result", "Distribute the reward"],
    stepNotes: ["Planned in Wave 1: describe a goal and tasks.", "Planned in Wave 1: people apply; agent delegation comes later.", "Wave 2: agree scope, recipients and payment terms.", "Wave 2: check agreed criteria and handle revisions.", "Wave 2: pay the agreed recipients; an agent's owner receives its reward."],
    earnings: "What could your workflow earn?", earningsLead: "Explore your own sales scenario in ACP. Change the price, order count and costs to see what remains.",
    assumptions: "Illustrative inputs — editable assumptions, not ANCAP fees, typical earnings or a demand forecast. Order count refers to a period you choose.",
    price: "Price per order (ACP)", orders: "Assumed orders per period", feePercent: "Your platform fee assumption (%)", variableCost: "Cost per order (ACP)", fixedCost: "Other costs per period (ACP)",
    gross: "Gross order value", fee: "Assumed platform fee", costs: "Assumed execution and other costs", net: "Scenario remainder", loss: "This scenario produces a loss", invalid: "Enter non-negative amounts up to 8 decimals, whole orders and a fee from 0 to 100% (up to 2 decimals).",
    formula: "Remainder = price × orders − platform fee − cost per order × orders − other costs.",
    disclaimer: "This is a scenario before taxes and any unentered refunds or expenses. Orders and earnings are not guaranteed. It neither creates a balance nor executes payouts; ACP is not converted to EUR or USD.",
    creator: "Explore the creator workspace", browse: "Choose an existing workflow",
  },
  ru: {
    title: "Люди + ИИ. Общий проект, понятный результат.",
    lead: "Автор публикует применение с понятным результатом; люди проверяют исходные данные, ИИ готовит черновик. Первые пять карточек — демо-проекты 3n3rgy. Заработок сегодня — через оплаченные запуски workflow; этот совместный каталог пока в предпросмотре.",
    badge: "Предлагаемая модель проектов", limits: "Создание и заявки сообщества, а также выплаты участникам по совместным проектам ещё закрыты. Условия платных workflow определяются отдельно. Доход не гарантирован.",
    explore: "Изучить модель проектов", tests: "Посмотреть тестовые AI-проекты",
    authorPrefix: "Автор", home: "Главная ANCAP",
    steps: ["Опубликовать проект", "Подобрать участников", "Согласовать заказ и оплату", "Принять результат", "Распределить вознаграждение"],
    stepNotes: ["План Wave 1: описать цель и задачи.", "План Wave 1: заявки людей; делегация агентам появится позже.", "Wave 2: согласовать объём, получателей и условия оплаты.", "Wave 2: проверить критерии и выполнить доработки.", "Wave 2: рассчитаться по условиям; за работу агента получает его владелец."],
    earnings: "Сколько может приносить ваш workflow?", earningsLead: "Рассчитайте собственный сценарий продаж в ACP. Меняйте цену, число заказов и затраты, чтобы увидеть остаток.",
    assumptions: "Пример расчёта: все значения — изменяемые допущения, а не тарифы ANCAP, типичный доход или прогноз спроса. Период для числа заказов выбираете вы.",
    price: "Цена заказа (ACP)", orders: "Предполагаемые заказы за период", feePercent: "Ваше допущение комиссии (%)", variableCost: "Затраты на заказ (ACP)", fixedCost: "Другие затраты за период (ACP)",
    gross: "Общая сумма заказов", fee: "Предполагаемая комиссия", costs: "Предполагаемые затраты", net: "Остаток по сценарию", loss: "Этот сценарий убыточен", invalid: "Введите неотрицательные суммы до 8 знаков после запятой, целое число заказов и комиссию 0–100% (до 2 знаков).",
    formula: "Остаток = цена × заказы − комиссия − затраты на заказ × заказы − другие затраты.",
    disclaimer: "Сценарий до налогов и неуказанных возвратов или расходов. Заказы и доход не гарантированы. Расчёт не создаёт баланс и не выполняет выплаты; ACP не переводятся в EUR или USD.",
    creator: "Изучить кабинет автора", browse: "Выбрать существующий workflow",
  },
  uk: {
    title: "Люди + ШІ. Спільний проєкт, визначений результат.",
    lead: "Автор публікує застосування з чітким результатом; люди перевіряють вхідні дані, ШІ готує чернетку. Перші п’ять карток — демо-проєкти 3n3rgy. Заробіток сьогодні — через оплачені запуски workflow; цей спільний каталог поки в попередньому перегляді.",
    badge: "Запропонована модель проєктів", limits: "Створення й заявки спільноти, а також виплати учасникам за спільними проєктами ще закриті. Умови платних workflow визначаються окремо. Дохід не гарантовано.",
    explore: "Дослідити модель проєктів", tests: "Переглянути тестові AI-проєкти",
    authorPrefix: "Автор", home: "Головна ANCAP",
    steps: ["Опублікувати проєкт", "Знайти учасників", "Узгодити замовлення й оплату", "Прийняти результат", "Розподілити винагороду"],
    stepNotes: ["План Wave 1: описати мету й завдання.", "План Wave 1: заявки людей; делегування агентам згодом.", "Wave 2: погодити обсяг, одержувачів та умови оплати.", "Wave 2: перевірити критерії й виконати доопрацювання.", "Wave 2: розрахуватися за умовами; винагороду агента отримує його власник."],
    earnings: "Скільки може приносити ваш workflow?", earningsLead: "Розрахуйте власний сценарій продажів в ACP. Змінюйте ціну, кількість замовлень і витрати, щоб побачити залишок.",
    assumptions: "Приклад розрахунку: усі значення — змінні припущення, а не тарифи ANCAP, типовий дохід чи прогноз попиту. Період для кількості замовлень обираєте ви.",
    price: "Ціна замовлення (ACP)", orders: "Очікувані замовлення за період", feePercent: "Ваше припущення комісії (%)", variableCost: "Витрати на замовлення (ACP)", fixedCost: "Інші витрати за період (ACP)",
    gross: "Загальна сума замовлень", fee: "Передбачувана комісія", costs: "Передбачувані витрати", net: "Залишок за сценарієм", loss: "Цей сценарій збитковий", invalid: "Введіть невід’ємні суми до 8 десяткових знаків, цілу кількість замовлень і комісію 0–100% (до 2 знаків).",
    formula: "Залишок = ціна × замовлення − комісія − витрати на замовлення × замовлення − інші витрати.",
    disclaimer: "Сценарій до податків і невказаних повернень чи витрат. Замовлення та дохід не гарантовані. Розрахунок не створює баланс і не виконує виплати; ACP не переводяться в EUR або USD.",
    creator: "Дослідити кабінет автора", browse: "Обрати наявний workflow",
  },
  de: {
    title: "Menschen + KI. Ein gemeinsames Projekt, ein klares Ergebnis.",
    lead: "Autoren veröffentlichen Anwendungen mit klarem Ergebnis; Menschen prüfen Eingaben, KI erstellt Entwürfe. Die ersten fünf Karten sind Demoprojekte von 3n3rgy. Verdienen Sie heute über bezahlte Workflow-Läufe; dieser gemeinsame Katalog bleibt in der Vorschau.",
    badge: "Vorgeschlagenes Projektmodell", limits: "Community-Erstellung/Bewerbungen und Auszahlungen für gemeinsame Projekte sind noch geschlossen. Für bestehende bezahlte Workflows gelten eigene Bedingungen. Einnahmen sind nicht garantiert.",
    explore: "Projektmodell ansehen", tests: "KI-Testprojekte ansehen",
    authorPrefix: "Autor", home: "ANCAP-Startseite",
    steps: ["Projekt veröffentlichen", "Mitwirkende finden", "Auftrag und Zahlung vereinbaren", "Ergebnis abnehmen", "Vergütung verteilen"],
    stepNotes: ["Geplant für Wave 1: Ziel und Aufgaben beschreiben.", "Geplant für Wave 1: Bewerbungen von Menschen; Agentendelegation folgt später.", "Wave 2: Umfang, Empfänger und Zahlungsbedingungen vereinbaren.", "Wave 2: Kriterien prüfen und Überarbeitungen bearbeiten.", "Wave 2: gemäß Vereinbarung auszahlen; die Agentenvergütung erhält dessen Eigentümer."],
    earnings: "Was könnte Ihr Workflow einbringen?", earningsLead: "Berechnen Sie Ihr eigenes Verkaufsszenario in ACP. Ändern Sie Preis, Auftragszahl und Kosten und sehen Sie den verbleibenden Betrag.",
    assumptions: "Beispielrechnung: Alle Werte sind bearbeitbare Annahmen, keine ANCAP-Tarife, typischen Einkünfte oder Nachfrageprognosen. Den Zeitraum für die Auftragszahl wählen Sie selbst.",
    price: "Preis pro Auftrag (ACP)", orders: "Angenommene Aufträge pro Zeitraum", feePercent: "Ihre Gebührenannahme (%)", variableCost: "Kosten pro Auftrag (ACP)", fixedCost: "Weitere Kosten pro Zeitraum (ACP)",
    gross: "Gesamtwert der Aufträge", fee: "Angenommene Plattformgebühr", costs: "Angenommene Kosten", net: "Verbleibender Szenariobetrag", loss: "Dieses Szenario ergibt einen Verlust", invalid: "Geben Sie nichtnegative Beträge mit bis zu 8 Dezimalstellen, ganze Aufträge und eine Gebühr von 0–100% (bis zu 2 Dezimalstellen) ein.",
    formula: "Restbetrag = Preis × Aufträge − Gebühr − Kosten pro Auftrag × Aufträge − weitere Kosten.",
    disclaimer: "Szenario vor Steuern und nicht eingetragenen Erstattungen oder Ausgaben. Aufträge und Erträge sind nicht garantiert. Die Berechnung erzeugt weder Guthaben noch Auszahlungen; ACP wird nicht in EUR oder USD umgerechnet.",
    creator: "Autorenbereich ansehen", browse: "Bestehenden Workflow auswählen",
  },
  "zh-Hant": {
    title: "人類 + AI：共同專案，明確成果。",
    lead: "作者發布具有明確成果的應用；人員核對輸入，AI 產生草稿供審核。前五張卡片是 3n3rgy 的示範專案。今日可透過付費工作流程執行獲得收益；此共同目錄仍為預覽。",
    badge: "擬議專案模式", limits: "社群建立／申請與共同專案參與者付款尚未開放。現有付費工作流程各有條款。收益不作保證。",
    explore: "了解專案模式", tests: "查看 AI 測試專案",
    authorPrefix: "作者", home: "ANCAP 首頁",
    steps: ["發布專案", "尋找參與者", "議定訂單與付款", "驗收成果", "分配報酬"],
    stepNotes: ["Wave 1 規劃：說明目標與任務。", "Wave 1 規劃：人員提出申請；代理授權稍後推出。", "Wave 2：議定範圍、收款方與付款條件。", "Wave 2：核對約定標準並處理修改。", "Wave 2：依約向收款方付款；代理的報酬由其擁有者收取。"],
    earnings: "您的工作流程可能帶來多少收入？", earningsLead: "以 ACP 試算您自己的銷售情境。調整價格、訂單數與成本，查看剩餘金額。",
    assumptions: "試算範例：所有數值皆為可調整的假設，並非 ANCAP 費率、典型收入或需求預測。訂單數所涵蓋的期間由您自行選定。",
    price: "每筆訂單價格（ACP）", orders: "假設期間訂單數", feePercent: "您假設的平台費率（%）", variableCost: "每筆訂單成本（ACP）", fixedCost: "期間其他成本（ACP）",
    gross: "訂單總額", fee: "假設平台費用", costs: "假設執行與其他成本", net: "情境剩餘金額", loss: "此情境產生虧損", invalid: "請輸入非負金額（最多 8 位小數）、整數訂單數，以及 0–100% 的費率（最多 2 位小數）。",
    formula: "剩餘金額 = 價格 × 訂單數 − 平台費用 − 每筆成本 × 訂單數 − 其他成本。",
    disclaimer: "此情境未扣稅，亦未計入未填寫的退款或費用。不保證訂單或收入。試算不會建立餘額或執行付款；ACP 不換算為歐元或美元。",
    creator: "了解作者工作區", browse: "選擇現有工作流程",
  },
};
