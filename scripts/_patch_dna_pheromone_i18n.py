# -*- coding: utf-8 -*-
from pathlib import Path

aeterna = Path("frontend-app/src/locales/aeterna.ts")
text = aeterna.read_text(encoding="utf-8")

blocks = {
    "en": """
    intent25Title: "DNA-matched pheromone perfume (1 bottle)",
    intent25Body:
      "Licensed cosmetic / fragrance partner fill informed by an optional DNA-vault hash — 8,900 ACP per bottle. Not a drug, not an aphrodisiac claim, not a guaranteed attraction outcome.",

    ppfCta: "Buy 1 bottle",
    ppfVaultCta: "Open DNA vault",
    ppfLegalCta: "Perfume legal notice",
    ppfKicker: "AETERNA · fragrance · DNA match literacy",
    ppfTitle: "Pheromone perfume matched to your DNA",
    ppfPrice: "8,900 ACP",
    ppfUnit: "per 1 bottle",
    ppfLead:
      "One bottle at a time. Optional DNA-vault content hash informs olfactory-profile literacy for a licensed cosmetic partner who blends a pheromone-forward fragrance and fills a single vial.",
    ppfDisclaimer:
      "ANCAP does not compound drugs, does not upload genome bytes, does not claim aphrodisiac or attraction results, and does not sell CE/FDA pheromone medicine. Physical fill and labeling stay with the licensed fragrance partner after screening.",
    ppfStep1Title: "Vault hash",
    ppfStep1Body: "Optional local hash → olfactory theme literacy. No genome upload.",
    ppfStep2Title: "Blend",
    ppfStep2Body: "Pheromone-forward fragrance literacy with skin-safe carrier notes.",
    ppfStep3Title: "1 bottle",
    ppfStep3Body: "Sale unit is exactly one vial. Order again for the next bottle.",
    ppfStep4Title: "Handoff",
    ppfStep4Body: "ACP buys partner fill + brief — not a drug prescription.",
""",
    "ru": """
    intent25Title: "Духи с феромонами под ДНК (1 флакон)",
    intent25Body:
      "Лицензированный косметический / парфюмерный партнёрский розлив с учётом опционального хеша DNA-vault — 8 900 ACP за 1 флакон. Не лекарство, не афродизиак-клейм, не гарантия притяжения.",

    ppfCta: "Купить 1 флакон",
    ppfVaultCta: "Открыть DNA vault",
    ppfLegalCta: "Юр. текст духов",
    ppfKicker: "AETERNA · парфюм · грамотность ДНК-матча",
    ppfTitle: "Духи с феромонами, подобранные по ДНК",
    ppfPrice: "8 900 ACP",
    ppfUnit: "за 1 флакон",
    ppfLead:
      "Продажа строго по одному флакону. Опциональный хеш DNA-vault задаёт грамотность обонятельного профиля для лицензированного косметического партнёра, который смешивает феромонный аромат и разливает один флакон.",
    ppfDisclaimer:
      "ANCAP не компаундит лекарства, не загружает геном, не обещает афродизиак или результат «притяжения» и не продаёт CE/FDA-феромонную медицину. Физический розлив и этикетка — у лицензированного парфюмерного партнёра после скрининга.",
    ppfStep1Title: "Хеш vault",
    ppfStep1Body: "Опциональный локальный хеш → грамотность арома-темы. Без загрузки генома.",
    ppfStep2Title: "Смесь",
    ppfStep2Body: "Феромонный аромат и безопасный для кожи носитель — literacy.",
    ppfStep3Title: "1 флакон",
    ppfStep3Body: "Единица продажи — ровно один флакон. Следующий — отдельный заказ.",
    ppfStep4Title: "Handoff",
    ppfStep4Body: "ACP оплачивает партнёрский розлив и бриф — не рецепт.",
""",
    "uk": """
    intent25Title: "Парфуми з феромонами під ДНК (1 флакон)",
    intent25Body:
      "Ліцензований косметичний / парфумерний партнерський розлив з урахуванням опційного хешу DNA-vault — 8 900 ACP за 1 флакон. Не ліки, не афродизіак-клейм, не гарантія притягання.",

    ppfCta: "Купити 1 флакон",
    ppfVaultCta: "Відкрити DNA vault",
    ppfLegalCta: "Юр. текст парфумів",
    ppfKicker: "AETERNA · парфум · грамотність ДНК-матчу",
    ppfTitle: "Парфуми з феромонами, підібрані за ДНК",
    ppfPrice: "8 900 ACP",
    ppfUnit: "за 1 флакон",
    ppfLead:
      "Продаж строго по одному флакону. Опційний хеш DNA-vault задає грамотність нюхового профілю для ліцензованого косметичного партнера, який змішує феромонний аромат і розливає один флакон.",
    ppfDisclaimer:
      "ANCAP не компаундить ліки, не завантажує геном, не обіцяє афродизіак або результат «притягання» і не продає CE/FDA-феромонну медицину. Фізичний розлив і етикетка — у ліцензованого парфумерного партнера після скринінгу.",
    ppfStep1Title: "Хеш vault",
    ppfStep1Body: "Опційний локальний хеш → грамотність арома-теми. Без завантаження геному.",
    ppfStep2Title: "Суміш",
    ppfStep2Body: "Феромонний аромат і безпечний для шкіри носій — literacy.",
    ppfStep3Title: "1 флакон",
    ppfStep3Body: "Одиниця продажу — рівно один флакон. Наступний — окреме замовлення.",
    ppfStep4Title: "Handoff",
    ppfStep4Body: "ACP оплачує партнерський розлив і бриф — не рецепт.",
""",
    "de": """
    intent25Title: "DNA-abgestimmtes Pheromon-Parfuem (1 Flasche)",
    intent25Body:
      "Lizenzierter Kosmetik- / Duftpartner-Abfuellung mit optionalem DNA-Vault-Hash — 8.900 ACP pro Flasche. Kein Arzneimittel, kein Aphrodisiakum-Claim, kein garantiertes Anziehungsergebnis.",

    ppfCta: "1 Flasche kaufen",
    ppfVaultCta: "DNA-Vault oeffnen",
    ppfLegalCta: "Parfuem-Rechtshinweis",
    ppfKicker: "AETERNA · Duft · DNA-Match-Literalitaet",
    ppfTitle: "Pheromon-Parfuem nach Ihrer DNA",
    ppfPrice: "8.900 ACP",
    ppfUnit: "pro 1 Flasche",
    ppfLead:
      "Verkauf streng pro Flasche. Ein optionaler DNA-Vault-Hash informiert die olfaktorische Profil-Literalitaet fuer einen lizenzierten Kosmetikpartner, der eine pheromonbetonte Duftnote mischt und eine einzelne Flasche abfuellt.",
    ppfDisclaimer:
      "ANCAP compoundiert keine Arzneimittel, laedt keine Genomdaten hoch, verspricht kein Aphrodisiakum oder Anziehungsergebnis und verkauft keine CE/FDA-Pheromonmedizin. Abfuellung und Etikett bleiben beim lizenzierten Duftpartner nach Screening.",
    ppfStep1Title: "Vault-Hash",
    ppfStep1Body: "Optionaler lokaler Hash → Duft-Themen-Literalitaet. Kein Genom-Upload.",
    ppfStep2Title: "Mischung",
    ppfStep2Body: "Pheromonbetonter Duft mit hautsicherem Traeger — Literacy.",
    ppfStep3Title: "1 Flasche",
    ppfStep3Body: "Verkaufseinheit ist genau eine Flasche. Naechste = neuer Auftrag.",
    ppfStep4Title: "Handoff",
    ppfStep4Body: "ACP kauft Partner-Abfuellung + Brief — kein Rezept.",
""",
    "zh": """
    intent25Title: "DNA 匹配費洛蒙香水（1 瓶）",
    intent25Body:
      "持照化妝品／香水夥伴灌裝，可選 DNA vault 雜湊參考 — 每瓶 8,900 ACP。非藥品、非催情宣稱、非保證吸引結果。",

    ppfCta: "購買 1 瓶",
    ppfVaultCta: "開啟 DNA vault",
    ppfLegalCta: "香水法律聲明",
    ppfKicker: "AETERNA · 香水 · DNA 匹配素養",
    ppfTitle: "依 DNA 匹配的費洛蒙香水",
    ppfPrice: "8,900 ACP",
    ppfUnit: "每 1 瓶",
    ppfLead:
      "嚴格以單瓶販售。可選 DNA vault 內容雜湊提供嗅覺輪廓素養，由持照化妝品夥伴調配費洛蒙導向香調並灌裝單瓶。",
    ppfDisclaimer:
      "ANCAP 不調配藥品、不上傳基因組、不承諾催情或吸引結果，亦不販售 CE/FDA 費洛蒙藥品。實體灌裝與標籤留在通過審查的持照香水夥伴。",
    ppfStep1Title: "Vault 雜湊",
    ppfStep1Body: "可選本地雜湊 → 香調素養。無基因組上傳。",
    ppfStep2Title: "調配",
    ppfStep2Body: "費洛蒙導向香調與膚用載體 — literacy。",
    ppfStep3Title: "1 瓶",
    ppfStep3Body: "銷售單位恰為一瓶。下一瓶需另下單。",
    ppfStep4Title: "交接",
    ppfStep4Body: "ACP 購買夥伴灌裝與簡報 — 非處方。",
""",
}

marker = "    vetKicker:"
parts = text.split(marker)
if len(parts) != 6:
    raise SystemExit(f"expected 6 parts, got {len(parts)}")
order = ["en", "ru", "uk", "de", "zh"]
out_parts = []
for i, lang in enumerate(order):
    segment = parts[i]
    if "ppfKicker:" not in segment[-2000:]:
        segment = segment.rstrip() + "\n" + blocks[lang] + "\n"
    out_parts.append(segment)
    out_parts.append(marker)
out_parts.append(parts[-1])
aeterna.write_text("".join(out_parts), encoding="utf-8")
print("aeterna ppfKicker count", "".join(out_parts).count("ppfKicker:"))

# --- legal.ts ---
legal = Path("frontend-app/src/locales/legal.ts")
ltext = legal.read_text(encoding="utf-8")

legal_blocks = {
    "en": """
    dnaPheromonePerfumeLink: "DNA pheromone perfume",
    hubCardDnaPheromonePerfume: "Per-bottle DNA-matched pheromone fragrance via licensed cosmetic partner — not a drug or aphrodisiac claim.",
    dnaPheromonePerfumeKicker: "Legal / cosmetic fragrance literacy",
    dnaPheromonePerfumeTitle: "DNA-matched pheromone perfume — legal notice",
    dnaPheromonePerfumeIntro: "13 September 2026. Sale unit is one bottle (8,900 ACP).",
    ppf1Title: "1. Platform role",
    ppf1Body: "ANCAP settles ACP and issues a licensed cosmetic / fragrance partner handoff. Physical bottle fill stays with the partner.",
    ppf2Title: "2. DNA matching",
    ppf2Body: "Optional DNA-vault content hash may inform olfactory-profile literacy. Genome bytes are never uploaded to ANCAP.",
    ppf3Title: "3. Unit of sale",
    ppf3Body: "Each order is for exactly one bottle. Additional bottles require a new order.",
    ppf4Title: "4. Not a drug",
    ppf4Body: "This rail is not a medicine, not CE/FDA pheromone therapy, and not compounding of controlled substances.",
    ppf5Title: "5. No aphrodisiac claim",
    ppf5Body: "ANCAP does not claim guaranteed attraction, relationship, or sexual outcomes.",
    ppf6Title: "6. Partner screening",
    ppf6Body: "Fragrance partners must pass ANCAP screening before receiving a handoff.",
    ppf7Title: "7. Skin safety",
    ppf7Body: "Patch testing and ingredient disclosure remain with the licensed partner under local cosmetic law.",
    ppf8Title: "8. Minors",
    ppf8Body: "Not marketed for children. Local age-of-purchase rules for fragrance apply.",
    ppf9Title: "9. Refunds",
    ppf9Body: "ACP settlement follows ANCAP refunds policy once partner fill has started; unused draft intents may cancel.",
    ppf10Title: "10. Contact",
    ppf10Body: "Questions: legal@ancap.cloud. Product surface: /aeterna#dna-pheromone-perfume.",
""",
    "ru": """
    dnaPheromonePerfumeLink: "Духи с феромонами (ДНК)",
    hubCardDnaPheromonePerfume: "Продажа по флакону: феромонный аромат под ДНК через лицензированного косметического партнёра — не лекарство и не афродизиак-клейм.",
    dnaPheromonePerfumeKicker: "Юридическое / косметическая грамотность",
    dnaPheromonePerfumeTitle: "Духи с феромонами под ДНК — юридическое уведомление",
    dnaPheromonePerfumeIntro: "13 сентября 2026. Единица продажи — 1 флакон (8 900 ACP).",
    ppf1Title: "1. Роль платформы",
    ppf1Body: "ANCAP проводит расчёт в ACP и выдаёт handoff лицензированному косметическому / парфюмерному партнёру. Физический розлив — у партнёра.",
    ppf2Title: "2. ДНК-матч",
    ppf2Body: "Опциональный хеш DNA-vault может задавать грамотность обонятельного профиля. Байты генома на ANCAP не загружаются.",
    ppf3Title: "3. Единица продажи",
    ppf3Body: "Каждый заказ — ровно один флакон. Следующие флаконы — отдельный заказ.",
    ppf4Title: "4. Не лекарство",
    ppf4Body: "Это не медицина, не CE/FDA-феромонная терапия и не компаундинг контролируемых веществ.",
    ppf5Title: "5. Без афродизиак-клейма",
    ppf5Body: "ANCAP не обещает гарантированного притяжения, отношений или сексуального результата.",
    ppf6Title: "6. Скрининг партнёра",
    ppf6Body: "Парфюмерные партнёры проходят скрининг ANCAP до handoff.",
    ppf7Title: "7. Безопасность кожи",
    ppf7Body: "Патч-тест и раскрытие состава остаются у лицензированного партнёра по местному косметическому праву.",
    ppf8Title: "8. Несовершеннолетние",
    ppf8Body: "Не для детей. Действуют местные возрастные правила покупки парфюмерии.",
    ppf9Title: "9. Возвраты",
    ppf9Body: "Расчёт ACP следует политике возвратов ANCAP после начала розлива; неиспользованные draft-интенты можно отменить.",
    ppf10Title: "10. Контакт",
    ppf10Body: "Вопросы: legal@ancap.cloud. Продукт: /aeterna#dna-pheromone-perfume.",
""",
    "uk": """
    dnaPheromonePerfumeLink: "Парфуми з феромонами (ДНК)",
    hubCardDnaPheromonePerfume: "Продаж по флакону: феромонний аромат під ДНК через ліцензованого косметичного партнера — не ліки і не афродизіак-клейм.",
    dnaPheromonePerfumeKicker: "Юридичне / косметична грамотність",
    dnaPheromonePerfumeTitle: "Парфуми з феромонами під ДНК — юридичне повідомлення",
    dnaPheromonePerfumeIntro: "13 вересня 2026. Одиниця продажу — 1 флакон (8 900 ACP).",
    ppf1Title: "1. Роль платформи",
    ppf1Body: "ANCAP проводить розрахунок в ACP і видає handoff ліцензованому косметичному / парфумерному партнеру. Фізичний розлив — у партнера.",
    ppf2Title: "2. ДНК-матч",
    ppf2Body: "Опційний хеш DNA-vault може задавати грамотність нюхового профілю. Байти геному на ANCAP не завантажуються.",
    ppf3Title: "3. Одиниця продажу",
    ppf3Body: "Кожне замовлення — рівно один флакон. Наступні флакони — окреме замовлення.",
    ppf4Title: "4. Не ліки",
    ppf4Body: "Це не медицина, не CE/FDA-феромонна терапія і не компаундинг контрольованих речовин.",
    ppf5Title: "5. Без афродизіак-клейму",
    ppf5Body: "ANCAP не обіцяє гарантованого притягання, стосунків чи сексуального результату.",
    ppf6Title: "6. Скринінг партнера",
    ppf6Body: "Парфумерні партнери проходять скринінг ANCAP до handoff.",
    ppf7Title: "7. Безпека шкіри",
    ppf7Body: "Патч-тест і розкриття складу залишаються у ліцензованого партнера за місцевим косметичним правом.",
    ppf8Title: "8. Неповнолітні",
    ppf8Body: "Не для дітей. Діють місцеві вікові правила купівлі парфумерії.",
    ppf9Title: "9. Повернення",
    ppf9Body: "Розрахунок ACP слідує політиці повернень ANCAP після початку розливу; невикористані draft-інтенти можна скасувати.",
    ppf10Title: "10. Контакт",
    ppf10Body: "Питання: legal@ancap.cloud. Продукт: /aeterna#dna-pheromone-perfume.",
""",
    "de": """
    dnaPheromonePerfumeLink: "DNA-Pheromon-Parfuem",
    hubCardDnaPheromonePerfume: "Pro Flasche: DNA-abgestimmter Pheromonduft ueber lizenzierten Kosmetikpartner — kein Arzneimittel, kein Aphrodisiakum-Claim.",
    dnaPheromonePerfumeKicker: "Recht / kosmetische Duft-Literalitaet",
    dnaPheromonePerfumeTitle: "DNA-abgestimmtes Pheromon-Parfuem — Rechtshinweis",
    dnaPheromonePerfumeIntro: "13. September 2026. Verkaufseinheit ist eine Flasche (8.900 ACP).",
    ppf1Title: "1. Plattformrolle",
    ppf1Body: "ANCAP settelt ACP und stellt einen Handoff an einen lizenzierten Kosmetik-/Duftpartner aus. Abfuellung bleibt beim Partner.",
    ppf2Title: "2. DNA-Matching",
    ppf2Body: "Optionaler DNA-Vault-Hash kann olfaktorische Profil-Literalitaet informieren. Genombytes werden nicht hochgeladen.",
    ppf3Title: "3. Verkaufseinheit",
    ppf3Body: "Jede Bestellung gilt fuer genau eine Flasche. Weitere Flaschen erfordern neue Auftraege.",
    ppf4Title: "4. Kein Arzneimittel",
    ppf4Body: "Keine Medizin, keine CE/FDA-Pheromontherapie, kein Compounding kontrollierter Stoffe.",
    ppf5Title: "5. Kein Aphrodisiakum-Claim",
    ppf5Body: "ANCAP verspricht keine garantierte Anziehung, Beziehung oder sexuelle Wirkung.",
    ppf6Title: "6. Partner-Screening",
    ppf6Body: "Duftpartner muessen ANCAP-Screening vor dem Handoff bestehen.",
    ppf7Title: "7. Hautsicherheit",
    ppf7Body: "Patch-Test und Inhaltsstoffe bleiben beim lizenzierten Partner nach lokalem Kosmetikrecht.",
    ppf8Title: "8. Minderjaehrige",
    ppf8Body: "Nicht fuer Kinder. Lokale Altersregeln fuer Parfuemkauf gelten.",
    ppf9Title: "9. Rueckerstattungen",
    ppf9Body: "ACP folgt der ANCAP-Refund-Policy nach Start der Abfuellung; ungenutzte Draft-Intents koennen storniert werden.",
    ppf10Title: "10. Kontakt",
    ppf10Body: "Fragen: legal@ancap.cloud. Produkt: /aeterna#dna-pheromone-perfume.",
""",
    "zh": """
    dnaPheromonePerfumeLink: "DNA 費洛蒙香水",
    hubCardDnaPheromonePerfume: "按瓶販售：經持照化妝品夥伴的 DNA 匹配費洛蒙香氛 — 非藥品、非催情宣稱。",
    dnaPheromonePerfumeKicker: "法律／化妝品香氛素養",
    dnaPheromonePerfumeTitle: "DNA 匹配費洛蒙香水 — 法律聲明",
    dnaPheromonePerfumeIntro: "2026 年 9 月 13 日。銷售單位為一瓶（8,900 ACP）。",
    ppf1Title: "1. 平台角色",
    ppf1Body: "ANCAP 以 ACP 結算並向持照化妝品／香水夥伴發出交接。實體灌裝由夥伴完成。",
    ppf2Title: "2. DNA 匹配",
    ppf2Body: "可選 DNA vault 內容雜湊可提供嗅覺輪廓素養。基因組位元組不會上傳至 ANCAP。",
    ppf3Title: "3. 銷售單位",
    ppf3Body: "每筆訂單恰為一瓶。額外瓶數需另下單。",
    ppf4Title: "4. 非藥品",
    ppf4Body: "非藥品、非 CE/FDA 費洛蒙治療、非受控物質調配。",
    ppf5Title: "5. 無催情宣稱",
    ppf5Body: "ANCAP 不保證吸引、關係或性結果。",
    ppf6Title: "6. 夥伴審查",
    ppf6Body: "香水夥伴須通過 ANCAP 審查後方可交接。",
    ppf7Title: "7. 皮膚安全",
    ppf7Body: "貼膚測試與成分揭露依當地化妝品法由持照夥伴負責。",
    ppf8Title: "8. 未成年人",
    ppf8Body: "非針對兒童行銷。適用當地香水購買年齡規定。",
    ppf9Title: "9. 退款",
    ppf9Body: "一旦夥伴開始灌裝，ACP 結算依 ANCAP 退款政策；未使用的 draft intent 可取消。",
    ppf10Title: "10. 聯絡",
    ppf10Body: "問題：legal@ancap.cloud。產品：/aeterna#dna-pheromone-perfume。",
""",
}

# Insert before each stardustLink or after installationProjectLink block
# Find installationProjectIntro occurrences - insert after ip10Body blocks
# Easier: insert before "    stardustLink:" in each language
smarker = "    stardustLink:"
lparts = ltext.split(smarker)
if len(lparts) != 6:
    raise SystemExit(f"legal expected 6 parts, got {len(lparts)}")
lout = []
for i, lang in enumerate(order):
    segment = lparts[i]
    if "dnaPheromonePerfumeLink:" not in segment[-2500:]:
        segment = segment.rstrip() + "\n" + legal_blocks[lang] + "\n"
    lout.append(segment)
    lout.append(smarker)
lout.append(lparts[-1])
legal.write_text("".join(lout), encoding="utf-8")
print("legal dnaPheromonePerfumeLink count", "".join(lout).count("dnaPheromonePerfumeLink:"))
print("done")
