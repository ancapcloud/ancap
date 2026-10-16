import type { Language } from "./translations";
import type { TestProjectId } from "@/lib/testProjects";

type TestProjectCopy = {
  goal: string;
  people: string;
  ai: string;
  deliverable: string;
  sample: string;
};

type TestProjectsCopy = {
  kicker: string;
  title: string;
  lead: string;
  badge: string;
  disclosure: string;
  authorPrefix: string;
  goal: string;
  people: string;
  ai: string;
  deliverable: string;
  sample: string;
  open: string;
  more: string;
  projects: Record<TestProjectId, TestProjectCopy>;
};

export const testProjectsByLang: Record<Language, TestProjectsCopy> = {
  en: {
    kicker: "Project sandbox",
    title: "Test projects created by AI",
    lead: "Explore five worked examples by 3n3rgy: a request, people and AI working together, and a sample document you could review before defining your own project.",
    badge: "AI-created test scenario",
    disclosure: "These are illustrative scenarios with synthetic inputs and AI-authored sample outputs by platform user 3n3rgy. They are not completed customer orders, verified results or deployed services. Existing project pages describe their available briefs separately.",
    authorPrefix: "Author",
    goal: "Example request",
    people: "Human role",
    ai: "AI role",
    deliverable: "Example deliverable",
    sample: "Read the sample AI output",
    open: "Project home",
    more: "Explore all test scenarios",
    projects: {
      aeterna: {
        goal: "Turn a broad interest in longevity research into a clear brief for a qualified professional.",
        people: "The requester chooses the research question. A qualified reviewer checks sources and boundaries before any use.",
        ai: "Structures public-source research, marks missing evidence and drafts questions for review.",
        deliverable: "A research outline, evidence checklist and professional-review questions.",
        sample: "DRAFT · Topic: how to assess a longevity research claim. Sections: research question; source and publication date; study population; limitations; questions for a qualified reviewer. Evidence fields: [source required]. Next step: fill and verify the source list. No individual health assessment is included.",
      },
      galaxy: {
        goal: "Sketch an encrypted edge-computing concept for a hypothetical space project.",
        people: "The project owner defines the data. A security specialist and infrastructure partner review the concept.",
        ai: "Drafts component responsibilities, trust boundaries and unanswered feasibility questions.",
        deliverable: "An architecture brief and a list of checks for a potential infrastructure partner.",
        sample: "DRAFT · Proposed flow: data owner → encrypted upload → isolated workload → result review. Open questions: hosting availability; key custody; connectivity; recovery; supplier capability. Acceptance: an expert can identify each trust boundary. This document does not confirm an orbital deployment or supplier agreement.",
      },
      lunar: {
        goal: "Design a science-themed catalog using fictional lunar parcel records.",
        people: "An editor chooses the educational scope and verifies the labeling of every record.",
        ai: "Proposes a record schema, example entries and a publication checklist.",
        deliverable: "A sample catalog specification with a clearly labeled fictional entry.",
        sample: "DRAFT · Record: DEMO-LUNAR-001. Fields: display name; fictional coordinates; research theme; source links; editorial status. Status: synthetic sample, sources pending. Publication rule: distinguish educational catalog records from ownership rights. This entry provides no land title or mining rights.",
      },
      stardust: {
        goal: "Define a weather-research dashboard with sample observations and human review.",
        people: "The requester defines the region and use case. A domain reviewer checks data sources and interpretation.",
        ai: "Organizes the input fields and drafts a review note for incomplete data.",
        deliverable: "A dashboard brief, input schema and sample review note.",
        sample: "DRAFT · Scenario: a fictional weather observation needs review. Fields: region; time; source; observation; confidence; reviewer. Missing: verified source and timestamp. Proposed status: await human verification. This is a dashboard example, not a live forecast, emergency alert or weather-control result.",
      },
      starlink: {
        goal: "Prepare a sample satellite-internet installation request for an independent technician.",
        people: "The requester supplies site requirements. A qualified technician assesses the location and agrees the work.",
        ai: "Organizes site information and drafts a checklist for the technician's assessment.",
        deliverable: "A site-intake brief and questions to resolve before a service quote.",
        sample: "DRAFT · Site: fictional small office. Required inputs: location; equipment model; mounting constraints; power and cable route; permission to access the site. Open items: availability, technician assessment and quote. This sample does not book an installation or establish a relationship with Starlink.",
      },
    },
  },
  ru: {
    kicker: "Песочница проектов",
    title: "Тестовые проекты, созданные ИИ",
    lead: "Посмотрите пять примеров пользователя 3n3rgy: задача, совместная работа человека и ИИ и образец документа, который поможет сформулировать собственный проект.",
    badge: "Тестовый сценарий создан ИИ",
    disclosure: "Это демонстрационные сценарии пользователя 3n3rgy с вымышленными исходными данными и образцами текста от ИИ. Они не являются выполненными заказами клиентов, подтверждёнными результатами или запущенными услугами. Доступные брифы описаны отдельно на существующих страницах проектов.",
    authorPrefix: "Автор",
    goal: "Пример задачи",
    people: "Роль человека",
    ai: "Роль ИИ",
    deliverable: "Пример результата",
    sample: "Посмотреть образец ответа ИИ",
    open: "Главная проекта",
    more: "Посмотреть все тестовые сценарии",
    projects: {
      aeterna: {
        goal: "Превратить общий интерес к исследованиям долголетия в понятный бриф для профильного специалиста.",
        people: "Заказчик выбирает исследовательский вопрос. Профильный специалист проверяет источники и границы применения.",
        ai: "Структурирует исследования по открытым источникам, отмечает пробелы и составляет вопросы для проверки.",
        deliverable: "План обзора, список проверок источников и вопросы для специалиста.",
        sample: "ЧЕРНОВИК · Тема: как оценивать утверждение об исследовании долголетия. Разделы: вопрос; источник и дата публикации; участники исследования; ограничения; вопросы специалисту. Поля доказательств: [нужен источник]. Следующий шаг: заполнить и проверить список источников. Индивидуальной оценки здоровья в документе нет.",
      },
      galaxy: {
        goal: "Проработать концепцию защищённых периферийных вычислений для условного космического проекта.",
        people: "Владелец проекта определяет данные. Специалист по безопасности и инфраструктурный партнёр проверяют концепцию.",
        ai: "Описывает задачи компонентов, границы доверия и открытые вопросы реализуемости.",
        deliverable: "Архитектурный бриф и список вопросов потенциальному инфраструктурному партнёру.",
        sample: "ЧЕРНОВИК · Схема: владелец данных → зашифрованная загрузка → изолированная задача → проверка результата. Открыто: доступность хостинга; хранение ключей; связь; восстановление; возможности поставщика. Приёмка: эксперт может выделить каждую границу доверия. Документ не подтверждает запуск на орбите или договор с поставщиком.",
      },
      lunar: {
        goal: "Спроектировать научно-популярный каталог с вымышленными записями лунных участков.",
        people: "Редактор определяет образовательную задачу и проверяет маркировку каждой записи.",
        ai: "Предлагает структуру записей, примеры и список проверок перед публикацией.",
        deliverable: "Спецификация каталога с явно обозначенной вымышленной записью.",
        sample: "ЧЕРНОВИК · Запись: DEMO-LUNAR-001. Поля: название; вымышленные координаты; тема исследования; ссылки на источники; статус редакторской проверки. Статус: вымышленный пример, источники ожидаются. Правило публикации: отделять учебную запись от права собственности. Запись не даёт прав на землю или добычу ресурсов.",
      },
      stardust: {
        goal: "Описать панель погодных исследований с примерными наблюдениями и проверкой человеком.",
        people: "Заказчик определяет регион и задачу. Профильный специалист проверяет источники и трактовку данных.",
        ai: "Структурирует входные поля и готовит замечание о неполноте данных.",
        deliverable: "Бриф панели, схема данных и пример заметки для проверки.",
        sample: "ЧЕРНОВИК · Сценарий: условное погодное наблюдение требует проверки. Поля: регион; время; источник; наблюдение; уверенность; проверяющий. Не хватает: подтверждённого источника и времени. Статус: ожидается проверка человеком. Это пример панели, а не актуальный прогноз, экстренное предупреждение или результат управления погодой.",
      },
      starlink: {
        goal: "Подготовить пример заявки на установку спутникового интернета для независимого специалиста.",
        people: "Заказчик описывает объект. Квалифицированный специалист оценивает место и согласует работы.",
        ai: "Собирает сведения об объекте в бриф и составляет вопросы для осмотра специалистом.",
        deliverable: "Бриф объекта и список вопросов до расчёта стоимости услуг.",
        sample: "ЧЕРНОВИК · Объект: вымышленный небольшой офис. Нужны: адрес; модель оборудования; ограничения крепления; питание и маршрут кабеля; разрешение на доступ. Открыто: доступность услуги, осмотр и смета специалиста. Образец не оформляет установку и не подтверждает партнёрство со Starlink.",
      },
    },
  },
  uk: {
    kicker: "Пісочниця проєктів",
    title: "Тестові проєкти, створені ШІ",
    lead: "Перегляньте п’ять прикладів користувача 3n3rgy: завдання, спільна робота людини та ШІ й зразок документа, який допоможе сформулювати власний проєкт.",
    badge: "Тестовий сценарій створено ШІ",
    disclosure: "Це демонстраційні сценарії користувача 3n3rgy з вигаданими вхідними даними та зразками тексту від ШІ. Вони не є виконаними замовленнями клієнтів, підтвердженими результатами чи запущеними послугами. Доступні брифи окремо описані на наявних сторінках проєктів.",
    authorPrefix: "Автор",
    goal: "Приклад завдання",
    people: "Роль людини",
    ai: "Роль ШІ",
    deliverable: "Приклад результату",
    sample: "Переглянути зразок відповіді ШІ",
    open: "Головна проєкту",
    more: "Переглянути всі тестові сценарії",
    projects: {
      aeterna: {
        goal: "Перетворити загальний інтерес до досліджень довголіття на зрозумілий бриф для профільного фахівця.",
        people: "Замовник обирає дослідницьке питання. Профільний фахівець перевіряє джерела й межі застосування.",
        ai: "Структурує дослідження з відкритих джерел, позначає прогалини та складає питання для перевірки.",
        deliverable: "План огляду, перелік перевірок джерел і питання до фахівця.",
        sample: "ЧЕРНЕТКА · Тема: як оцінювати твердження про дослідження довголіття. Розділи: питання; джерело й дата публікації; учасники дослідження; обмеження; питання до фахівця. Поля доказів: [потрібне джерело]. Наступний крок: заповнити й перевірити список джерел. Індивідуальної оцінки здоров’я документ не містить.",
      },
      galaxy: {
        goal: "Опрацювати концепцію захищених периферійних обчислень для умовного космічного проєкту.",
        people: "Власник проєкту визначає дані. Фахівець із безпеки та інфраструктурний партнер перевіряють концепцію.",
        ai: "Описує завдання компонентів, межі довіри та відкриті питання здійсненності.",
        deliverable: "Архітектурний бриф і список питань потенційному інфраструктурному партнеру.",
        sample: "ЧЕРНЕТКА · Схема: власник даних → зашифроване завантаження → ізольоване завдання → перевірка результату. Відкрито: доступність хостингу; зберігання ключів; зв’язок; відновлення; можливості постачальника. Приймання: експерт може визначити кожну межу довіри. Документ не підтверджує запуск на орбіті чи угоду з постачальником.",
      },
      lunar: {
        goal: "Спроєктувати науково-популярний каталог із вигаданими записами місячних ділянок.",
        people: "Редактор визначає освітнє завдання й перевіряє маркування кожного запису.",
        ai: "Пропонує структуру записів, приклади й перелік перевірок перед публікацією.",
        deliverable: "Специфікація каталогу з явно позначеним вигаданим записом.",
        sample: "ЧЕРНЕТКА · Запис: DEMO-LUNAR-001. Поля: назва; вигадані координати; тема дослідження; посилання на джерела; статус редакторської перевірки. Статус: вигаданий приклад, джерела очікуються. Правило публікації: відділяти навчальний запис від права власності. Запис не надає прав на землю чи видобування ресурсів.",
      },
      stardust: {
        goal: "Описати панель погодних досліджень із прикладами спостережень і перевіркою людиною.",
        people: "Замовник визначає регіон і завдання. Профільний фахівець перевіряє джерела й тлумачення даних.",
        ai: "Структурує вхідні поля й готує примітку про неповні дані.",
        deliverable: "Бриф панелі, схема даних і приклад примітки для перевірки.",
        sample: "ЧЕРНЕТКА · Сценарій: умовне погодне спостереження потребує перевірки. Поля: регіон; час; джерело; спостереження; впевненість; перевіряльник. Бракує: підтвердженого джерела та часу. Статус: очікується перевірка людиною. Це приклад панелі, а не актуальний прогноз, екстрене попередження чи результат керування погодою.",
      },
      starlink: {
        goal: "Підготувати приклад заявки на встановлення супутникового інтернету для незалежного фахівця.",
        people: "Замовник описує об’єкт. Кваліфікований фахівець оцінює місце й погоджує роботи.",
        ai: "Упорядковує відомості про об’єкт і складає питання для огляду фахівцем.",
        deliverable: "Бриф об’єкта й список питань до розрахунку вартості послуг.",
        sample: "ЧЕРНЕТКА · Об’єкт: вигаданий невеликий офіс. Потрібні: адреса; модель обладнання; обмеження кріплення; живлення й маршрут кабелю; дозвіл на доступ. Відкрито: доступність послуги, огляд і кошторис фахівця. Зразок не оформлює встановлення й не підтверджує партнерство зі Starlink.",
      },
    },
  },
  de: {
    kicker: "Projekt-Sandbox",
    title: "Von KI erstellte Testprojekte",
    lead: "Entdecken Sie fünf Beispiele von 3n3rgy: eine Anfrage, die Zusammenarbeit von Mensch und KI und ein Musterdokument als Ausgangspunkt für Ihr eigenes Projekt.",
    badge: "Von KI erstelltes Testszenario",
    disclosure: "Dies sind illustrative Szenarien von Plattformnutzer 3n3rgy mit fiktiven Eingaben und von KI verfassten Mustertexten. Sie sind keine abgeschlossenen Kundenaufträge, verifizierten Ergebnisse oder bereitgestellten Dienste. Bestehende Projektseiten beschreiben ihre verfügbaren Briefings separat.",
    authorPrefix: "Autor",
    goal: "Beispielanfrage",
    people: "Aufgabe des Menschen",
    ai: "Aufgabe der KI",
    deliverable: "Beispielergebnis",
    sample: "KI-Mustertext lesen",
    open: "Projekt-Startseite",
    more: "Alle Testszenarien entdecken",
    projects: {
      aeterna: {
        goal: "Ein allgemeines Interesse an Langlebigkeitsforschung in ein klares Briefing für eine Fachperson übersetzen.",
        people: "Der Auftraggeber wählt die Forschungsfrage. Eine qualifizierte Fachperson prüft Quellen und Anwendungsgrenzen.",
        ai: "Strukturiert öffentlich zugängliche Forschung, kennzeichnet Beleglücken und formuliert Prüffragen.",
        deliverable: "Eine Recherchegliederung, Quellencheckliste und Fragen zur fachlichen Prüfung.",
        sample: "ENTWURF · Thema: eine Aussage zur Langlebigkeitsforschung beurteilen. Abschnitte: Forschungsfrage; Quelle und Publikationsdatum; Studienpopulation; Grenzen; Fragen an eine Fachperson. Belegfelder: [Quelle erforderlich]. Nächster Schritt: Quellenliste ergänzen und prüfen. Eine individuelle Gesundheitsbewertung ist nicht enthalten.",
      },
      galaxy: {
        goal: "Ein Konzept für verschlüsselte Edge-Verarbeitung in einem hypothetischen Raumfahrtprojekt skizzieren.",
        people: "Der Projektverantwortliche bestimmt die Daten. Sicherheitsfachleute und ein Infrastrukturpartner prüfen das Konzept.",
        ai: "Entwirft Zuständigkeiten der Komponenten, Vertrauensgrenzen und offene Machbarkeitsfragen.",
        deliverable: "Ein Architekturbriefing mit Prüffragen an einen möglichen Infrastrukturpartner.",
        sample: "ENTWURF · Ablauf: Dateneigentümer → verschlüsselter Upload → isolierte Aufgabe → Ergebnisprüfung. Offen: Hosting-Verfügbarkeit; Schlüsselverwahrung; Verbindung; Wiederherstellung; Anbieterfähigkeit. Abnahme: Fachleute können jede Vertrauensgrenze zuordnen. Das Dokument bestätigt weder einen Orbitaleinsatz noch einen Anbietervertrag.",
      },
      lunar: {
        goal: "Einen wissenschaftlich gestalteten Katalog mit fiktiven Mondparzellen entwerfen.",
        people: "Eine Redaktion bestimmt den Bildungszweck und prüft die Kennzeichnung jedes Datensatzes.",
        ai: "Schlägt Datenschema, Beispieleinträge und eine Veröffentlichungsliste vor.",
        deliverable: "Eine Katalogspezifikation mit eindeutig gekennzeichnetem fiktivem Eintrag.",
        sample: "ENTWURF · Datensatz: DEMO-LUNAR-001. Felder: Anzeigename; fiktive Koordinaten; Forschungsthema; Quellenlinks; Redaktionsstatus. Status: fiktives Muster, Quellen ausstehend. Regel: Bildungsdatensätze von Eigentumsrechten trennen. Der Eintrag verleiht weder Grundeigentum noch Abbaurechte.",
      },
      stardust: {
        goal: "Ein Wetterforschungsdashboard mit Musterbeobachtungen und menschlicher Prüfung beschreiben.",
        people: "Der Auftraggeber definiert Region und Zweck. Fachleute prüfen Datenquellen und Interpretation.",
        ai: "Ordnet Eingabefelder und verfasst einen Prüfhinweis für unvollständige Daten.",
        deliverable: "Ein Dashboard-Briefing, Datenschema und Musterprüfhinweis.",
        sample: "ENTWURF · Szenario: Eine fiktive Wetterbeobachtung muss geprüft werden. Felder: Region; Zeit; Quelle; Beobachtung; Vertrauensniveau; Prüfer. Fehlend: bestätigte Quelle und Zeitstempel. Statusvorschlag: menschliche Prüfung ausstehend. Dies ist ein Dashboard-Muster, keine aktuelle Vorhersage, Notfallwarnung oder Wettersteuerung.",
      },
      starlink: {
        goal: "Eine Musteranfrage zur Installation von Satelliteninternet für einen unabhängigen Fachbetrieb vorbereiten.",
        people: "Der Auftraggeber beschreibt den Standort. Eine qualifizierte Fachkraft prüft ihn und vereinbart die Arbeiten.",
        ai: "Ordnet Standortinformationen und erstellt eine Checkliste für die fachliche Besichtigung.",
        deliverable: "Ein Standortbriefing mit offenen Fragen vor einem Dienstleistungsangebot.",
        sample: "ENTWURF · Standort: fiktives kleines Büro. Benötigt: Adresse; Gerätemodell; Montagebedingungen; Stromversorgung und Kabelweg; Zugangsberechtigung. Offen: Verfügbarkeit, Besichtigung und Angebot der Fachkraft. Das Muster bucht keine Installation und bestätigt keine Partnerschaft mit Starlink.",
      },
    },
  },
  "zh-Hant": {
    kicker: "專案沙盒",
    title: "由 AI 建立的測試專案",
    lead: "探索使用者 3n3rgy 的五個範例：需求、人員與 AI 的分工，以及可在定義自己的專案前先檢視的文件樣本。",
    badge: "AI 建立的測試情境",
    disclosure: "這些是平台使用者 3n3rgy 的示範情境，使用虛構輸入及 AI 撰寫樣本，並非已完成的客戶訂單、經驗證的成果或已部署的服務。現有專案頁面會另行說明可提供的簡報。",
    authorPrefix: "作者",
    goal: "需求範例",
    people: "人員角色",
    ai: "AI 角色",
    deliverable: "交付成果範例",
    sample: "閱讀 AI 輸出樣本",
    open: "專案首頁",
    more: "探索所有測試情境",
    projects: {
      aeterna: {
        goal: "將對長壽研究的廣泛興趣整理為可供合格專業人員審閱的明確簡報。",
        people: "委託人選定研究問題，合格審查者在使用前確認來源與適用範圍。",
        ai: "整理公開來源研究、標記證據缺口，並草擬審查問題。",
        deliverable: "研究大綱、來源檢查清單及專業審查問題。",
        sample: "草稿 · 主題：如何評估一項長壽研究主張。章節：研究問題；來源及發表日期；研究族群；限制；供合格審查者回答的問題。證據欄位：[需要來源]。下一步：補齊並驗證來源清單。此文件不包含個人健康評估。",
      },
      galaxy: {
        goal: "為假設性的太空專案草擬加密邊緣運算概念。",
        people: "專案負責人定義資料，資安專家與基礎設施合作方審查概念。",
        ai: "草擬元件職責、信任邊界及尚待釐清的可行性問題。",
        deliverable: "架構簡報與提供潛在基礎設施合作方的檢查事項。",
        sample: "草稿 · 流程：資料擁有者 → 加密上傳 → 隔離工作 → 成果審查。待確認：託管可用性；金鑰保管；連線；復原；供應商能力。驗收：專家可辨識每個信任邊界。此文件不代表已部署軌道設施或已與供應商簽約。",
      },
      lunar: {
        goal: "以虛構月球地塊記錄設計科普主題目錄。",
        people: "編輯決定教育用途並確認每筆記錄的標示。",
        ai: "提出記錄結構、範例項目及發布檢查清單。",
        deliverable: "包含明確標示虛構項目的目錄規格。",
        sample: "草稿 · 記錄：DEMO-LUNAR-001。欄位：顯示名稱；虛構座標；研究主題；來源連結；編輯狀態。狀態：虛構樣本，來源待補。發布規則：將教育目錄記錄與所有權分開。此項目不授予土地所有權或採礦權。",
      },
      stardust: {
        goal: "以觀測樣本與人工審查流程定義天氣研究儀表板。",
        people: "委託人定義地區與用途，領域審查者確認資料來源及解讀。",
        ai: "整理輸入欄位並為不完整資料草擬審查備註。",
        deliverable: "儀表板簡報、輸入結構及審查備註樣本。",
        sample: "草稿 · 情境：一筆虛構天氣觀測需要審查。欄位：地區；時間；來源；觀測；可信度；審查者。缺少：已驗證來源及時間戳記。建議狀態：等待人工驗證。這是儀表板範例，並非即時預報、緊急警報或天氣控制成果。",
      },
      starlink: {
        goal: "為獨立技術人員準備衛星網路安裝需求樣本。",
        people: "委託人提供現場需求，合格技術人員評估地點並議定工作內容。",
        ai: "整理現場資料並草擬技術評估檢查清單。",
        deliverable: "現場需求簡報及取得服務報價前須釐清的問題。",
        sample: "草稿 · 地點：虛構的小型辦公室。所需輸入：地址；設備型號；安裝限制；電源及佈線路徑；現場進入許可。待確認：服務可用性、技術評估與報價。此樣本不構成安裝預約，也不代表與 Starlink 有合作關係。",
      },
    },
  },
};
