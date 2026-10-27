"""Patch Down syndrome + Africa i18n with markers matching current locale files."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AETERNA = ROOT / "frontend-app/src/locales/aeterna.ts"
LEGAL = ROOT / "frontend-app/src/locales/legal.ts"

a = AETERNA.read_text(encoding="utf-8")

INTENT_INSERTS = [
    (
        'intent25Body:\n      "Licensed cosmetic / fragrance partner fill informed by an optional DNA-vault hash — 8,900 ACP per bottle. Not a drug, not an aphrodisiac claim, not a guaranteed attraction outcome.",',
        'intent25Body:\n      "Licensed cosmetic / fragrance partner fill informed by an optional DNA-vault hash — 8,900 ACP per bottle. Not a drug, not an aphrodisiac claim, not a guaranteed attraction outcome.",\n    intent26Title: "Down syndrome support brief",\n    intent26Body:\n      "Licensed developmental pediatrics / genetics partner brief for Down syndrome support literacy — not a cure, not a diagnosis, not gene therapy sold by ANCAP.",',
    ),
    (
        'intent25Body:\n      "Лицензированный косметический / парфюмерный партнёрский розлив с учётом опционального хеша DNA-vault — 8 900 ACP за 1 флакон. Не лекарство, не афродизиак-клейм, не гарантия притяжения.",',
        'intent25Body:\n      "Лицензированный косметический / парфюмерный партнёрский розлив с учётом опционального хеша DNA-vault — 8 900 ACP за 1 флакон. Не лекарство, не афродизиак-клейм, не гарантия притяжения.",\n    intent26Title: "Поддержка при синдроме Дауна",\n    intent26Body:\n      "Бриф для лицензированного партнёра (детская неврология / генетика / развивающая педиатрия) — не излечение, не диагноз и не генная терапия от ANCAP.",',
    ),
    (
        'intent25Body:\n      "Ліцензований косметичний / парфумерний партнерський розлив з урахуванням опційного хешу DNA-vault — 8 900 ACP за 1 флакон. Не ліки, не афродизіак-клейм, не гарантія притягання.",',
        'intent25Body:\n      "Ліцензований косметичний / парфумерний партнерський розлив з урахуванням опційного хешу DNA-vault — 8 900 ACP за 1 флакон. Не ліки, не афродизіак-клейм, не гарантія притягання.",\n    intent26Title: "Підтримка при синдромі Дауна",\n    intent26Body:\n      "Бріф для ліцензованого партнера (дитяча неврологія / генетика) — не вилікування, не діагноз і не генна терапія від ANCAP.",',
    ),
    (
        'intent25Body:\n      "Lizenzierter Kosmetik- / Duftpartner-Abfuellung mit optionalem DNA-Vault-Hash — 8.900 ACP pro Flasche. Kein Arzneimittel, kein Aphrodisiakum-Claim, kein garantiertes Anziehungsergebnis.",',
        'intent25Body:\n      "Lizenzierter Kosmetik- / Duftpartner-Abfuellung mit optionalem DNA-Vault-Hash — 8.900 ACP pro Flasche. Kein Arzneimittel, kein Aphrodisiakum-Claim, kein garantiertes Anziehungsergebnis.",\n    intent26Title: "Down-Syndrom-Unterstuetzung",\n    intent26Body:\n      "Lizenzierter Partnerbrief (Entwicklungsmedizin / Genetik) — keine Heilung, keine Diagnose und keine Gentherapie durch ANCAP.",',
    ),
    (
        'intent25Body:\n      "持照化妝品／香水夥伴灌裝，可選 DNA vault 雜湊參考 — 每瓶 8,900 ACP。非藥品、非催情宣稱、非保證吸引結果。",',
        'intent25Body:\n      "持照化妝品／香水夥伴灌裝，可選 DNA vault 雜湊參考 — 每瓶 8,900 ACP。非藥品、非催情宣稱、非保證吸引結果。",\n    intent26Title: "唐氏症支援簡報",\n    intent26Body:\n      "持照發展兒科／遺傳學夥伴簡報——非治癒、非診斷、非 ANCAP 基因治療。",',
    ),
]

if "intent26Title" not in a:
    for old, new in INTENT_INSERTS:
        if old not in a:
            print("WARN skip intent:", old[:70])
            continue
        a = a.replace(old, new, 1)

EN_DS = '''
    downKicker: "Down syndrome · licensed clinician · support literacy",
    downTitle: "Down syndrome support",
    downPrice: "42,000 ACP",
    downLead: "ACP-settled brief for a licensed developmental pediatrics / genetics / child-neurology partner covering early intervention, family support, and school-adaptation literacy.",
    downDisclaimer: "ANCAP is not a clinic. This is not a cure for Down syndrome, not a diagnosis, not gene therapy or CRISPR sold by ANCAP, not a prescription, and not a guaranteed developmental or life outcome.",
    downAlt: "Down syndrome support literacy panel",
    downStep1Title: "Early support",
    downStep1Body: "Literacy on early intervention themes with the licensed clinician.",
    downStep2Title: "Family care",
    downStep2Body: "Caregiver coordination literacy — decisions stay with the family and clinician.",
    downStep3Title: "Learning path",
    downStep3Body: "School and skills adaptation literacy, not a guaranteed academic outcome.",
    downStep4Title: "Health partners",
    downStep4Body: "Partner screening for licensed developmental / genetics handoff.",
    downStep5Title: "Community",
    downStep5Body: "Peer and community support literacy — not a substitute for clinical care.",
    downStep6Title: "ACP receipt",
    downStep6Body: "Settled brief with proof receipt; clinical care remains with the licensed partner.",
    downCta: "Open Down syndrome support brief",
    downLegalCta: "Down syndrome support legal notice",
'''

RU_DS = '''
    downKicker: "Синдром Дауна · лицензированный клиницист · грамотность поддержки",
    downTitle: "Поддержка при синдроме Дауна",
    downPrice: "42 000 ACP",
    downLead: "ACP-бриф для лицензированного партнёра (развивающая педиатрия / генетика / детская неврология): ранняя поддержка, семья и школьная адаптация.",
    downDisclaimer: "ANCAP не клиника. Это не излечение синдрома Дауна, не диагноз, не генная терапия или CRISPR от ANCAP, не рецепт и не гарантия результата развития.",
    downAlt: "Панель грамотности поддержки при синдроме Дауна",
    downStep1Title: "Ранняя поддержка",
    downStep1Body: "Грамотность раннего вмешательства с лицензированным клиницистом.",
    downStep2Title: "Семья",
    downStep2Body: "Координация опекунов — решения остаются у семьи и врача.",
    downStep3Title: "Обучение",
    downStep3Body: "Школьная и навыковая адаптация — без гарантии академического исхода.",
    downStep4Title: "Медпартнёры",
    downStep4Body: "Скрининг лицензированного handoff (генетика / неврология).",
    downStep5Title: "Сообщество",
    downStep5Body: "Грамотность peer-поддержки — не замена клинической помощи.",
    downStep6Title: "Чек ACP",
    downStep6Body: "Оплаченный бриф с proof; клиника остаётся у лицензированного партнёра.",
    downCta: "Открыть бриф поддержки",
    downLegalCta: "Юр. текст: поддержка при синдроме Дауна",
'''

UK_DS = '''
    downKicker: "Синдром Дауна · ліцензований клініцист · грамотність підтримки",
    downTitle: "Підтримка при синдромі Дауна",
    downPrice: "42 000 ACP",
    downLead: "ACP-бріф для ліцензованого партнера (розвиткова педіатрія / генетика / дитяча неврологія).",
    downDisclaimer: "ANCAP не клініка. Це не вилікування синдрому Дауна, не діагноз, не генна терапія від ANCAP і не гарантія результату розвитку.",
    downAlt: "Панель грамотності підтримки при синдромі Дауна",
    downStep1Title: "Рання підтримка",
    downStep1Body: "Грамотність раннього втручання з ліцензованим клініцистом.",
    downStep2Title: "Сімʼя",
    downStep2Body: "Координація опікунів — рішення залишаються в сімʼї та лікаря.",
    downStep3Title: "Навчання",
    downStep3Body: "Шкільна адаптація — без гарантії академічного результату.",
    downStep4Title: "Медпартнери",
    downStep4Body: "Скринінг ліцензованого handoff.",
    downStep5Title: "Спільнота",
    downStep5Body: "Peer-підтримка — не заміна клінічної допомоги.",
    downStep6Title: "Чек ACP",
    downStep6Body: "Оплачений бріф з proof; клініка у ліцензованого партнера.",
    downCta: "Відкрити бріф підтримки",
    downLegalCta: "Юр. текст: підтримка при синдромі Дауна",
'''

DE_DS = '''
    downKicker: "Down-Syndrom · lizenzierter Kliniker · Unterstuetzungsliteralitaet",
    downTitle: "Down-Syndrom-Unterstuetzung",
    downPrice: "42.000 ACP",
    downLead: "ACP-Brief fuer einen lizenzierten Partner (Entwicklungsmedizin / Genetik / Kinderneurologie).",
    downDisclaimer: "ANCAP ist keine Klinik. Keine Heilung des Down-Syndroms, keine Diagnose, keine Gentherapie durch ANCAP und kein garantiertes Entwicklungsergebnis.",
    downAlt: "Down-Syndrom-Unterstuetzungspanel",
    downStep1Title: "Fruehe Foerderung",
    downStep1Body: "Literalitaet frueher Intervention mit lizenziertem Kliniker.",
    downStep2Title: "Familie",
    downStep2Body: "Pflegekoordination — Entscheidungen bleiben bei Familie und Kliniker.",
    downStep3Title: "Lernen",
    downStep3Body: "Schul- und Kompetenzanpassung — ohne Ergebnisgarantie.",
    downStep4Title: "Medizinpartner",
    downStep4Body: "Partner-Screening fuer lizenzierten Handoff.",
    downStep5Title: "Community",
    downStep5Body: "Peer-Unterstuetzung — kein Ersatz fuer klinische Versorgung.",
    downStep6Title: "ACP-Beleg",
    downStep6Body: "Bezahlter Brief mit Proof; Klinik bleibt beim Partner.",
    downCta: "Down-Syndrom-Brief oeffnen",
    downLegalCta: "Rechtshinweis Down-Syndrom-Unterstuetzung",
'''

ZH_DS = '''
    downKicker: "唐氏症 · 持照臨床醫師 · 支援素養",
    downTitle: "唐氏症支援",
    downPrice: "42,000 ACP",
    downLead: "向持照發展兒科／遺傳學／兒童神經科夥伴交接的 ACP 簡報：早期介入、家庭與就學適應素養。",
    downDisclaimer: "ANCAP 非診所。非唐氏症治癒、非診斷、非 ANCAP 基因治療、非處方、非保證發展結果。",
    downAlt: "唐氏症支援素養面板",
    downStep1Title: "早期支援",
    downStep1Body: "與持照臨床醫師的早期介入素養。",
    downStep2Title: "家庭",
    downStep2Body: "照顧者協調——決定權在家庭與醫師。",
    downStep3Title: "學習",
    downStep3Body: "就學與技能適應——無學業結果保證。",
    downStep4Title: "醫療夥伴",
    downStep4Body: "持照交接夥伴篩選。",
    downStep5Title: "社群",
    downStep5Body: "同儕支援素養——非臨床照護替代。",
    downStep6Title: "ACP 收據",
    downStep6Body: "已結算簡報與證明；臨床照護在夥伴端。",
    downCta: "開啟唐氏症支援簡報",
    downLegalCta: "唐氏症支援法律聲明",
'''

if "downKicker:" not in a:
    for marker, block in [
        ('adhdLegalCta: "ADHD support legal notice",', EN_DS),
        ('adhdLegalCta: "Юр. текст: поддержка при СДВГ",', RU_DS),
        ('adhdLegalCta: "Юр. текст: підтримка при СДУГ",', UK_DS),
        ('adhdLegalCta: "Rechtshinweis ADHS-Unterstützung",', DE_DS),
        ('adhdLegalCta: "ADHD 支援法律聲明",', ZH_DS),
    ]:
        if marker not in a:
            print("WARN missing aeterna marker", marker)
            continue
        a = a.replace(marker, marker + block, 1)

AETERNA.write_text(a, encoding="utf-8")
print("aeterna", "downKicker" in a, "intent26Title" in a)

L = LEGAL.read_text(encoding="utf-8")

EN_L = '''
    downSyndromeSupportLink: "Down syndrome support",
    hubCardDownSyndromeSupport: "Licensed clinician partner brief for Down syndrome support literacy — not a cure or gene therapy sold by ANCAP.",
    downSyndromeSupportKicker: "Legal / clinician / Down syndrome support literacy",
    downSyndromeSupportTitle: "Down syndrome support — licensed clinician partner rail",
    downSyndromeSupportIntro: "14 September 2026. ANCAP settles ACP for a licensed developmental pediatrics / genetics partner handoff. Not a cure.",
    ds1Title: "1. Platform role",
    ds1Body: "ANCAP is a commercial ACP platform. It settles payment and issues a partner handoff brief. ANCAP is not a hospital, clinic, or treating physician.",
    ds2Title: "2. Not a cure or treatment sold by ANCAP",
    ds2Body: "There is no ANCAP product that cures Down syndrome. This rail is support literacy and clinician matching only — not gene therapy, CRISPR, or a drug sold by ANCAP.",
    ds3Title: "3. Not a diagnosis or prescription",
    ds3Body: "Paying ACP does not diagnose trisomy 21 or any condition and does not prescribe medication, therapy protocols, or devices.",
    ds4Title: "4. Licensed clinicians only",
    ds4Body: "Clinical care occurs only under a licensed developmental pediatrics, genetics, or child-neurology partner after screening. Caregivers retain decision rights with that clinician.",
    ds5Title: "5. No outcome guarantee",
    ds5Body: "ANCAP does not guarantee developmental, academic, medical, or life outcomes.",
    ds6Title: "6. Not medical advice from ANCAP",
    ds6Body: "Catalog copy, AI briefs, and infographics are literacy / intake — not medical advice.",
    ds7Title: "7. Health and child data",
    ds7Body: "Do not upload sensitive child health data unless lawful basis and caregiver consent allow. Prefer hashes or redacted intake where possible.",
    ds8Title: "8. Relationship to other rails",
    ds8Body: "Distinct from ADHD support, Installation Project, and humanitarian aid. Each has its own legal notice.",
    ds9Title: "9. Payments",
    ds9Body: "42,000 ACP covers the desk brief and handoff. Ongoing clinical fees are billed by the licensed partner.",
    ds10Title: "10. Contact",
    ds10Body: "Questions: legal@ancap.cloud. Product: /aeterna#down-syndrome-support.",
    footerDownSyndromeSupport: "Down syndrome support",
'''

RU_L = '''
    downSyndromeSupportLink: "Поддержка при синдроме Дауна",
    hubCardDownSyndromeSupport: "Бриф для лицензированного клинициста по поддержке при синдроме Дауна — не излечение и не генная терапия от ANCAP.",
    downSyndromeSupportKicker: "Правовое / клиницист / грамотность поддержки при синдроме Дауна",
    downSyndromeSupportTitle: "Поддержка при синдроме Дауна — рельс лицензированного клинициста",
    downSyndromeSupportIntro: "14 сентября 2026. ANCAP принимает ACP за handoff к лицензированному партнёру. Не излечение.",
    ds1Title: "1. Роль платформы",
    ds1Body: "ANCAP — коммерческая ACP-платформа. Принимает оплату и выдаёт бриф handoff. ANCAP не больница и не лечащий врач.",
    ds2Title: "2. Не излечение и не терапия от ANCAP",
    ds2Body: "У ANCAP нет продукта, который излечивает синдром Дауна. Только грамотность поддержки и подбор клинициста — не генная терапия, CRISPR или лекарство от ANCAP.",
    ds3Title: "3. Не диагноз и не рецепт",
    ds3Body: "Оплата ACP не ставит диагноз трисомии 21 и не выписывает лекарства или протоколы.",
    ds4Title: "4. Только лицензированные клиницисты",
    ds4Body: "Клиническая помощь — только у лицензированного партнёра после скрининга. Решения остаются у опекунов и врача.",
    ds5Title: "5. Без гарантии исхода",
    ds5Body: "ANCAP не гарантирует результаты развития, обучения, медицины или жизни.",
    ds6Title: "6. Не медсовет от ANCAP",
    ds6Body: "Каталог, AI-брифы и инфографика — грамотность / intake, не медицинский совет.",
    ds7Title: "7. Данные о здоровье детей",
    ds7Body: "Не загружайте чувствительные данные без правового основания и согласия опекуна.",
    ds8Title: "8. Связь с другими рельсами",
    ds8Body: "Отдельно от СДВГ, Проекта Установки и гуманитарной помощи.",
    ds9Title: "9. Оплата",
    ds9Body: "42 000 ACP покрывают бриф и handoff. Дальнейшие клинические счета — у партнёра.",
    ds10Title: "10. Контакт",
    ds10Body: "Вопросы: legal@ancap.cloud. Продукт: /aeterna#down-syndrome-support.",
    footerDownSyndromeSupport: "Поддержка при синдроме Дауна",
'''

UK_L = '''
    downSyndromeSupportLink: "Підтримка при синдромі Дауна",
    hubCardDownSyndromeSupport: "Бріф для ліцензованого клініциста щодо підтримки при синдромі Дауна — не вилікування і не генна терапія від ANCAP.",
    downSyndromeSupportKicker: "Право / клініцист / грамотність підтримки при синдромі Дауна",
    downSyndromeSupportTitle: "Підтримка при синдромі Дауна — рейл ліцензованого клініциста",
    downSyndromeSupportIntro: "14 вересня 2026. ANCAP приймає ACP за handoff до ліцензованого партнера. Не вилікування.",
    ds1Title: "1. Роль платформи",
    ds1Body: "ANCAP — комерційна ACP-платформа. Приймає оплату і видає бріф handoff. ANCAP не лікарня і не лікуючий лікар.",
    ds2Title: "2. Не вилікування і не терапія від ANCAP",
    ds2Body: "У ANCAP немає продукту, що виліковує синдром Дауна. Лише грамотність підтримки і підбір клініциста.",
    ds3Title: "3. Не діагноз і не рецепт",
    ds3Body: "Оплата ACP не ставить діагноз трисомії 21 і не виписує ліки чи протоколи.",
    ds4Title: "4. Лише ліцензовані клініцисти",
    ds4Body: "Клінічна допомога — лише у ліцензованого партнера після скринінгу.",
    ds5Title: "5. Без гарантії результату",
    ds5Body: "ANCAP не гарантує результати розвитку, навчання, медицини чи життя.",
    ds6Title: "6. Не медпорада від ANCAP",
    ds6Body: "Каталог і AI-бріфи — грамотність / intake, не медична порада.",
    ds7Title: "7. Дані про здоровʼя дітей",
    ds7Body: "Не завантажуйте чутливі дані без правової підстави та згоди опікуна.",
    ds8Title: "8. Звʼязок з іншими рейлами",
    ds8Body: "Окремо від СДУГ, Проекту Установки та гуманітарної допомоги.",
    ds9Title: "9. Оплата",
    ds9Body: "42 000 ACP покривають бріф і handoff. Подальші клінічні рахунки — у партнера.",
    ds10Title: "10. Контакт",
    ds10Body: "Питання: legal@ancap.cloud. Продукт: /aeterna#down-syndrome-support.",
    footerDownSyndromeSupport: "Підтримка при синдромі Дауна",
'''

DE_L = '''
    downSyndromeSupportLink: "Down-Syndrom-Unterstuetzung",
    hubCardDownSyndromeSupport: "Partnerbrief eines lizenzierten Klinikers zur Down-Syndrom-Unterstuetzung — keine Heilung und keine Gentherapie durch ANCAP.",
    downSyndromeSupportKicker: "Recht / Kliniker / Down-Syndrom-Unterstuetzungsliteralitaet",
    downSyndromeSupportTitle: "Down-Syndrom-Unterstuetzung — lizenzierte Kliniker-Schiene",
    downSyndromeSupportIntro: "14. September 2026. ANCAP nimmt ACP fuer den Handoff an einen lizenzierten Partner an. Keine Heilung.",
    ds1Title: "1. Plattformrolle",
    ds1Body: "ANCAP ist eine kommerzielle ACP-Plattform. Sie nimmt Zahlung entgegen und stellt einen Partner-Handoff-Brief aus. ANCAP ist kein Krankenhaus und kein behandelnder Arzt.",
    ds2Title: "2. Keine Heilung durch ANCAP",
    ds2Body: "Es gibt kein ANCAP-Produkt, das das Down-Syndrom heilt. Nur Unterstuetzungsliteralitaet und Kliniker-Matching — keine Gentherapie oder CRISPR durch ANCAP.",
    ds3Title: "3. Keine Diagnose und kein Rezept",
    ds3Body: "ACP-Zahlung diagnostiziert keine Trisomie 21 und verschreibt keine Medikamente oder Protokolle.",
    ds4Title: "4. Nur lizenzierte Kliniker",
    ds4Body: "Klinische Versorgung erfolgt nur unter einem lizenzierten Partner nach Screening.",
    ds5Title: "5. Keine Ergebnisgarantie",
    ds5Body: "ANCAP garantiert keine Entwicklungs-, Schul-, Medizin- oder Lebensergebnisse.",
    ds6Title: "6. Keine medizinische Beratung durch ANCAP",
    ds6Body: "Katalog und AI-Briefe sind Literalitaet / Intake — keine medizinische Beratung.",
    ds7Title: "7. Kindergesundheitsdaten",
    ds7Body: "Keine sensiblen Kindergesundheitsdaten ohne Rechtsgrundlage und Sorgeberechtigten-Zustimmung hochladen.",
    ds8Title: "8. Bezug zu anderen Schienen",
    ds8Body: "Getrennt von ADHS-Unterstuetzung, Installation Project und humanitaerer Hilfe.",
    ds9Title: "9. Zahlung",
    ds9Body: "42.000 ACP decken Brief und Handoff. Weitere klinische Gebuehren stellt der Partner.",
    ds10Title: "10. Kontakt",
    ds10Body: "Fragen: legal@ancap.cloud. Produkt: /aeterna#down-syndrome-support.",
    footerDownSyndromeSupport: "Down-Syndrom-Unterstuetzung",
'''

ZH_L = '''
    downSyndromeSupportLink: "唐氏症支援",
    hubCardDownSyndromeSupport: "持照臨床醫師唐氏症支援素養簡報——非治癒、非 ANCAP 基因治療。",
    downSyndromeSupportKicker: "法律／臨床醫師／唐氏症支援素養",
    downSyndromeSupportTitle: "唐氏症支援 — 持照臨床醫師夥伴軌道",
    downSyndromeSupportIntro: "2026 年 9 月 14 日。ANCAP 以 ACP 結算持照發展兒科／遺傳學夥伴交接。非治癒。",
    ds1Title: "1. 平台角色",
    ds1Body: "ANCAP 為商業 ACP 平台，結算付款並出具夥伴交接簡報。ANCAP 非醫院、診所或主治醫師。",
    ds2Title: "2. 非 ANCAP 治癒或治療",
    ds2Body: "ANCAP 沒有治癒唐氏症的產品。本軌道僅為支援素養與臨床醫師媒合——非基因治療、CRISPR 或藥品。",
    ds3Title: "3. 非診斷或處方",
    ds3Body: "支付 ACP 不診斷第 21 對染色體三體症，亦不開立藥物、療程或器材。",
    ds4Title: "4. 僅限持照臨床醫師",
    ds4Body: "臨床照護僅在篩選後由持照發展兒科／遺傳學／兒童神經科夥伴提供。",
    ds5Title: "5. 無結果保證",
    ds5Body: "ANCAP 不保證發展、學業、醫療或人生結果。",
    ds6Title: "6. 非 ANCAP 醫療建議",
    ds6Body: "目錄文案、AI 簡報與資訊圖為素養／intake——非醫療建議。",
    ds7Title: "7. 兒童健康資料",
    ds7Body: "除非有合法依據與照顧者同意，否則勿上傳敏感兒童健康資料。",
    ds8Title: "8. 與其他軌道關係",
    ds8Body: "有別於 ADHD 支援、Installation Project 與人道援助。",
    ds9Title: "9. 付款",
    ds9Body: "42,000 ACP 涵蓋簡報與交接。後續臨床費用由持照夥伴收取。",
    ds10Title: "10. 聯絡",
    ds10Body: "問題：legal@ancap.cloud。產品：/aeterna#down-syndrome-support。",
    footerDownSyndromeSupport: "唐氏症支援",
'''

if "downSyndromeSupportLink:" not in L:
    for marker, block in [
        ('footerAdhdSupport: "ADHD / СДВГ support",', EN_L),
        ('footerAdhdSupport: "Поддержка при СДВГ",', RU_L),
        ('footerAdhdSupport: "Підтримка при СДУГ",', UK_L),
        ('footerAdhdSupport: "ADHS-Unterstützung",', DE_L),
        ('footerAdhdSupport: "ADHD 支援",', ZH_L),
    ]:
        if marker not in L:
            print("WARN legal marker", marker)
            continue
        L = L.replace(marker, marker + block, 1)

if "Africa aid corridors" not in L and "Africa-focused corridors" not in L:
    old = (
        "The /humanitarian desk sells ACP-settled aid briefs and partner handoffs "
        "(food, water, nutrition, warm clothing, medical supplies via licensed channels, livelihood matching)."
    )
    new = (
        "The /humanitarian desk sells ACP-settled aid briefs and partner handoffs "
        "(food, water, nutrition, warm clothing, medical supplies via licensed channels, livelihood matching), "
        "including Africa-focused corridors listed on /humanitarian."
    )
    if old in L:
        L = L.replace(old, new, 1)
        print("legal Africa note patched")
    else:
        print("WARN Africa hum body not found")

LEGAL.write_text(L, encoding="utf-8")
print("legal", "downSyndromeSupportLink" in L, L.count("downSyndromeSupportLink"))
