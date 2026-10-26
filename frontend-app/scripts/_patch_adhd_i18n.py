# -*- coding: utf-8 -*-
"""Insert ADHD support i18n into aeterna.ts + legal.ts."""
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


def insert_after_intent19(section: str, block: str) -> str:
    marker = "intent19Body:"
    idx = section.find(marker)
    if idx < 0:
        raise SystemExit("no intent19Body")
    after = section[idx:]
    close = after.find('",\n\n')
    if close < 0:
        raise SystemExit("cannot close intent19Body")
    at = idx + close + len('",\n\n')
    return section[:at] + block + "\n" + section[at:]


def insert_after_sbm6(section: str, block: str) -> str:
    marker = "sbmStep6Body:"
    idx = section.find(marker)
    if idx < 0:
        raise SystemExit("no sbmStep6Body")
    after = section[idx:]
    close = after.find(",\n\n")
    if close < 0:
        raise SystemExit("cannot close sbmStep6")
    at = idx + close + len(",\n\n")
    return section[:at] + block + "\n" + section[at:]


def replace_once(section: str, old: str, new: str) -> str:
    if old not in section:
        return section
    return section.replace(old, new, 1)


INTENTS = {
    "en": (
        '    intent20Title: "ADHD / СДВГ support brief",\n'
        "    intent20Body:\n"
        '      "Licensed clinician / child psychiatry–neurology partner brief for ADHD support literacy. '
        "42,000 ACP. Not a diagnosis, not a prescription, not stimulant compounding, not a CE/FDA drug, "
        'and not a guaranteed academic or financial outcome.",\n'
    ),
    "ru": (
        '    intent20Title: "Поддержка при СДВГ",\n'
        "    intent20Body:\n"
        '      "Бриф для лицензированного клинициста (детская психиатрия / неврология) по поддержке при СДВГ. '
        "42 000 ACP. Не диагноз, не рецепт, не компаундинг стимуляторов, не лекарство CE/FDA и не гарантированный "
        'учебный или финансовый результат.",\n'
    ),
    "uk": (
        '    intent20Title: "Підтримка при СДУГ",\n'
        "    intent20Body:\n"
        '      "Бриф для ліцензованого клініциста (дитяча психіатрія / неврологія) щодо підтримки при СДУГ. '
        "42 000 ACP. Не діагноз, не рецепт, не компаундинг стимуляторів, не ліки CE/FDA і не гарантований "
        'навчальний чи фінансовий результат.",\n'
    ),
    "de": (
        '    intent20Title: "ADHS-Unterstützung",\n'
        "    intent20Body:\n"
        '      "Partnerbrief für lizenzierte Kliniker (Kinderpsychiatrie / Neurologie) zur ADHS-Unterstützungsliteralität. '
        "42.000 ACP. Keine Diagnose, kein Rezept, kein Stimulanzien-Compounding, kein CE/FDA-Arzneimittel und "
        'kein garantiertes Schul- oder Finanzergebnis.",\n'
    ),
    "zh-Hant": (
        '    intent20Title: "ADHD／注意力不足過動支援",\n'
        "    intent20Body:\n"
        '      "持照臨床醫師（兒童精神／神經）夥伴簡報，ADHD 支援素養。42,000 ACP。'
        '非診斷、非處方、非興奮劑配製、非 CE/FDA 藥品，亦非保證學業或財務結果。",\n'
    ),
}

PANELS = {
    "en": """    adhdCta: "Open ADHD support brief",
    adhdKicker: "ADHD / СДВГ · licensed clinician · support literacy",
    adhdTitle: "ADHD support — focus today, bigger future",
    adhdPrice: "42,000 ACP",
    adhdLead:
      "ADHD is a different way of seeing the world, not a sentence. This SKU buys a licensed-clinician partner brief: focus, planning, emotional control, relationships, self-esteem, and risk literacy. The 'path to a billion' stairs on the artwork are motivational literacy — not a promise of wealth.",
    adhdDisclaimer:
      "ANCAP does not diagnose, prescribe, compound stimulants, or guarantee school, career, or financial outcomes. Physical care occurs only under a licensed clinician after screening. Infographic billionaire framing is motivational literacy, not a product claim.",
    adhdLegalCta: "ADHD support legal notice",
    adhdAlt:
      "Infographic about ADHD support for children: focus, planning, emotional control, relationships, self-esteem, risk reduction, and a motivational staircase. Conceptual literacy for licensed clinician partners — not a diagnosis or treatment claim.",
    adhdStep1Title: "Focus",
    adhdStep1Body: "Hold attention longer and finish tasks — literacy for a licensed clinician brief.",
    adhdStep2Title: "Planning",
    adhdStep2Body: "Reduce impulsivity; set goals and follow plans with partner support.",
    adhdStep3Title: "Emotions",
    adhdStep3Body: "Fewer mood swings; lower anxiety and irritability as partner themes.",
    adhdStep4Title: "Relationships",
    adhdStep4Body: "Communicate, make friends, and work in a team — social adaptation literacy.",
    adhdStep5Title: "Self-esteem",
    adhdStep5Body: "Feel more confident realizing abilities — not a guaranteed school grade.",
    adhdStep6Title: "Risk literacy",
    adhdStep6Body: "Lower future risk themes (depression, anxiety, addiction, behavior). Not a cure claim.",
""",
    "ru": """    adhdCta: "Открыть бриф по СДВГ",
    adhdKicker: "СДВГ · лицензированный клиницист · грамотность поддержки",
    adhdTitle: "Поддержка при СДВГ — фокус сегодня, большое будущее",
    adhdPrice: "42 000 ACP",
    adhdLead:
      "СДВГ — другой взгляд на мир, а не приговор. Этот SKU покупает партнёрский бриф лицензированного клинициста: фокус, планирование, эмоции, отношения, самооценка и снижение рисков. Лестница «к миллиарду» на инфографике — мотивационная грамотность, не обещание богатства.",
    adhdDisclaimer:
      "ANCAP не ставит диагноз, не выписывает рецепты, не компаундит стимуляторы и не гарантирует школу, карьеру или деньги. Физическая помощь — только у лицензированного клинициста после скрининга. «Миллиардер» на картинке — мотивация, не claim продукта.",
    adhdLegalCta: "Юр. текст: поддержка при СДВГ",
    adhdAlt:
      "Инфографика о поддержке детей с СДВГ: фокус, планирование, эмоции, отношения, самооценка, снижение рисков и мотивационная лестница. Концептуальная грамотность для лицензированных клиницистов — не диагноз и не лечение от ANCAP.",
    adhdStep1Title: "Фокус",
    adhdStep1Body: "Дольше удерживать внимание и доводить дела — грамотность брифа.",
    adhdStep2Title: "Планирование",
    adhdStep2Body: "Меньше импульсивности; цели и планы с поддержкой партнёра.",
    adhdStep3Title: "Эмоции",
    adhdStep3Body: "Меньше качелей настроения; тревога и раздражительность как темы партнёра.",
    adhdStep4Title: "Отношения",
    adhdStep4Body: "Общение, дружба, команда — грамотность социальной адаптации.",
    adhdStep5Title: "Самооценка",
    adhdStep5Body: "Увереннее реализовывать способности — не гарантия оценок.",
    adhdStep6Title: "Риски",
    adhdStep6Body: "Темы снижения будущих рисков. Не claim «вылечили».",
""",
    "uk": """    adhdCta: "Відкрити бриф щодо СДУГ",
    adhdKicker: "СДУГ · ліцензований клініцист · грамотність підтримки",
    adhdTitle: "Підтримка при СДУГ — фокус сьогодні, велике майбутнє",
    adhdPrice: "42 000 ACP",
    adhdLead:
      "СДУГ — інший погляд на світ, а не вирок. Цей SKU купує партнерський бриф ліцензованого клініциста. Сходи «до мільярда» на інфографіці — мотиваційна грамотність, не обіцянка багатства.",
    adhdDisclaimer:
      "ANCAP не ставить діагноз, не виписує рецепти, не компаундить стимулятори і не гарантує школу, кар'єру чи гроші. Фізична допомога — лише у ліцензованого клініциста.",
    adhdLegalCta: "Юр. текст: підтримка при СДУГ",
    adhdAlt:
      "Інфографіка про підтримку дітей із СДУГ: фокус, планування, емоції, стосунки, самооцінка та мотиваційні сходи. Концептуальна грамотність для ліцензованих клініцистів.",
    adhdStep1Title: "Фокус",
    adhdStep1Body: "Довше утримувати увагу й доводити справи — грамотність брифу.",
    adhdStep2Title: "Планування",
    adhdStep2Body: "Менше імпульсивності; цілі й плани з підтримкою партнера.",
    adhdStep3Title: "Емоції",
    adhdStep3Body: "Менше хитавиці настрою; тривога й дратівливість як теми партнера.",
    adhdStep4Title: "Стосунки",
    adhdStep4Body: "Спілкування, дружба, команда — грамотність соціальної адаптації.",
    adhdStep5Title: "Самооцінка",
    adhdStep5Body: "Впевненіше реалізовувати здібності — не гарантія оцінок.",
    adhdStep6Title: "Ризики",
    adhdStep6Body: "Теми зниження майбутніх ризиків. Не claim «вилікували».",
""",
    "de": """    adhdCta: "ADHS-Brief öffnen",
    adhdKicker: "ADHS · lizenzierter Kliniker · Unterstützungsliteralität",
    adhdTitle: "ADHS-Unterstützung — Fokus heute, große Zukunft",
    adhdPrice: "42.000 ACP",
    adhdLead:
      "ADHS ist eine andere Weltwahrnehmung, kein Urteil. Dieses SKU kauft einen Partnerbrief eines lizenzierten Klinikers. Die „Milliardärs“-Treppe auf der Infografik ist Motivationsliteralität — kein Vermögensversprechen.",
    adhdDisclaimer:
      "ANCAP diagnostiziert nicht, verschreibt nicht, compoundiert keine Stimulanzien und garantiert keine Schul-, Karriere- oder Finanzergebnisse. Körperliche Versorgung nur unter lizenziertem Kliniker.",
    adhdLegalCta: "Rechtshinweis ADHS-Unterstützung",
    adhdAlt:
      "Infografik zur ADHS-Unterstützung bei Kindern: Fokus, Planung, Emotionen, Beziehungen, Selbstwert und Motivationsleiter. Konzeptuelle Literalität für lizenzierte Kliniker.",
    adhdStep1Title: "Fokus",
    adhdStep1Body: "Aufmerksamkeit halten und Aufgaben beenden — Brief-Literalität.",
    adhdStep2Title: "Planung",
    adhdStep2Body: "Weniger Impulsivität; Ziele und Pläne mit Partnerunterstützung.",
    adhdStep3Title: "Emotionen",
    adhdStep3Body: "Weniger Stimmungsschwankungen; Angst und Reizbarkeit als Partner-Themen.",
    adhdStep4Title: "Beziehungen",
    adhdStep4Body: "Kommunikation, Freunde, Teamarbeit — soziale Anpassungsliteralität.",
    adhdStep5Title: "Selbstwert",
    adhdStep5Body: "Fähigkeiten sicherer nutzen — keine Notengarantie.",
    adhdStep6Title: "Risiken",
    adhdStep6Body: "Themen zur Senkung künftiger Risiken. Kein Heilungs-Claim.",
""",
    "zh-Hant": """    adhdCta: "開啟 ADHD 支援簡報",
    adhdKicker: "ADHD · 持照臨床醫師 · 支援素養",
    adhdTitle: "ADHD 支援 — 今日專注，更大未來",
    adhdPrice: "42,000 ACP",
    adhdLead:
      "ADHD 是不同的看世界方式，不是判決。此 SKU 購買持照臨床醫師夥伴簡報。圖上「億萬富翁」階梯是動機素養，不是致富保證。",
    adhdDisclaimer:
      "ANCAP 不診斷、不開方、不配製興奮劑，亦不保證學業、職涯或財務結果。實體照護僅在持照臨床醫師篩檢後進行。",
    adhdLegalCta: "ADHD 支援法律聲明",
    adhdAlt:
      "關於兒童 ADHD 支援的資訊圖：專注、規劃、情緒、關係、自尊與動機階梯。持照臨床醫師夥伴的概念素養。",
    adhdStep1Title: "專注",
    adhdStep1Body: "更久維持注意力並完成任務 — 簡報素養。",
    adhdStep2Title: "規劃",
    adhdStep2Body: "減少衝動；與夥伴支援設定目標並執行。",
    adhdStep3Title: "情緒",
    adhdStep3Body: "較少情緒波動；焦慮與易怒作為夥伴主題。",
    adhdStep4Title: "關係",
    adhdStep4Body: "溝通、交友、團隊 — 社會適應素養。",
    adhdStep5Title: "自尊",
    adhdStep5Body: "更有信心發揮能力 — 非成績保證。",
    adhdStep6Title: "風險",
    adhdStep6Body: "降低未來風險的主題。非治癒宣稱。",
""",
}

HERO_PAY = {
    "en": [
        (
            "or a synthetic-blood / Black Mamba architecture brief at 98,000 ACP.",
            "or a synthetic-blood / Black Mamba architecture brief at 98,000 ACP, or an ADHD / СДВГ support brief at 42,000 ACP.",
        ),
        (
            "synthetic-blood / Black Mamba architecture brief is 98,000 ACP. AETERNA",
            "synthetic-blood / Black Mamba architecture brief is 98,000 ACP; ADHD / СДВГ support brief is 42,000 ACP. AETERNA",
        ),
        (
            "synthetic-blood / Black Mamba architecture, ACP workflows",
            "synthetic-blood / Black Mamba architecture, ADHD / СДВГ support, ACP workflows",
        ),
        (
            "synthetic-blood / Black Mamba architecture brief at 98,000 ACP.",
            "synthetic-blood / Black Mamba architecture brief at 98,000 ACP, ADHD / СДВГ support brief at 42,000 ACP.",
        ),
    ],
    "ru": [
        (
            "или бриф синтетической крови / Чёрной Мамбы за 98 000 ACP.",
            "или бриф синтетической крови / Чёрной Мамбы за 98 000 ACP, или бриф поддержки при СДВГ за 42 000 ACP.",
        ),
        (
            "синтетическая кровь / Чёрная Мамба — 98 000 ACP. AETERNA",
            "синтетическая кровь / Чёрная Мамба — 98 000 ACP; бриф поддержки при СДВГ — 42 000 ACP. AETERNA",
        ),
        (
            "синтетическая кровь / Чёрная Мамба 98 000 ACP.",
            "синтетическая кровь / Чёрная Мамба 98 000 ACP, поддержка при СДВГ 42 000 ACP.",
        ),
    ],
    "uk": [
        (
            "або бриф синтетичної крові / Чорної Мамби за 98 000 ACP.",
            "або бриф синтетичної крові / Чорної Мамби за 98 000 ACP, або бриф підтримки при СДУГ за 42 000 ACP.",
        ),
        (
            "синтетична кров / Чорна Мамба — 98 000 ACP. AETERNA",
            "синтетична кров / Чорна Мамба — 98 000 ACP; бриф підтримки при СДУГ — 42 000 ACP. AETERNA",
        ),
        (
            "синтетична кров / Чорна Мамба 98 000 ACP.",
            "синтетична кров / Чорна Мамба 98 000 ACP, підтримка при СДУГ 42 000 ACP.",
        ),
    ],
    "de": [
        (
            "Synthetisches Blut / Black Mamba 98.000 ACP.",
            "Synthetisches Blut / Black Mamba 98.000 ACP, ADHS-Unterstützung 42.000 ACP.",
        ),
    ],
    "zh-Hant": [
        (
            "或以 98,000 ACP 開啟合成血／黑曼巴架構簡報。",
            "或以 98,000 ACP 開啟合成血／黑曼巴架構簡報，或以 42,000 ACP 開啟 ADHD 支援簡報。",
        ),
        (
            "合成血／黑曼巴架構簡報 98,000 ACP。AETERNA",
            "合成血／黑曼巴架構簡報 98,000 ACP；ADHD 支援簡報 42,000 ACP。AETERNA",
        ),
        (
            "合成血／黑曼巴架構簡報 98,000 ACP。",
            "合成血／黑曼巴架構簡報 98,000 ACP、ADHD 支援簡報 42,000 ACP。",
        ),
    ],
}


LEGAL = {
    "en": """    adhdSupportLink: "ADHD / СДВГ support",
    hubCardAdhdSupport:
      "Licensed clinician brief for ADHD support literacy. Not a diagnosis, not a prescription, not stimulant compounding, not a guaranteed academic or financial outcome.",
    adhdSupportKicker: "Legal / clinician / ADHD support literacy",
    adhdSupportTitle: "ADHD / СДВГ support — licensed clinician partner rail",
    adhdSupportIntro:
      "How ANCAP frames the ADHD support SKU as of 13 September 2026. These pages sell ACP-settled consult briefs, not diagnoses, prescriptions, stimulants, or a guaranteed path to wealth.",
    adhd1Title: "1. Platform role",
    adhd1Body:
      "ANCAP provides ACP settlement, consult briefs, and licensed-partner matching. ANCAP does not diagnose ADHD, prescribe medication, compound stimulants, or practice child psychiatry or neurology.",
    adhd2Title: "2. Not a diagnosis or treatment",
    adhd2Body:
      "The infographic is motivational and educational literacy. It is not a clinical guideline, not a CE/FDA drug brochure, and not treatment sold by ANCAP.",
    adhd3Title: "3. Forbidden outcome claims",
    adhd3Body:
      "ANCAP does not guarantee calm behavior, school grades, career success, entrepreneurship, or becoming a billionaire. The 'path to a billion' stairs are motivational literacy only.",
    adhd4Title: "4. Licensed clinicians only",
    adhd4Body:
      "Any assessment, therapy, or medication decision is a licensed clinician act after screening. Users must not treat these pages as a substitute for professional care.",
    adhd5Title: "5. Infographic literacy, not a protocol",
    adhd5Body:
      "Focus, planning, emotional control, relationships, self-esteem, and risk-reduction icons are support literacy. ANCAP does not publish stimulant dosing or therapy SOPs.",
    adhd6Title: "6. Not medical advice",
    adhd6Body:
      "Catalog copy is informational. It is not a diagnosis, prescription, or treatment plan.",
    adhd7Title: "7. Health and child data",
    adhd7Body:
      "Treat identifiers and clinical history as sensitive. Do not upload records without a lawful basis and caregiver consent where required.",
    adhd8Title: "8. Relationship to other rails",
    adhd8Body:
      "Longevity and bioreactor rails remain separate. This SKU does not authorize compounding or unlicensed practice of medicine.",
    adhd9Title: "9. Payments",
    adhd9Body:
      "ACP buys a consult brief and partner match at 42,000 ACP — not a diagnosis, not a stimulant course, and not a refundable academic or financial outcome. Refunds follow /legal/refunds.",
    adhd10Title: "10. Contact",
    adhd10Body:
      "Legal notices: legal@ancap.cloud. Product: /aeterna#adhd-support. Related notices: /legal/terms, /legal/risk.",
    footerAdhdSupport: "ADHD / СДВГ support",
""",
    "ru": """    adhdSupportLink: "Поддержка при СДВГ",
    hubCardAdhdSupport:
      "Бриф лицензированного клинициста по поддержке при СДВГ. Не диагноз, не рецепт, не компаундинг стимуляторов, не гарантированный учебный или финансовый результат.",
    adhdSupportKicker: "Право / клиницист / грамотность поддержки при СДВГ",
    adhdSupportTitle: "Поддержка при СДВГ — рейл лицензированного клинициста",
    adhdSupportIntro:
      "Как ANCAP формулирует SKU поддержки при СДВГ на 13 сентября 2026. Эти страницы продают брифы в ACP, а не диагнозы, рецепты, стимуляторы и не путь к богатству.",
    adhd1Title: "1. Роль платформы",
    adhd1Body:
      "ANCAP обеспечивает расчёт в ACP, брифы и подбор лицензированного партнёра. ANCAP не ставит диагноз СДВГ, не выписывает лекарства, не компаундит стимуляторы и не практикует детскую психиатрию или неврологию.",
    adhd2Title: "2. Не диагноз и не лечение",
    adhd2Body:
      "Инфографика — мотивационная и образовательная грамотность. Это не клиническое руководство, не брошюра CE/FDA и не лечение от ANCAP.",
    adhd3Title: "3. Запрещённые обещания результата",
    adhd3Body:
      "ANCAP не гарантирует спокойствие, оценки, карьеру, предпринимательство или статус миллиардера. Лестница «к миллиарду» — только мотивационная грамотность.",
    adhd4Title: "4. Только лицензированные клиницисты",
    adhd4Body:
      "Любая оценка, терапия или решение о лекарствах — акт лицензированного клинициста после скрининга. Эти страницы не заменяют профессиональную помощь.",
    adhd5Title: "5. Грамотность инфографики, не протокол",
    adhd5Body:
      "Фокус, планирование, эмоции, отношения, самооценка и снижение рисков — грамотность поддержки. ANCAP не публикует дозировки стимуляторов и SOP терапии.",
    adhd6Title: "6. Не медицинский совет",
    adhd6Body:
      "Тексты каталога информационные. Это не диагноз, не рецепт и не план лечения.",
    adhd7Title: "7. Данные о здоровье и детях",
    adhd7Body:
      "Идентификаторы и клиническая история — чувствительные данные. Не загружайте записи без законного основания и согласия опекуна, где оно требуется.",
    adhd8Title: "8. Связь с другими рейлами",
    adhd8Body:
      "Рейлы долголетия и биореактора остаются отдельными. Этот SKU не разрешает компаундинг и нелицензированную врачебную практику.",
    adhd9Title: "9. Платежи",
    adhd9Body:
      "ACP покупает бриф и подбор партнёра за 42 000 ACP — не диагноз, не курс стимуляторов и не возвращаемый учебный или финансовый результат. Возвраты: /legal/refunds.",
    adhd10Title: "10. Контакты",
    adhd10Body:
      "Юридические уведомления: legal@ancap.cloud. Продукт: /aeterna#adhd-support. Связанные тексты: /legal/terms, /legal/risk.",
    footerAdhdSupport: "Поддержка при СДВГ",
""",
    "uk": """    adhdSupportLink: "Підтримка при СДУГ",
    hubCardAdhdSupport:
      "Бриф ліцензованого клініциста щодо підтримки при СДУГ. Не діагноз, не рецепт, не компаундинг стимуляторів, не гарантований навчальний чи фінансовий результат.",
    adhdSupportKicker: "Право / клініцист / грамотність підтримки при СДУГ",
    adhdSupportTitle: "Підтримка при СДУГ — рейл ліцензованого клініциста",
    adhdSupportIntro:
      "Як ANCAP формулює SKU підтримки при СДУГ станом на 13 вересня 2026. Ці сторінки продають брифи в ACP, а не діагнози, рецепти чи шлях до багатства.",
    adhd1Title: "1. Роль платформи",
    adhd1Body:
      "ANCAP забезпечує розрахунок в ACP, брифи та підбір ліцензованого партнера. ANCAP не ставить діагноз СДУГ і не практикує дитячу психіатрію чи неврологію.",
    adhd2Title: "2. Не діагноз і не лікування",
    adhd2Body:
      "Інфографіка — мотиваційна грамотність. Це не клінічна настанова і не лікування від ANCAP.",
    adhd3Title: "3. Заборонені обіцянки результату",
    adhd3Body:
      "ANCAP не гарантує спокій, оцінки, кар'єру чи статус мільярдера. Сходи «до мільярда» — лише мотиваційна грамотність.",
    adhd4Title: "4. Лише ліцензовані клініцисти",
    adhd4Body:
      "Будь-яка оцінка, терапія чи рішення про ліки — акт ліцензованого клініциста після скринінгу.",
    adhd5Title: "5. Грамотність інфографіки, не протокол",
    adhd5Body:
      "Фокус, планування, емоції, стосунки, самооцінка й ризики — грамотність підтримки. ANCAP не публікує SOP терапії.",
    adhd6Title: "6. Не медична порада",
    adhd6Body:
      "Тексти каталогу інформаційні. Це не діагноз, не рецепт і не план лікування.",
    adhd7Title: "7. Дані про здоров'я та дітей",
    adhd7Body:
      "Ідентифікатори й клінічна історія — чутливі. Не завантажуйте записи без законної підстави.",
    adhd8Title: "8. Зв'язок з іншими рейлами",
    adhd8Body:
      "Рейли довголіття залишаються окремими. Цей SKU не дозволяє компаундинг.",
    adhd9Title: "9. Платежі",
    adhd9Body:
      "ACP купує бриф і підбір партнера за 42 000 ACP. Повернення: /legal/refunds.",
    adhd10Title: "10. Контакти",
    adhd10Body:
      "Юридичні повідомлення: legal@ancap.cloud. Продукт: /aeterna#adhd-support.",
    footerAdhdSupport: "Підтримка при СДУГ",
""",
    "de": """    adhdSupportLink: "ADHS-Unterstützung",
    hubCardAdhdSupport:
      "Partnerbrief eines lizenzierten Klinikers zur ADHS-Unterstützung. Keine Diagnose, kein Rezept, kein Stimulanzien-Compounding, kein garantiertes Schul- oder Finanzergebnis.",
    adhdSupportKicker: "Recht / Kliniker / ADHS-Unterstützungsliteralität",
    adhdSupportTitle: "ADHS-Unterstützung — lizenzierte Kliniker-Schiene",
    adhdSupportIntro:
      "Wie ANCAP die ADHS-Unterstützungs-SKU zum 13. September 2026 rahmt. Diese Seiten verkaufen ACP-Briefs, keine Diagnosen, Rezepte, Stimulanzien oder einen garantierten Reichtumspfad.",
    adhd1Title: "1. Plattformrolle",
    adhd1Body:
      "ANCAP bietet ACP-Abrechnung, Briefs und Partner-Matching. ANCAP diagnostiziert kein ADHS, verschreibt nicht und praktiziert keine Kinderpsychiatrie oder Neurologie.",
    adhd2Title: "2. Keine Diagnose, keine Behandlung",
    adhd2Body:
      "Die Infografik ist Motivations- und Bildungsliteralität. Kein klinischer Leitfaden und keine Behandlung von ANCAP.",
    adhd3Title: "3. Verbotene Ergebnisversprechen",
    adhd3Body:
      "ANCAP garantiert keine Ruhe, Noten, Karriere oder Milliardärsstatus. Die „Milliardärs“-Treppe ist nur Motivationsliteralität.",
    adhd4Title: "4. Nur lizenzierte Kliniker",
    adhd4Body:
      "Jede Beurteilung, Therapie oder Medikamentenentscheidung ist eine Handlung eines lizenzierten Klinikers nach Screening.",
    adhd5Title: "5. Infografik-Literalität, kein Protokoll",
    adhd5Body:
      "Fokus, Planung, Emotionen, Beziehungen, Selbstwert und Risiken sind Unterstützungsliteralität. ANCAP veröffentlicht keine Stimulanzien-Dosierung oder Therapie-SOPs.",
    adhd6Title: "6. Keine medizinische Beratung",
    adhd6Body:
      "Katalogtexte sind informativ. Keine Diagnose, kein Rezept, kein Behandlungsplan.",
    adhd7Title: "7. Gesundheits- und Kinderdaten",
    adhd7Body:
      "Kennungen und klinische Historie sind sensibel. Keine Uploads ohne Rechtsgrundlage.",
    adhd8Title: "8. Verhältnis zu anderen Schienen",
    adhd8Body:
      "Longevity-Schienen bleiben getrennt. Diese SKU autorisiert kein Compounding.",
    adhd9Title: "9. Zahlungen",
    adhd9Body:
      "ACP kauft Brief und Partner-Match für 42.000 ACP. Rückerstattungen: /legal/refunds.",
    adhd10Title: "10. Kontakt",
    adhd10Body:
      "Rechtliches: legal@ancap.cloud. Produkt: /aeterna#adhd-support.",
    footerAdhdSupport: "ADHS-Unterstützung",
""",
    "zh-Hant": """    adhdSupportLink: "ADHD／注意力不足過動支援",
    hubCardAdhdSupport:
      "持照臨床醫師 ADHD 支援素養簡報。非診斷、非處方、非興奮劑配製、非保證學業或財務結果。",
    adhdSupportKicker: "法律／臨床醫師／ADHD 支援素養",
    adhdSupportTitle: "ADHD 支援 — 持照臨床醫師夥伴軌道",
    adhdSupportIntro:
      "ANCAP 於 2026 年 9 月 13 日對 ADHD 支援 SKU 的表述。這些頁面販售 ACP 結算簡報，而非診斷、處方、興奮劑或致富保證。",
    adhd1Title: "1. 平台角色",
    adhd1Body:
      "ANCAP 提供 ACP 結算、簡報與持照夥伴媒合。ANCAP 不診斷 ADHD、不開方、不配製興奮劑，亦不執業兒童精神醫學或神經科。",
    adhd2Title: "2. 非診斷、非治療",
    adhd2Body:
      "資訊圖為動機與教育素養。非臨床指引，亦非 ANCAP 販售之治療。",
    adhd3Title: "3. 禁止結果宣稱",
    adhd3Body:
      "ANCAP 不保證安靜行為、成績、職涯、創業或成為億萬富翁。「通往十億」階梯僅為動機素養。",
    adhd4Title: "4. 僅持照臨床醫師",
    adhd4Body:
      "任何評估、治療或用藥決定均為持照臨床醫師於篩檢後之行為。這些頁面不可取代專業照護。",
    adhd5Title: "5. 資訊圖素養，非協議",
    adhd5Body:
      "專注、規劃、情緒、關係、自尊與風險圖示為支援素養。ANCAP 不公開興奮劑劑量或治療 SOP。",
    adhd6Title: "6. 非醫療建議",
    adhd6Body:
      "目錄文案僅供資訊。非診斷、非處方、非治療計畫。",
    adhd7Title: "7. 健康與兒童資料",
    adhd7Body:
      "識別碼與臨床病史屬敏感資料。無合法基礎請勿上傳紀錄。",
    adhd8Title: "8. 與其他軌道之關係",
    adhd8Body:
      "長壽軌道仍為獨立。此 SKU 不授權配製或未持照執業。",
    adhd9Title: "9. 付款",
    adhd9Body:
      "ACP 以 42,000 ACP 購買簡報與夥伴媒合。退款依 /legal/refunds。",
    adhd10Title: "10. 聯絡",
    adhd10Body:
      "法律通知：legal@ancap.cloud。產品：/aeterna#adhd-support。",
    footerAdhdSupport: "ADHD 支援",
""",
}


def patch_aeterna() -> None:
    path = ROOT / "aeterna.ts"
    text = path.read_text(encoding="utf-8")
    if "intent20Title" in text:
        print("aeterna.ts already patched")
        return
    for lang in LANGS:
        start, end = bounds(text, lang)
        section = text[start:end]
        section = insert_after_intent19(section, INTENTS[lang])
        section = insert_after_sbm6(section, PANELS[lang])
        for old, new in HERO_PAY.get(lang, []):
            section = replace_once(section, old, new)
        text = text[:start] + section + text[end:]
    path.write_text(text, encoding="utf-8")
    print("patched aeterna.ts")


def patch_legal() -> None:
    path = ROOT / "legal.ts"
    text = path.read_text(encoding="utf-8")
    if "adhdSupportLink" in text:
        print("legal.ts already patched")
        return
    for lang in LANGS:
        start, end = bounds(text, lang)
        section = text[start:end]
        marker = "footerSyntheticBloodMamba:"
        idx = section.find(marker)
        if idx < 0:
            raise SystemExit(f"no footerSyntheticBloodMamba in {lang}")
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
