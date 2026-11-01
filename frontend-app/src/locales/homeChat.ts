import type { Language } from "./translations";

export const homeChatByLang: Record<Language, {
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
  intro: string;
  workflows: string;
  smartPay: string;
  creators: string;
  howto: string;
  findWorkflow: string;
  earn: string;
  howtoPrompt: string;
  workflowsPrompt: string;
  earnPrompt: string;
  expand: string;
  collapse: string;
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
    unavailable: "Chat is currently unavailable. Explore the workflows and guides below.",
    limited: "The free model is busy. Try again in a little while.",
    failed: "The reply did not come through. Try again.",
    noVoice: "Voice input is not available in this browser.",
    dialog: "Ask ANCAP",
    intro: "Find a workflow, understand a payment, or explore how to earn.",
    workflows: "Workflows",
    smartPay: "Smart Pay",
    creators: "Creators",
    howto: "How ANCAP works",
    findWorkflow: "Find a workflow",
    earn: "How to earn",
    howtoPrompt: "Explain how ANCAP works in simple terms: buying and selling defined AI workflow outputs with ACP.",
    workflowsPrompt: "Help me choose a workflow on ANCAP for my task. Ask what I need, then suggest where to look in the catalog.",
    earnPrompt: "How can I earn on ANCAP as a creator? What do I publish and where do paid runs settle?",
    expand: "Full screen",
    collapse: "Exit full screen",
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
    unavailable: "Чат сейчас недоступен. Посмотрите процессы и руководства ниже.",
    limited: "Бесплатная модель занята. Попробуйте чуть позже.",
    failed: "Ответ не пришёл. Попробуйте ещё раз.",
    noVoice: "Голосовой ввод в этом браузере недоступен.",
    dialog: "Спросить ANCAP",
    intro: "Найдите workflow, разберитесь с оплатой или узнайте, как зарабатывать.",
    workflows: "Workflows",
    smartPay: "Smart Pay",
    creators: "Авторам",
    howto: "Как работает ANCAP",
    findWorkflow: "Найти workflow",
    earn: "Как зарабатывать",
    howtoPrompt: "Объясни простыми словами, как работает ANCAP: покупка и продажа готовых AI workflow за ACP.",
    workflowsPrompt: "Помоги выбрать workflow на ANCAP под мою задачу. Уточни, что нужно, и куда смотреть в каталоге.",
    earnPrompt: "Как зарабатывать на ANCAP как автор? Что публиковать и как проходят оплаченные запуски?",
    expand: "На весь экран",
    collapse: "Свернуть",
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
    unavailable: "Чат зараз недоступний. Перегляньте процеси й посібники нижче.",
    limited: "Безкоштовна модель зайнята. Спробуйте трохи пізніше.",
    failed: "Відповідь не надійшла. Спробуйте ще раз.",
    noVoice: "Голосове введення в цьому браузері недоступне.",
    dialog: "Запитати ANCAP",
    intro: "Знайдіть workflow, розберіться з оплатою або дізнайтеся, як заробляти.",
    workflows: "Workflows",
    smartPay: "Smart Pay",
    creators: "Авторам",
    howto: "Як працює ANCAP",
    findWorkflow: "Знайти workflow",
    earn: "Як заробляти",
    howtoPrompt: "Поясни простими словами, як працює ANCAP: купівля і продаж готових AI workflow за ACP.",
    workflowsPrompt: "Допоможи обрати workflow на ANCAP під мою задачу. Уточни потребу і куди дивитися в каталозі.",
    earnPrompt: "Як заробляти на ANCAP як автор? Що публікувати і як проходять оплачені запуски?",
    expand: "На весь екран",
    collapse: "Згорнути",
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
    unavailable: "Der Chat ist gerade nicht verfügbar. Entdecken Sie die Workflows und Anleitungen unten.",
    limited: "Das kostenlose Modell ist ausgelastet. Bitte später erneut versuchen.",
    failed: "Die Antwort ist nicht angekommen. Bitte erneut versuchen.",
    noVoice: "Spracheingabe ist in diesem Browser nicht verfügbar.",
    dialog: "ANCAP fragen",
    intro: "Workflow finden, Zahlungen verstehen oder Verdienstmöglichkeiten entdecken.",
    workflows: "Workflows",
    smartPay: "Smart Pay",
    creators: "Creator",
    howto: "So funktioniert ANCAP",
    findWorkflow: "Workflow finden",
    earn: "Verdienen",
    howtoPrompt: "Erkläre einfach, wie ANCAP funktioniert: Kauf und Verkauf definierter AI-Workflow-Ergebnisse mit ACP.",
    workflowsPrompt: "Hilf mir, einen Workflow auf ANCAP für meine Aufgabe zu finden. Frage nach dem Bedarf und zeige den Katalog.",
    earnPrompt: "Wie verdiene ich auf ANCAP als Creator? Was veröffentliche ich und wie laufen bezahlte Runs?",
    expand: "Vollbild",
    collapse: "Vollbild beenden",
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
    unavailable: "對話目前無法使用。請探索下方的工作流程與指南。",
    limited: "免費模型忙碌中，請稍後再試。",
    failed: "沒有收到回覆，請再試一次。",
    noVoice: "這個瀏覽器無法使用語音輸入。",
    dialog: "詢問 ANCAP",
    intro: "尋找工作流程、了解付款方式，或探索賺取收益的方法。",
    workflows: "Workflows",
    smartPay: "Smart Pay",
    creators: "創作者",
    howto: "ANCAP 如何運作",
    findWorkflow: "找 workflow",
    earn: "如何賺取",
    howtoPrompt: "用簡單說明解釋 ANCAP：如何用 ACP 買賣已定義的 AI workflow 產出。",
    workflowsPrompt: "幫我在 ANCAP 依需求選 workflow，並指出目錄該怎麼看。",
    earnPrompt: "作為創作者如何在 ANCAP 賺錢？要發布什麼，付費執行怎麼結算？",
    expand: "全螢幕",
    collapse: "結束全螢幕",
  },
};
