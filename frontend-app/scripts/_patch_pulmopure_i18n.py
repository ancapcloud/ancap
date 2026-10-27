# -*- coding: utf-8 -*-
"""Insert PulmoPure subscription i18n into aeterna.ts + legal.ts."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src" / "locales"
LANGS = ["en", "ru", "uk", "de", "zh-Hant"]


def lang_key(lang: str) -> str:
    return f'  "{lang}": {{' if lang == "zh-Hant" else f"  {lang}: {{"


def bounds(text: str, lang: str) -> tuple[int, int]:
    start = text.find(lang_key(lang))
    if start < 0:
        raise SystemExit(f"missing {lang}")
    ends = []
    for other in LANGS:
        if other == lang:
            continue
        p = text.find(lang_key(other), start + 1)
        if p > 0:
            ends.append(p)
    return start, min(ends) if ends else len(text)


def insert_after_marker(section: str, marker: str, close: str, block: str) -> str:
    idx = section.find(marker)
    if idx < 0:
        raise SystemExit(f"no {marker}")
    after = section[idx:]
    c = after.find(close)
    if c < 0:
        raise SystemExit(f"cannot close {marker}")
    at = idx + c + len(close)
    return section[:at] + block + "\n" + section[at:]


INTENTS = {
    "en": (
        '    intent21Title: "PulmoPure lung-care subscription",\n'
        "    intent21Body:\n"
        '      "Licensed pulmonology / respiratory clinic subscription for gas-vibration and lavender-oil '
        "architecture literacy. 14,000 ACP / month. Not a CE/FDA device, not ozone therapy, not medical-gas "
        'compounding, and not a guaranteed tar-clearance or clean-lungs outcome.",\n'
    ),
    "ru": (
        '    intent21Title: "Подписка PulmoPure (лёгкие)",\n'
        "    intent21Body:\n"
        '      "Подписка лицензированной пульмонологической / респираторной клиники: газо-вибрация и '
        "лавандовый атомайзер как грамотность. 14 000 ACP / месяц. Не изделие CE/FDA, не озонотерапия, "
        'не компаундинг медгазов и не гарантия «чистых лёгких».",\n'
    ),
    "uk": (
        '    intent21Title: "Підписка PulmoPure (легені)",\n'
        "    intent21Body:\n"
        '      "Підписка ліцензованої пульмонологічної / респіраторної клініки: газо-вібрація та лавандовий '
        "атомайзер як грамотність. 14 000 ACP / місяць. Не виріб CE/FDA, не озонотерапія, не компаундинг "
        'медгазів і не гарантія «чистих легень».",\n'
    ),
    "de": (
        '    intent21Title: "PulmoPure Lungenpflege-Abo",\n'
        "    intent21Body:\n"
        '      "Lizenziertes Pneumologie-/Atemwegs-Klinik-Abo für Gasvibrations- und Lavendelöl-Literalität. '
        "14.000 ACP / Monat. Kein CE/FDA-Gerät, keine Ozontherapie, kein Medizingas-Compounding und keine "
        'garantierte Teerklärung oder „saubere Lungen“.",\n'
    ),
    "zh-Hant": (
        '    intent21Title: "PulmoPure 肺部照護訂閱",\n'
        "    intent21Body:\n"
        '      "持照肺科／呼吸科診所訂閱：氣體振動與薰衣草霧化架構素養。每月 14,000 ACP。'
        '非 CE/FDA 器材、非臭氧治療、非醫用氣體複配，亦非保證清除焦油或「潔淨肺部」。",\n'
    ),
}

PANELS = {
    "en": """    ppCta: "Subscribe to PulmoPure rail",
    ppKicker: "Subscription · gas vibration · licensed pulmonology",
    ppTitle: "PulmoPure — clean-lungs literacy, partner clinic only",
    ppPrice: "14,000 ACP / month",
    ppPeriods: "38,000 ACP / quarter · 128,000 ACP / year",
    ppLead:
      "A conceptual handheld system: silicone mouthpiece, gas-vibration generator, medical-gas mix literacy, lavender-oil atomizer, filter unit, and Soft / Standard / Intensive modes. Infographic before/after alveoli and 'clean lungs' slogans are protocol literacy — AETERNA does not sell a CE/FDA device, does not compound ozone or medical gases, and does not promise tar clearance.",
    ppDisclaimer:
      "ANCAP does not manufacture PulmoPure, does not practice pulmonology, and does not claim CE/FDA device status or safe home ozone inhalation. Soft / Standard / Intensive modes and package contents on the artwork are partner literacy. Physical sessions occur only under a licensed clinician after screening (asthma, COPD, pneumothorax history, pregnancy, ozone sensitivity).",
    ppLegalCta: "PulmoPure legal notice",
    ppAlt:
      "Infographic of the PulmoPure handheld lung-care system: gas vibration, medical-gas mix literacy, lavender oils, Soft / Standard / Intensive modes, and before/after alveoli diagrams. Conceptual architecture for licensed pulmonology partners — not a CE/FDA device or ozone therapy sold by ANCAP.",
    ppStep1Title: "Vibration",
    ppStep1Body: "Controlled gas pulsation literacy. Not a guaranteed tar peel.",
    ppStep2Title: "Gas mix",
    ppStep2Body: "Partner medical-gas protocol literacy. Not ozone therapy sold by ANCAP.",
    ppStep3Title: "Lavender",
    ppStep3Body: "Aromatherapy atomizer literacy. Not a drug or antiseptic claim.",
    ppStep4Title: "Handoff",
    ppStep4Body: "ACP buys a subscription brief and licensed clinic match — not hardware title.",
""",
    "ru": """    ppCta: "Подписаться на PulmoPure",
    ppKicker: "Подписка · газо-вибрация · лицензированная пульмонология",
    ppTitle: "PulmoPure — грамотность «чистых лёгких», только партнёрская клиника",
    ppPrice: "14 000 ACP / месяц",
    ppPeriods: "38 000 ACP / квартал · 128 000 ACP / год",
    ppLead:
      "Концептуальный портативный аппарат: силиконовый мундштук, генератор газо-вибрации, грамотность смеси медгазов, лавандовый атомайзер, фильтр и режимы Soft / Standard / Intensive. «До/после» альвеол и слоган «чистые лёгкие» — грамотность протокола: AETERNA не продаёт изделие CE/FDA, не компаундит озон или медгазы и не обещает очистку от смол.",
    ppDisclaimer:
      "ANCAP не производит PulmoPure, не практикует пульмонологию и не заявляет статус CE/FDA или безопасную домашнюю озоноингаляцию. Режимы и комплектация на картинке — грамотность партнёра. Сеансы — только у лицензированного клинициста после скрининга.",
    ppLegalCta: "Юр. текст PulmoPure",
    ppAlt:
      "Инфографика аппарата PulmoPure: газо-вибрация, смесь газов, лавандовые масла, режимы Soft / Standard / Intensive и схемы альвеол. Концептуальная архитектура для лицензированных пульмонологических партнёров.",
    ppStep1Title: "Вибрация",
    ppStep1Body: "Грамотность газовых пульсаций. Не гарантия снятия смол.",
    ppStep2Title: "Смесь газов",
    ppStep2Body: "Грамотность партнёрского протокола. Не озонотерапия от ANCAP.",
    ppStep3Title: "Лаванда",
    ppStep3Body: "Грамотность ароматерапии. Не лекарство и не антисептик-claim.",
    ppStep4Title: "Передача",
    ppStep4Body: "ACP покупает подписочный бриф и клинику — не право на железо.",
""",
    "uk": """    ppCta: "Підписатися на PulmoPure",
    ppKicker: "Підписка · газо-вібрація · ліцензована пульмонологія",
    ppTitle: "PulmoPure — грамотність «чистих легень», лише партнерська клініка",
    ppPrice: "14 000 ACP / місяць",
    ppPeriods: "38 000 ACP / квартал · 128 000 ACP / рік",
    ppLead:
      "Концептуальний портативний апарат: мундштук, газо-вібрація, грамотність суміші медгазів, лавандовий атомайзер і режими Soft / Standard / Intensive. AETERNA не продає виріб CE/FDA і не обіцяє очищення від смол.",
    ppDisclaimer:
      "ANCAP не виробляє PulmoPure і не практикує пульмонологію. Сеанси — лише у ліцензованого клініциста після скринінгу.",
    ppLegalCta: "Юр. текст PulmoPure",
    ppAlt:
      "Інфографіка апарата PulmoPure: газо-вібрація, суміш газів, лаванда, режими та схеми альвеол. Концептуальна архітектура для ліцензованих партнерів.",
    ppStep1Title: "Вібрація",
    ppStep1Body: "Грамотність газових пульсацій. Не гарантія зняття смол.",
    ppStep2Title: "Суміш газів",
    ppStep2Body: "Грамотність партнерського протоколу. Не озонотерапія від ANCAP.",
    ppStep3Title: "Лаванда",
    ppStep3Body: "Грамотність ароматерапії. Не ліки.",
    ppStep4Title: "Передача",
    ppStep4Body: "ACP купує підписний бриф і клініку — не право на залізо.",
""",
    "de": """    ppCta: "PulmoPure-Abo öffnen",
    ppKicker: "Abo · Gasvibration · lizenzierte Pneumologie",
    ppTitle: "PulmoPure — „saubere Lungen“-Literalität, nur Partnerklinik",
    ppPrice: "14.000 ACP / Monat",
    ppPeriods: "38.000 ACP / Quartal · 128.000 ACP / Jahr",
    ppLead:
      "Konzeptuelles Handgerät: Mundstück, Gasvibrationsgenerator, Medizingas-Mix-Literacy, Lavendelöl-Zerstäuber und Soft-/Standard-/Intensiv-Modi. AETERNA verkauft kein CE/FDA-Gerät und verspricht keine Teerklärung.",
    ppDisclaimer:
      "ANCAP stellt PulmoPure nicht her und praktiziert keine Pneumologie. Sitzungen nur unter lizenziertem Kliniker nach Screening.",
    ppLegalCta: "Rechtshinweis PulmoPure",
    ppAlt:
      "Infografik des PulmoPure-Handgeräts: Gasvibration, Gasgemisch, Lavendel, Modi und Alveolen-Diagramme. Konzeptuelle Architektur für lizenzierte Pneumologie-Partner.",
    ppStep1Title: "Vibration",
    ppStep1Body: "Gasimpuls-Literalität. Keine garantierte Teerablösung.",
    ppStep2Title: "Gasgemisch",
    ppStep2Body: "Partnerprotokoll-Literalität. Keine Ozontherapie von ANCAP.",
    ppStep3Title: "Lavendel",
    ppStep3Body: "Aromatherapie-Literalität. Kein Arzneimittel-Claim.",
    ppStep4Title: "Übergabe",
    ppStep4Body: "ACP kauft Abo-Brief und Klinik-Match — kein Hardware-Eigentum.",
""",
    "zh-Hant": """    ppCta: "訂閱 PulmoPure",
    ppKicker: "訂閱 · 氣體振動 · 持照肺科",
    ppTitle: "PulmoPure — 「潔淨肺部」素養，僅限夥伴診所",
    ppPrice: "每月 14,000 ACP",
    ppPeriods: "季繳 38,000 ACP · 年繳 128,000 ACP",
    ppLead:
      "概念性手持裝置：矽膠咬嘴、氣體振動、醫用氣體混合素養、薰衣草霧化與 Soft／Standard／Intensive 模式。AETERNA 不販售 CE/FDA 器材，亦不保證清除焦油。",
    ppDisclaimer:
      "ANCAP 不製造 PulmoPure，亦不執業肺科。實體療程僅在持照臨床醫師篩檢後進行。",
    ppLegalCta: "PulmoPure 法律聲明",
    ppAlt:
      "PulmoPure 手持肺部照護系統資訊圖：氣體振動、氣體混合、薰衣草、模式與肺泡圖。持照肺科夥伴的概念架構。",
    ppStep1Title: "振動",
    ppStep1Body: "氣體脈動素養。非保證清除焦油。",
    ppStep2Title: "氣體混合",
    ppStep2Body: "夥伴協議素養。非 ANCAP 臭氧治療。",
    ppStep3Title: "薰衣草",
    ppStep3Body: "芳療素養。非藥品宣稱。",
    ppStep4Title: "移交",
    ppStep4Body: "ACP 購買訂閱簡報與診所媒合 — 非硬體所有權。",
""",
}

LEGAL = {
    "en": """    pulmopureLink: "PulmoPure",
    hubCardPulmopure:
      "Licensed pulmonology subscription for PulmoPure gas-vibration literacy. Not a CE/FDA device, not ozone therapy, not a guaranteed clean-lungs outcome.",
    pulmopureKicker: "Legal / pulmonology / lung-care literacy",
    pulmopureTitle: "PulmoPure — licensed pulmonology subscription rail",
    pulmopureIntro:
      "How ANCAP frames the PulmoPure subscription SKU as of 13 September 2026. These pages sell ACP-settled clinic retainers, not devices, not ozone therapy, and not a guaranteed respiratory cure.",
    pp1Title: "1. Platform role",
    pp1Body:
      "ANCAP provides ACP settlement, consult briefs, and licensed-partner matching. ANCAP does not manufacture PulmoPure, does not compound medical gases or ozone, and does not practice pulmonology.",
    pp2Title: "2. Not a medical device sold here",
    pp2Body:
      "The infographic is conceptual architecture. It is not an EU MDR or FDA brochure and not a CE-marked respiratory device sold by ANCAP.",
    pp3Title: "3. Forbidden outcome claims",
    pp3Body:
      "ANCAP does not guarantee tar clearance, clean alveoli, cough reduction, ease of breathing, or smoking-cessation success. Before/after artwork is literacy only.",
    pp4Title: "4. Ozone and medical gases",
    pp4Body:
      "Any gas mix, including oxygen or ozone callouts on marketing art, is partner-protocol literacy. ANCAP does not sell ozone therapy or authorize home gas inhalation kits.",
    pp5Title: "5. Licensed clinicians only",
    pp5Body:
      "Physical sessions occur only under a licensed pulmonology / respiratory / smoking-cessation clinician after screening (asthma, COPD, pneumothorax history, pregnancy, ozone sensitivity).",
    pp6Title: "6. Modes and package contents",
    pp6Body:
      "Soft / Standard / Intensive modes, cartridges, USB-C cable, and case icons are package literacy — not a product catalog ANCAP ships.",
    pp7Title: "7. Not medical advice",
    pp7Body:
      "Catalog copy is informational. It is not a diagnosis, prescription, or treatment plan.",
    pp8Title: "8. Relationship to other rails",
    pp8Body:
      "M-receptor inhaler literacy and oxygen-carrier rails remain separate. This SKU does not authorize compounding or unlicensed device sale.",
    pp9Title: "9. Payments",
    pp9Body:
      "ACP buys a subscription brief and partner match at 14,000 ACP / month (38,000 quarterly; 128,000 annual) — not hardware title and not a refundable clinical outcome. Refunds follow /legal/refunds.",
    pp10Title: "10. Contact",
    pp10Body:
      "Legal notices: legal@ancap.cloud. Product: /aeterna#pulmopure. Related notices: /legal/m-receptor, /legal/terms, /legal/risk.",
    footerPulmopure: "PulmoPure",
""",
    "ru": """    pulmopureLink: "PulmoPure",
    hubCardPulmopure:
      "Подписка лицензированной пульмонологии на грамотность PulmoPure. Не изделие CE/FDA, не озонотерапия, не гарантия «чистых лёгких».",
    pulmopureKicker: "Право / пульмонология / грамотность ухода за лёгкими",
    pulmopureTitle: "PulmoPure — подписочный рейл лицензированной пульмонологии",
    pulmopureIntro:
      "Как ANCAP формулирует подписку PulmoPure на 13 сентября 2026. Эти страницы продают ретейнер клиники в ACP, а не аппарат, не озонотерапию и не гарантированное лечение.",
    pp1Title: "1. Роль платформы",
    pp1Body:
      "ANCAP обеспечивает расчёт в ACP, брифы и подбор партнёра. ANCAP не производит PulmoPure, не компаундит медгазы или озон и не практикует пульмонологию.",
    pp2Title: "2. Не медицинское изделие на продажу здесь",
    pp2Body:
      "Инфографика — концептуальная архитектура. Это не брошюра EU MDR / FDA и не CE-изделие от ANCAP.",
    pp3Title: "3. Запрещённые обещания результата",
    pp3Body:
      "ANCAP не гарантирует очистку от смол, чистые альвеолы, уменьшение кашля или успех отказа от курения. «До/после» — только грамотность.",
    pp4Title: "4. Озон и медгазы",
    pp4Body:
      "Любая смесь газов на маркетинговой картинке — грамотность партнёрского протокола. ANCAP не продаёт озонотерапию и не разрешает домашние наборы ингаляции газов.",
    pp5Title: "5. Только лицензированные клиницисты",
    pp5Body:
      "Физические сеансы — только у лицензированного пульмонолога / респираторного клинициста после скрининга.",
    pp6Title: "6. Режимы и комплектация",
    pp6Body:
      "Режимы Soft / Standard / Intensive, картриджи и кейс — грамотность комплектации, не каталог поставки ANCAP.",
    pp7Title: "7. Не медицинский совет",
    pp7Body:
      "Тексты каталога информационные. Это не диагноз, не рецепт и не план лечения.",
    pp8Title: "8. Связь с другими рейлами",
    pp8Body:
      "Ингалятор M-рецепторов и переносчик кислорода остаются отдельными. Этот SKU не разрешает компаундинг.",
    pp9Title: "9. Платежи",
    pp9Body:
      "ACP покупает подписочный бриф и подбор партнёра за 14 000 ACP / месяц (38 000 квартал; 128 000 год). Возвраты: /legal/refunds.",
    pp10Title: "10. Контакты",
    pp10Body:
      "Юридические уведомления: legal@ancap.cloud. Продукт: /aeterna#pulmopure.",
    footerPulmopure: "PulmoPure",
""",
    "uk": """    pulmopureLink: "PulmoPure",
    hubCardPulmopure:
      "Підписка ліцензованої пульмонології на грамотність PulmoPure. Не виріб CE/FDA, не озонотерапія, не гарантія «чистих легень».",
    pulmopureKicker: "Право / пульмонологія",
    pulmopureTitle: "PulmoPure — підписний рейл ліцензованої пульмонології",
    pulmopureIntro:
      "Як ANCAP формулює підписку PulmoPure станом на 13 вересня 2026.",
    pp1Title: "1. Роль платформи",
    pp1Body:
      "ANCAP забезпечує розрахунок в ACP і підбір партнера. ANCAP не виробляє PulmoPure і не практикує пульмонологію.",
    pp2Title: "2. Не медичний виріб на продаж тут",
    pp2Body:
      "Інфографіка — концептуальна архітектура. Не брошура CE/FDA від ANCAP.",
    pp3Title: "3. Заборонені обіцянки результату",
    pp3Body:
      "ANCAP не гарантує очищення від смол чи зменшення кашлю.",
    pp4Title: "4. Озон і медгази",
    pp4Body:
      "Суміш газів на зображенні — грамотність протоколу. ANCAP не продає озонотерапію.",
    pp5Title: "5. Лише ліцензовані клініцисти",
    pp5Body:
      "Сеанси — лише у ліцензованого клініциста після скринінгу.",
    pp6Title: "6. Режими та комплектація",
    pp6Body:
      "Режими Soft / Standard / Intensive — грамотність комплектації.",
    pp7Title: "7. Не медична порада",
    pp7Body:
      "Тексти каталогу інформаційні.",
    pp8Title: "8. Зв'язок з іншими рейлами",
    pp8Body:
      "M-рецептори та переносник кисню лишаються окремими.",
    pp9Title: "9. Платежі",
    pp9Body:
      "ACP купує підписний бриф за 14 000 ACP / місяць. Повернення: /legal/refunds.",
    pp10Title: "10. Контакти",
    pp10Body:
      "Юридичні повідомлення: legal@ancap.cloud. Продукт: /aeterna#pulmopure.",
    footerPulmopure: "PulmoPure",
""",
    "de": """    pulmopureLink: "PulmoPure",
    hubCardPulmopure:
      "Lizenziertes Pneumologie-Abo für PulmoPure-Gasvibrations-Literalität. Kein CE/FDA-Gerät, keine Ozontherapie, keine garantierten sauberen Lungen.",
    pulmopureKicker: "Recht / Pneumologie",
    pulmopureTitle: "PulmoPure — lizenzierte Pneumologie-Abo-Schiene",
    pulmopureIntro:
      "Wie ANCAP die PulmoPure-Abo-SKU zum 13. September 2026 rahmt.",
    pp1Title: "1. Plattformrolle",
    pp1Body:
      "ANCAP bietet ACP-Abrechnung und Partner-Matching. ANCAP stellt PulmoPure nicht her und praktiziert keine Pneumologie.",
    pp2Title: "2. Kein hier verkauftes Medizinprodukt",
    pp2Body:
      "Die Infografik ist konzeptuelle Architektur. Keine CE/FDA-Broschüre von ANCAP.",
    pp3Title: "3. Verbotene Ergebnisversprechen",
    pp3Body:
      "ANCAP garantiert keine Teerklärung oder Hustenreduktion.",
    pp4Title: "4. Ozon und Medizingase",
    pp4Body:
      "Gasgemische auf der Grafik sind Partnerprotokoll-Literalität. ANCAP verkauft keine Ozontherapie.",
    pp5Title: "5. Nur lizenzierte Kliniker",
    pp5Body:
      "Sitzungen nur unter lizenziertem Kliniker nach Screening.",
    pp6Title: "6. Modi und Lieferumfang",
    pp6Body:
      "Soft / Standard / Intensiv sind Paket-Literalität.",
    pp7Title: "7. Keine medizinische Beratung",
    pp7Body:
      "Katalogtexte sind informativ.",
    pp8Title: "8. Verhältnis zu anderen Schienen",
    pp8Body:
      "M-Rezeptor und Sauerstoffträger bleiben getrennt.",
    pp9Title: "9. Zahlungen",
    pp9Body:
      "ACP kauft Abo-Brief für 14.000 ACP / Monat. Rückerstattungen: /legal/refunds.",
    pp10Title: "10. Kontakt",
    pp10Body:
      "Rechtliches: legal@ancap.cloud. Produkt: /aeterna#pulmopure.",
    footerPulmopure: "PulmoPure",
""",
    "zh-Hant": """    pulmopureLink: "PulmoPure",
    hubCardPulmopure:
      "持照肺科訂閱 PulmoPure 氣體振動素養。非 CE/FDA 器材、非臭氧治療、非保證潔淨肺部。",
    pulmopureKicker: "法律／肺科",
    pulmopureTitle: "PulmoPure — 持照肺科訂閱軌道",
    pulmopureIntro:
      "ANCAP 於 2026 年 9 月 13 日對 PulmoPure 訂閱 SKU 的表述。",
    pp1Title: "1. 平台角色",
    pp1Body:
      "ANCAP 提供 ACP 結算與夥伴媒合。ANCAP 不製造 PulmoPure，亦不執業肺科。",
    pp2Title: "2. 非於此販售之醫療器材",
    pp2Body:
      "資訊圖為概念架構。非 ANCAP 之 CE/FDA 型錄。",
    pp3Title: "3. 禁止結果宣稱",
    pp3Body:
      "ANCAP 不保證清除焦油或減少咳嗽。",
    pp4Title: "4. 臭氧與醫用氣體",
    pp4Body:
      "圖上氣體混合為夥伴協議素養。ANCAP 不販售臭氧治療。",
    pp5Title: "5. 僅持照臨床醫師",
    pp5Body:
      "實體療程僅在篩檢後由持照臨床醫師進行。",
    pp6Title: "6. 模式與配件",
    pp6Body:
      "Soft／Standard／Intensive 為配件素養。",
    pp7Title: "7. 非醫療建議",
    pp7Body:
      "目錄文案僅供資訊。",
    pp8Title: "8. 與其他軌道之關係",
    pp8Body:
      "M 受體與氧載體仍為獨立。",
    pp9Title: "9. 付款",
    pp9Body:
      "ACP 以每月 14,000 ACP 購買訂閱簡報。退款依 /legal/refunds。",
    pp10Title: "10. 聯絡",
    pp10Body:
      "法律通知：legal@ancap.cloud。產品：/aeterna#pulmopure。",
    footerPulmopure: "PulmoPure",
""",
}

HERO = {
    "en": [
        (
            "or an ADHD / СДВГ support brief at 42,000 ACP.",
            "or an ADHD / СДВГ support brief at 42,000 ACP, or a PulmoPure lung-care subscription from 14,000 ACP / month.",
        ),
        (
            "ADHD / СДВГ support brief is 42,000 ACP. AETERNA",
            "ADHD / СДВГ support brief is 42,000 ACP; PulmoPure lung-care subscription is 14,000 ACP / month (38,000 quarterly; 128,000 annual). AETERNA",
        ),
    ],
    "ru": [
        (
            "или бриф поддержки при СДВГ за 42 000 ACP.",
            "или бриф поддержки при СДВГ за 42 000 ACP, или подписку PulmoPure от 14 000 ACP / месяц.",
        ),
        (
            "бриф поддержки при СДВГ — 42 000 ACP. AETERNA",
            "бриф поддержки при СДВГ — 42 000 ACP; подписка PulmoPure — 14 000 ACP / месяц (38 000 квартал; 128 000 год). AETERNA",
        ),
    ],
    "uk": [
        (
            "або бриф підтримки при СДУГ за 42 000 ACP.",
            "або бриф підтримки при СДУГ за 42 000 ACP, або підписку PulmoPure від 14 000 ACP / місяць.",
        ),
        (
            "бриф підтримки при СДУГ — 42 000 ACP. AETERNA",
            "бриф підтримки при СДУГ — 42 000 ACP; підписка PulmoPure — 14 000 ACP / місяць. AETERNA",
        ),
    ],
    "de": [
        (
            "oder ein ADHS-Unterstützungsbrief für 42.000 ACP.",
            "oder ein ADHS-Unterstützungsbrief für 42.000 ACP, oder ein PulmoPure-Lungenpflege-Abo ab 14.000 ACP / Monat.",
        ),
        (
            "ADHS-Unterstützungsbrief 42.000 ACP. AETERNA",
            "ADHS-Unterstützungsbrief 42.000 ACP; PulmoPure-Abo 14.000 ACP / Monat. AETERNA",
        ),
    ],
    "zh-Hant": [
        (
            "或以 42,000 ACP 開啟 ADHD 支援簡報。",
            "或以 42,000 ACP 開啟 ADHD 支援簡報，或以每月 14,000 ACP 起訂 PulmoPure 肺部照護訂閱。",
        ),
        (
            "ADHD 支援簡報 42,000 ACP。AETERNA",
            "ADHD 支援簡報 42,000 ACP；PulmoPure 訂閱每月 14,000 ACP。AETERNA",
        ),
    ],
}


def patch_aeterna() -> None:
    path = ROOT / "aeterna.ts"
    text = path.read_text(encoding="utf-8")
    if "intent21Title" in text:
        print("aeterna.ts already patched")
        return
    for lang in LANGS:
        start, end = bounds(text, lang)
        section = text[start:end]
        section = insert_after_marker(section, "intent20Body:", '",\n\n', INTENTS[lang] + "\n")
        section = insert_after_marker(section, "adhdStep6Body:", ",\n\n", PANELS[lang] + "\n")
        for old, new in HERO.get(lang, []):
            if old in section:
                section = section.replace(old, new, 1)
        text = text[:start] + section + text[end:]
    path.write_text(text, encoding="utf-8")
    print("patched aeterna.ts")


def patch_legal() -> None:
    path = ROOT / "legal.ts"
    text = path.read_text(encoding="utf-8")
    if "pulmopureLink" in text:
        print("legal.ts already patched")
        return
    for lang in LANGS:
        start, end = bounds(text, lang)
        section = text[start:end]
        marker = "footerAdhdSupport:"
        idx = section.find(marker)
        if idx < 0:
            raise SystemExit(f"no footerAdhdSupport in {lang}")
        after = section[idx:]
        close = after.find(",\n")
        if close < 0:
            raise SystemExit(f"cannot close footer in {lang}")
        at = idx + close + len(",\n")
        section = section[:at] + "\n" + LEGAL[lang] + section[at:]
        text = text[:start] + section + text[end:]
    path.write_text(text, encoding="utf-8")
    print("patched legal.ts")


if __name__ == "__main__":
    patch_aeterna()
    patch_legal()
