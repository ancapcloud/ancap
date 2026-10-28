# -*- coding: utf-8 -*-
"""Patch aeterna + legal locales for Installation Project SKU."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AETERNA = ROOT / "frontend-app" / "src" / "locales" / "aeterna.ts"
LEGAL = ROOT / "frontend-app" / "src" / "locales" / "legal.ts"

AETERNA_BLOCKS = {
    "en": '''
    intent24Title: "Installation Project (neonatal nutrition + hyperbaric)",
    intent24Body:
      "Licensed neonatology / infant-nutrition partner brief for high-protein milk-line and neonatal hyperbaric-chamber literacy — 72,000 ACP. Not formula sold by ANCAP, not home HBO, not a guaranteed clinical outcome.",

    ipCta: "Open Installation Project brief",
    ipInsuranceCta: "Neonatal install insurance",
    ipKicker: "Installation Project · neonatal · GMP literacy",
    ipTitle: "Installation Project — healthy start, partner clinic only",
    ipPrice: "72,000 ACP",
    ipLead:
      "Two partner rails in one brief: high-protein natural-synthetic infant milk production literacy (conceptual ~1,000 L/day; liquid and dry formats; whey/casein/plant proteins, Omega-3/6, vitamins and minerals) and a neonatal hyperbaric chamber (1.5–2.0 ATA; 36–37 °C; 1–2 newborns; vitals monitoring).",
    ipDisclaimer:
      "ANCAP does not manufacture infant formula, does not operate a dairy plant or NICU, does not sell a CE/FDA hyperbaric device, and does not claim guaranteed reduction of rickets, anemia, infection, or developmental delay. GMP / medical-standards callouts and capacities on the artwork are partner literacy. Physical production and clinical sessions occur only under licensed partners after screening.",
    ipLegalCta: "Installation Project legal notice",
    ipAlt:
      "Infographic of Installation Project: high-protein infant milk production line and neonatal hyperbaric chamber. Conceptual architecture for licensed neonatology / nutrition partners — not formula or a CE/FDA device sold by ANCAP.",
    ipStep1Title: "Milk line",
    ipStep1Body: "Prep → mix → pasteurize → enrich → pack. Conceptual ~1,000 L/day literacy.",
    ipStep2Title: "Nutrition",
    ipStep2Body: "High protein (3–4 g / 100 ml literacy), non-GMO / no-preservative framing — not a product claim.",
    ipStep3Title: "Hyperbaric",
    ipStep3Body: "1.5–2.0 ATA, 36–37 °C, vitals monitoring literacy. Not home HBO.",
    ipStep4Title: "Handoff",
    ipStep4Body: "ACP buys a partner brief — not a plant title deed or device clearance.",
''',
    "ru": '''
    intent24Title: "Проект Установки (питание + барокамера)",
    intent24Body:
      "Бриф лицензированного неонатологического / нутриционного партнёра по линии высокобелкового молока и неонатальной барокамере — 72 000 ACP. Не смесь от ANCAP, не домашняя HBO, не гарантия клинического исхода.",

    ipCta: "Открыть бриф Проекта Установки",
    ipInsuranceCta: "Страховка neonatal install",
    ipKicker: "Проект Установки · неонатология · грамотность GMP",
    ipTitle: "Проект Установки — здоровое начало, только партнёрская клиника",
    ipPrice: "72 000 ACP",
    ipLead:
      "Два рейла в одном брифе: производство натурально-синтетического высокобелкового молока для младенцев (концептуально до ~1 000 л/сутки; жидкое и сухое; сыворотка/казеин/растительные белки, Omega-3/6, витамины и минералы) и барокамера для недоношенных (1,5–2,0 ATA; 36–37 °C; 1–2 новорождённых; мониторинг витальных показателей).",
    ipDisclaimer:
      "ANCAP не производит детскую смесь, не ведёт молочный завод и не NICU, не продаёт изделие CE/FDA для HBO и не обещает снижение рахита, анемии, инфекций или задержки развития. Пометки GMP и мощности на инфографике — грамотность партнёра. Производство и сеансы — только у лицензированных партнёров после скрининга.",
    ipLegalCta: "Юр. текст Проекта Установки",
    ipAlt:
      "Инфографика Проекта Установки: линия высокобелкового детского молока и неонатальная барокамера. Концептуальная архитектура для лицензированных партнёров.",
    ipStep1Title: "Линия молока",
    ipStep1Body: "Подготовка → смешивание → пастеризация → обогащение → фасовка. Грамотность ~1 000 л/сутки.",
    ipStep2Title: "Питание",
    ipStep2Body: "Высокий белок (3–4 г / 100 мл), без ГМО / консервантов на картинке — не претензия продукта.",
    ipStep3Title: "Барокамера",
    ipStep3Body: "1,5–2,0 ATA, 36–37 °C, мониторинг. Не домашняя HBO.",
    ipStep4Title: "Передача",
    ipStep4Body: "ACP покупает бриф партнёра — не право на завод и не clearance устройства.",
''',
    "uk": '''
    intent24Title: "Проєкт Установки (харчування + барокамера)",
    intent24Body:
      "Бриф ліцензованого неонатологічного / нутриційного партнера щодо лінії високобілкового молока та неонатальної барокамери — 72 000 ACP.",

    ipCta: "Відкрити бриф Проєкту Установки",
    ipInsuranceCta: "Страхування neonatal install",
    ipKicker: "Проєкт Установки · неонатологія · грамотність GMP",
    ipTitle: "Проєкт Установки — здоровий старт, лише партнерська клініка",
    ipPrice: "72 000 ACP",
    ipLead:
      "Два рейли в одному брифі: високобілкове натурально-синтетичне молоко для немовлят (концептуально ~1 000 л/добу) та барокамера для недоношених (1,5–2,0 ATA; 36–37 °C).",
    ipDisclaimer:
      "ANCAP не виробляє суміш, не веде завод чи NICU і не гарантує клінічний результат. Сеанси — лише у ліцензованих партнерів після скринінгу.",
    ipLegalCta: "Юр. текст Проєкту Установки",
    ipAlt:
      "Інфографіка Проєкту Установки: лінія молока та неонатальна барокамера. Концептуальна архітектура для ліцензованих партнерів.",
    ipStep1Title: "Лінія молока",
    ipStep1Body: "Підготовка → змішування → пастеризація → збагачення → фасування.",
    ipStep2Title: "Харчування",
    ipStep2Body: "Високий білок, без ГМО / консервантів на зображенні — не претензія продукту.",
    ipStep3Title: "Барокамера",
    ipStep3Body: "1,5–2,0 ATA, 36–37 °C, моніторинг. Не домашня HBO.",
    ipStep4Title: "Передача",
    ipStep4Body: "ACP купує бриф партнера — не титул заводу.",
''',
    "de": '''
    intent24Title: "Installationsprojekt (neonatale Ernährung + Druckkammer)",
    intent24Body:
      "Lizenziertes Neonatologie-/Ernährungs-Partnerbriefing für Hochprotein-Milchlinie und neonatale Druckkammer — 72.000 ACP.",

    ipCta: "Installationsprojekt-Brief öffnen",
    ipInsuranceCta: "Neonatal-Install-Versicherung",
    ipKicker: "Installationsprojekt · Neonatologie · GMP-Literalität",
    ipTitle: "Installationsprojekt — gesunder Start, nur Partnerklinik",
    ipPrice: "72.000 ACP",
    ipLead:
      "Zwei Schienen in einem Briefing: hochproteinreiche natur-synthetische Säuglingsmilch (konzeptuell ~1.000 L/Tag) und neonatale Druckkammer (1,5–2,0 ATA; 36–37 °C).",
    ipDisclaimer:
      "ANCAP stellt keine Säuglingsnahrung her, betreibt keine Molkerei/NICU und gibt keine klinische Erfolgsgarantie. Sitzungen nur bei lizenzierten Partnern nach Screening.",
    ipLegalCta: "Rechtshinweis Installationsprojekt",
    ipAlt:
      "Infografik Installationsprojekt: Milchlinie und neonatale Druckkammer. Konzeptuelle Architektur für lizenzierte Partner.",
    ipStep1Title: "Milchlinie",
    ipStep1Body: "Vorbereitung → Mischen → Pasteurisierung → Anreicherung → Abfüllung.",
    ipStep2Title: "Ernährung",
    ipStep2Body: "Hoher Proteinanteil, Non-GMO-/ohne-Konservierungsstoffe-Framing — kein Produktclaim.",
    ipStep3Title: "Druckkammer",
    ipStep3Body: "1,5–2,0 ATA, 36–37 °C, Monitoring. Kein Heim-HBO.",
    ipStep4Title: "Übergabe",
    ipStep4Body: "ACP kauft ein Partnerbriefing — kein Werktitel.",
''',
    "zh": '''
    intent24Title: "安裝專案（新生兒營養＋高壓艙）",
    intent24Body:
      "持照新生兒科／營養夥伴簡報：高蛋白奶線與新生兒高壓艙素養 — 72,000 ACP。",

    ipCta: "開啟安裝專案簡報",
    ipInsuranceCta: "新生兒安裝保險",
    ipKicker: "安裝專案 · 新生兒 · GMP 素養",
    ipTitle: "安裝專案 — 健康起步，僅限夥伴診所",
    ipPrice: "72,000 ACP",
    ipLead:
      "單一簡報兩條軌道：高蛋白天然－合成嬰兒奶線（概念約 1,000 升／日）與新生兒高壓艙（1.5–2.0 ATA；36–37 °C）。",
    ipDisclaimer:
      "ANCAP 不製造配方奶、不營運乳廠／NICU，亦不保證臨床結果。實體療程僅在持照夥伴篩檢後進行。",
    ipLegalCta: "安裝專案法律聲明",
    ipAlt:
      "安裝專案資訊圖：高蛋白嬰兒奶生產線與新生兒高壓艙。持照夥伴的概念架構。",
    ipStep1Title: "奶線",
    ipStep1Body: "備料 → 混合 → 巴氏殺菌 → 強化 → 包裝。",
    ipStep2Title: "營養",
    ipStep2Body: "高蛋白、非基改／無防腐劑為圖示素養，非產品主張。",
    ipStep3Title: "高壓艙",
    ipStep3Body: "1.5–2.0 ATA、36–37 °C、監測。非家用 HBO。",
    ipStep4Title: "交接",
    ipStep4Body: "ACP 購買夥伴簡報 — 非廠房產權。",
''',
}

LEGAL_BLOCKS = {
    "en": '''
    installationProjectLink: "Installation Project",
    hubCardInstallationProject:
      "Licensed neonatology / infant-nutrition partner brief for high-protein milk-line and neonatal hyperbaric literacy. Not formula sold by ANCAP, not home HBO, not a guaranteed outcome.",
    installationProjectKicker: "Legal / neonatology / infant nutrition literacy",
    installationProjectTitle: "Installation Project — licensed neonatal partner rail",
    installationProjectIntro:
      "How ANCAP frames the Installation Project (Проект Установки) SKU as of 13 September 2026. These pages sell ACP-settled partner briefs, not infant formula, not dairy plants, and not CE/FDA hyperbaric devices.",
    ip1Title: "1. Platform role",
    ip1Body:
      "ANCAP provides ACP settlement, consult briefs, and licensed-partner matching. ANCAP does not manufacture infant formula, does not operate a milk plant or NICU, and does not practice neonatology.",
    ip2Title: "2. Not a formula product sold by ANCAP",
    ip2Body:
      "Composition callouts (whey, casein, plant proteins, Omega-3/6, vitamins, minerals), non-GMO, and preservative-free framing on the artwork are partner literacy — not a marketed infant formula SKU from ANCAP.",
    ip3Title: "3. Not a CE/FDA hyperbaric device",
    ip3Body:
      "Operating pressure (1.5–2.0 ATA), temperature (36–37 °C), capacity, and monitoring icons are architecture literacy. ANCAP does not sell a cleared hyperbaric chamber or home HBO kit.",
    ip4Title: "4. Forbidden outcome claims",
    ip4Body:
      "ANCAP does not guarantee reduced rickets, anemia, infection, growth delay, or developmental outcomes. Capacity figures (e.g. ~1,000 L/day) are conceptual partner literacy.",
    ip5Title: "5. Licensed partners only",
    ip5Body:
      "Any production run or clinical hyperbaric session is a partner act after screening under applicable food, drug, and medical-device law. Users must not treat these pages as a DIY plant or home chamber kit.",
    ip6Title: "6. GMP / medical-standards literacy, not a certificate",
    ip6Body:
      "References to GMP and medical standards describe partner expectations. They are not an ANCAP-issued manufacturing certificate or regulatory approval.",
    ip7Title: "7. Not medical or nutrition advice",
    ip7Body:
      "Catalog copy is informational architecture literacy. It is not infant feeding advice, a prescription, or a clinical protocol.",
    ip8Title: "8. Insurance relationship",
    ip8Body:
      "Parametric ACP cover class neonatal_install on /insurance may reference Installation Project intakes. It is not medical malpractice insurance, not a formula warranty, and not a CE/FDA device policy.",
    ip9Title: "9. Payments",
    ip9Body:
      "ACP buys a consult brief and partner match at 72,000 ACP — not plant title, not device clearance, and not a refundable clinical outcome. Refunds follow /legal/refunds.",
    ip10Title: "10. Contact",
    ip10Body:
      "Legal notices: legal@ancap.cloud. Product: /aeterna#installation-project. Insurance: /insurance. Related notices: /legal/terms, /legal/risk.",
    footerInstallationProject: "Installation Project",
''',
    "ru": '''
    installationProjectLink: "Проект Установки",
    hubCardInstallationProject:
      "Бриф лицензированного неонатологического / нутриционного партнёра по высокобелковому молоку и неонатальной барокамере. Не смесь от ANCAP, не домашняя HBO, не гарантия исхода.",
    installationProjectKicker: "Юридическое / неонатология / детское питание",
    installationProjectTitle: "Проект Установки — лицензированный неонатальный рейл",
    installationProjectIntro:
      "Как ANCAP оформляет SKU «Проект Установки» на 13 сентября 2026. Эти страницы продают ACP-брифы партнёра, а не детскую смесь, не молочный завод и не изделие CE/FDA для HBO.",
    ip1Title: "1. Роль платформы",
    ip1Body:
      "ANCAP даёт расчёт ACP, брифы и матч лицензированного партнёра. ANCAP не производит смесь, не ведёт завод или NICU и не практикует неонатологию.",
    ip2Title: "2. Не смесь от ANCAP",
    ip2Body:
      "Состав, «без ГМО» и «без консервантов» на инфографике — грамотность партнёра, не маркетинговый SKU смеси ANCAP.",
    ip3Title: "3. Не изделие CE/FDA для HBO",
    ip3Body:
      "Давление 1,5–2,0 ATA, температура 36–37 °C и мониторинг — архитектурная грамотность. ANCAP не продаёт cleared-камеру и не домашний HBO-набор.",
    ip4Title: "4. Запрещённые обещания исхода",
    ip4Body:
      "ANCAP не гарантирует снижение рахита, анемии, инфекций или задержки развития. Мощность ~1 000 л/сутки — концептуальная грамотность.",
    ip5Title: "5. Только лицензированные партнёры",
    ip5Body:
      "Производство и клинические сеансы — акт партнёра после скрининга по применимому праву. Страницы не DIY-завод и не домашний комплект.",
    ip6Title: "6. GMP — грамотность, не сертификат ANCAP",
    ip6Body:
      "Упоминания GMP и медстандартов описывают ожидания к партнёру, а не сертификат или approval от ANCAP.",
    ip7Title: "7. Не медсовет и не советы по вскармливанию",
    ip7Body:
      "Каталог — информационная архитектурная грамотность, не назначение и не клинический протокол.",
    ip8Title: "8. Связь со страховкой",
    ip8Body:
      "Класс покрытия neonatal_install на /insurance может ссылаться на интейки Проекта Установки. Это не страховка от врачебной ошибки и не гарантия смеси.",
    ip9Title: "9. Платежи",
    ip9Body:
      "ACP покупает бриф и матч партнёра за 72 000 ACP — не титул завода и не clearance устройства. Возвраты — /legal/refunds.",
    ip10Title: "10. Контакты",
    ip10Body:
      "Юр. уведомления: legal@ancap.cloud. Продукт: /aeterna#installation-project. Страховка: /insurance. Связанные: /legal/terms, /legal/risk.",
    footerInstallationProject: "Проект Установки",
''',
    "uk": '''
    installationProjectLink: "Проєкт Установки",
    hubCardInstallationProject:
      "Бриф ліцензованого неонатологічного / нутриційного партнера. Не суміш від ANCAP, не домашня HBO, не гарантія результату.",
    installationProjectKicker: "Юридичне / неонатологія / дитяче харчування",
    installationProjectTitle: "Проєкт Установки — ліцензований неонатальний рейл",
    installationProjectIntro:
      "Як ANCAP оформлює SKU «Проєкт Установки» станом на 13 вересня 2026. Сторінки продають ACP-брифи партнера, а не суміш і не CE/FDA-камеру.",
    ip1Title: "1. Роль платформи",
    ip1Body:
      "ANCAP дає розрахунок ACP, брифи та матч ліцензованого партнера. ANCAP не виробляє суміш і не практикує неонатологію.",
    ip2Title: "2. Не суміш від ANCAP",
    ip2Body:
      "Склад і «без ГМО» на інфографіці — грамотність партнера, не маркетинговий SKU суміші ANCAP.",
    ip3Title: "3. Не виріб CE/FDA для HBO",
    ip3Body:
      "Тиск 1,5–2,0 ATA і температура 36–37 °C — архітектурна грамотність. ANCAP не продає cleared-камеру.",
    ip4Title: "4. Заборонені обіцянки",
    ip4Body:
      "ANCAP не гарантує зниження рахіту, анемії чи затримки розвитку.",
    ip5Title: "5. Лише ліцензовані партнери",
    ip5Body:
      "Виробництво та клінічні сеанси — акт партнера після скринінгу.",
    ip6Title: "6. GMP — грамотність, не сертифікат ANCAP",
    ip6Body:
      "Згадки GMP описують очікування до партнера, а не approval від ANCAP.",
    ip7Title: "7. Не медична порада",
    ip7Body:
      "Каталог — інформаційна грамотність, не призначення.",
    ip8Title: "8. Зв’язок зі страхуванням",
    ip8Body:
      "Клас neonatal_install на /insurance може посилатися на інтейки Проєкту Установки. Це не страховка від лікарської помилки.",
    ip9Title: "9. Платежі",
    ip9Body:
      "ACP купує бриф за 72 000 ACP. Повернення — /legal/refunds.",
    ip10Title: "10. Контакти",
    ip10Body:
      "legal@ancap.cloud · /aeterna#installation-project · /insurance",
    footerInstallationProject: "Проєкт Установки",
''',
    "de": '''
    installationProjectLink: "Installationsprojekt",
    hubCardInstallationProject:
      "Lizenziertes Neonatologie-/Ernährungs-Partnerbriefing. Keine Säuglingsnahrung von ANCAP, kein Heim-HBO, keine Erfolgsgarantie.",
    installationProjectKicker: "Recht / Neonatologie / Säuglingsernährung",
    installationProjectTitle: "Installationsprojekt — lizenzierte neonatale Schiene",
    installationProjectIntro:
      "Wie ANCAP die SKU Installationsprojekt zum 13. September 2026 rahmt. Diese Seiten verkaufen ACP-Partnerbriefs, keine Säuglingsnahrung und kein CE/FDA-Druckkammergerät.",
    ip1Title: "1. Plattformrolle",
    ip1Body:
      "ANCAP stellt ACP-Settlement, Briefings und Partner-Matching bereit. ANCAP stellt keine Säuglingsnahrung her und praktiziert keine Neonatologie.",
    ip2Title: "2. Keine ANCAP-Säuglingsnahrung",
    ip2Body:
      "Zusammensetzung und Non-GMO-Framing auf der Infografik sind Partnerliteralität — kein vermarktetes ANCAP-Formula-SKU.",
    ip3Title: "3. Kein CE/FDA-Druckkammergerät",
    ip3Body:
      "1,5–2,0 ATA und 36–37 °C sind Architekturliteralität. ANCAP verkauft keine freigegebene Druckkammer.",
    ip4Title: "4. Verbotene Outcome-Claims",
    ip4Body:
      "ANCAP garantiert keine Reduktion von Rachitis, Anämie oder Entwicklungsverzögerung.",
    ip5Title: "5. Nur lizenzierte Partner",
    ip5Body:
      "Produktion und klinische Sitzungen sind Partnerakte nach Screening.",
    ip6Title: "6. GMP-Literalität, kein ANCAP-Zertifikat",
    ip6Body:
      "GMP-Hinweise beschreiben Partnererwartungen, keine ANCAP-Zulassung.",
    ip7Title: "7. Keine medizinische Beratung",
    ip7Body:
      "Katalogtext ist Architekturliteralität, kein Rezept.",
    ip8Title: "8. Versicherungsbezug",
    ip8Body:
      "Coverage-Klasse neonatal_install auf /insurance kann Installationsprojekt-Intakes referenzieren. Keine Malpractice-Police.",
    ip9Title: "9. Zahlungen",
    ip9Body:
      "ACP kauft ein Briefing für 72.000 ACP. Rückerstattungen: /legal/refunds.",
    ip10Title: "10. Kontakt",
    ip10Body:
      "legal@ancap.cloud · /aeterna#installation-project · /insurance",
    footerInstallationProject: "Installationsprojekt",
''',
    "zh": '''
    installationProjectLink: "安裝專案",
    hubCardInstallationProject:
      "持照新生兒科／營養夥伴簡報。非 ANCAP 配方奶、非家用 HBO、非結果保證。",
    installationProjectKicker: "法律／新生兒／嬰兒營養素養",
    installationProjectTitle: "安裝專案 — 持照新生兒夥伴軌道",
    installationProjectIntro:
      "ANCAP 於 2026 年 9 月 13 日對「安裝專案」SKU 的定位：販售 ACP 夥伴簡報，而非配方奶或 CE/FDA 高壓艙。",
    ip1Title: "1. 平台角色",
    ip1Body:
      "ANCAP 提供 ACP 結算、簡報與持照夥伴配對。ANCAP 不製造配方奶，亦不執業新生兒科。",
    ip2Title: "2. 非 ANCAP 配方奶",
    ip2Body:
      "成分與非基改／無防腐劑圖示為夥伴素養，非 ANCAP 市售配方 SKU。",
    ip3Title: "3. 非 CE/FDA 高壓艙",
    ip3Body:
      "1.5–2.0 ATA 與 36–37 °C 為架構素養。ANCAP 不販售已核准高壓艙。",
    ip4Title: "4. 禁止結果主張",
    ip4Body:
      "ANCAP 不保證降低佝僂病、貧血或發育遲緩。",
    ip5Title: "5. 僅限持照夥伴",
    ip5Body:
      "生產與臨床療程為夥伴行為，須經篩檢。",
    ip6Title: "6. GMP 素養，非 ANCAP 證書",
    ip6Body:
      "GMP 提及描述夥伴期待，非 ANCAP 核發核准。",
    ip7Title: "7. 非醫療建議",
    ip7Body:
      "目錄文案為架構素養，非處方。",
    ip8Title: "8. 與保險的關係",
    ip8Body:
      "/insurance 的 neonatal_install 可對應安裝專案進件。非醫療疏失保單。",
    ip9Title: "9. 付款",
    ip9Body:
      "ACP 以 72,000 ACP 購買簡報。退款見 /legal/refunds。",
    ip10Title: "10. 聯絡",
    ip10Body:
      "legal@ancap.cloud · /aeterna#installation-project · /insurance",
    footerInstallationProject: "安裝專案",
''',
}


def _insert_after_marker(text: str, marker: str, block: str, label: str) -> str:
    if "installationProjectLink" in text and label == "legal":
        return text
    if "intent24Title" in text and label == "aeterna":
        return text
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit(f"marker not found for {label}: {marker[:80]!r}")
    end = idx + len(marker)
    return text[:end] + "\n" + block.rstrip() + "\n" + text[end:]


def patch_aeterna() -> None:
    text = AETERNA.read_text(encoding="utf-8")
    if "intent24Title" in text:
        print("aeterna already patched")
        return
    # Insert after each language's teStep4Body block (last te key before next section)
    # Find teStep4Body occurrences in order (en, ru, uk, de, zh)
    langs = ["en", "ru", "uk", "de", "zh"]
    needle = "teStep4Body:"
    positions = []
    start = 0
    while True:
        i = text.find(needle, start)
        if i < 0:
            break
        # find end of that line's property (closing quote+comma newline)
        line_end = text.find("\n", i)
        # may be multi-line; for teStep4Body it's single line
        positions.append(line_end + 1)
        start = line_end + 1
    if len(positions) != 5:
        raise SystemExit(f"expected 5 teStep4Body, got {len(positions)}")
    # insert from end so offsets stay valid
    for lang, pos in zip(reversed(langs), reversed(positions)):
        block = AETERNA_BLOCKS[lang]
        text = text[:pos] + "\n" + block.lstrip("\n") + text[pos:]
    # Also extend homeLead / payLead lightly for EN only if teleport mention exists
    old_te = "or a teleport-earphones medevac fiction brief at 58,000 ACP"
    new_te = (
        "or a teleport-earphones medevac fiction brief at 58,000 ACP, "
        "or an Installation Project neonatal nutrition / hyperbaric brief at 72,000 ACP"
    )
    if old_te in text and "Installation Project neonatal" not in text:
        text = text.replace(old_te, new_te, 1)
    old_pay = "teleport-earphones medevac fiction brief is 58,000 ACP"
    new_pay = (
        "teleport-earphones medevac fiction brief is 58,000 ACP; "
        "Installation Project neonatal nutrition / hyperbaric brief is 72,000 ACP"
    )
    if old_pay in text and "Installation Project neonatal nutrition" not in text.split(old_pay)[0][-200:]:
        text = text.replace(old_pay, new_pay, 1)
    AETERNA.write_text(text, encoding="utf-8")
    print("patched aeterna.ts")


def patch_legal() -> None:
    text = LEGAL.read_text(encoding="utf-8")
    if "installationProjectLink" in text:
        print("legal already patched")
        return
    langs = ["en", "ru", "uk", "de", "zh"]
    needle = "footerTeleportEarphones:"
    positions = []
    start = 0
    while True:
        i = text.find(needle, start)
        if i < 0:
            break
        line_end = text.find("\n", i)
        positions.append(line_end + 1)
        start = line_end + 1
    if len(positions) != 5:
        raise SystemExit(f"expected 5 footerTeleportEarphones, got {len(positions)}")
    for lang, pos in zip(reversed(langs), reversed(positions)):
        block = LEGAL_BLOCKS[lang]
        text = text[:pos] + "\n" + block.lstrip("\n") + text[pos:]
    LEGAL.write_text(text, encoding="utf-8")
    print("patched legal.ts")


if __name__ == "__main__":
    patch_aeterna()
    patch_legal()
