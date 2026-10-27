from pathlib import Path

# translations.ts — darkMatterPage bindings
tp = Path("frontend-app/src/locales/translations.ts")
t = tp.read_text(encoding="utf-8")
for lang, expr in [
    ("en", "floraByLang.en"),
    ("ru", "floraByLang.ru"),
    ("uk", "floraByLang.uk"),
    ("de", "floraByLang.de"),
    ("zh", 'floraByLang["zh-Hant"]'),
]:
    old = f"floraPage: {expr},"
    dm_expr = expr.replace("floraByLang", "darkMatterByLang")
    new = f"floraPage: {expr},\n    darkMatterPage: {dm_expr},"
    if "darkMatterPage: darkMatterByLang" in t and f"darkMatterPage: {dm_expr}" in t:
        continue
    if old not in t:
        raise SystemExit(f"missing {old}")
    t = t.replace(old, new, 1)
tp.write_text(t, encoding="utf-8")
print("translations darkMatterPage:", t.count("darkMatterPage"))

# legal.ts — insert EN block after stardust contact / before next section if needed
# Find stardustLink and insert dark matter keys after stardust section for each lang.
# Simpler: insert after counsel block or after stardustLink line clusters.

lp = Path("frontend-app/src/locales/legal.ts")
legal = lp.read_text(encoding="utf-8")

EN_BLOCK = '''
    darkMatterLink: "Dark matter auction",
    hubCardDarkMatter: "Symbolic ACP cosmology titles for dark-matter halo / filament / detector literacy — not physical DM ownership.",
    darkMatterKicker: "Legal / dark matter auction",
    darkMatterTitle: "Dark matter auction — legal notice",
    darkMatterIntro: "14 September 2026. ANCAP dark-matter lots are symbolic ACP title RFQs and cosmology literacy only.",
    dm1Title: "1. Platform role",
    dm1Body: "ANCAP settles ACP bids for symbolic dark-matter title claims and detector / cosmology literacy briefs. ANCAP does not sell or transfer physical dark matter.",
    dm2Title: "2. No physical ownership",
    dm2Body: "A winning bid does not confer ownership, possession, custody, or extraction rights over any physical dark-matter particle, halo mass, or cosmological field.",
    dm3Title: "3. Outer Space Treaty / sovereignty",
    dm3Body: "Lots do not grant sovereignty, territorial claims, or rights under the Outer Space Treaty or any national space statute.",
    dm4Title: "4. Not a detection certificate",
    dm4Body: "Catalog copy and bid receipts are not scientific detection certificates, lab bookings, survey licenses, or peer-reviewed claims.",
    dm5Title: "5. Detector literacy partners",
    dm5Body: "Detector-themed lots are partner literacy / handoff briefs only. Licensed laboratory partners remain independent and set their own engagement terms.",
    dm6Title: "6. No outcome guarantee",
    dm6Body: "ANCAP does not guarantee cosmological discoveries, detector exposures, publication outcomes, or investment returns.",
    dm7Title: "7. Related desks",
    dm7Body: "Galaxy body / radiation titles remain on /galaxy. Dark-matter cosmology titles are on /dark-matter. Both are symbolic ACP desks.",
    dm8Title: "8. Insurance",
    dm8Body: "Optional parametric cover may be offered under coverage class dark_matter_title via /insurance. Policies do not create physical DM ownership.",
    dm9Title: "9. Refunds",
    dm9Body: "ACP settlement for bids follows ANCAP refunds policy once a sealed bid deal is recorded; review /legal/refunds.",
    dm10Title: "10. Contact",
    dm10Body: "Questions: legal@ancap.cloud. Product: /dark-matter.",
'''

RU_BLOCK = '''
    darkMatterLink: "Аукцион тёмной материи",
    hubCardDarkMatter: "Символические ACP-титулы космологии тёмной материи (halo / filament / детекторы) — не владение физической ТМ.",
    darkMatterKicker: "Правовое / аукцион тёмной материи",
    darkMatterTitle: "Аукцион тёмной материи — юридическое уведомление",
    darkMatterIntro: "14 сентября 2026. Лоты тёмной материи ANCAP — только символические ACP RFQ и космологическая грамотность.",
    dm1Title: "1. Роль платформы",
    dm1Body: "ANCAP принимает ставки ACP за символические титулы тёмной материи и брифы детекторов / космологии. ANCAP не продаёт и не передаёт физическую тёмную материю.",
    dm2Title: "2. Нет физического владения",
    dm2Body: "Выигрышная ставка не даёт права собственности, владения, хранения или извлечения какой-либо физической частицы или поля тёмной материи.",
    dm3Title: "3. Договор по космосу / суверенитет",
    dm3Body: "Лоты не дают суверенитета, территориальных претензий или прав по Outer Space Treaty либо национальному космическому праву.",
    dm4Title: "4. Не сертификат детекции",
    dm4Body: "Тексты каталога и чеки ставок не являются научными сертификатами детекции, бронями лабораторий, лицензиями обзоров или peer-reviewed заявлениями.",
    dm5Title: "5. Партнёры по детекторам",
    dm5Body: "Лоты про детекторы — только literacy / handoff. Лицензированные лабораторные партнёры независимы и сами задают условия работы.",
    dm6Title: "6. Без гарантии исхода",
    dm6Body: "ANCAP не гарантирует открытия, экспозиции детекторов, публикации или инвестиционную доходность.",
    dm7Title: "7. Связанные столы",
    dm7Body: "Титулы тел / излучения — на /galaxy. Космология тёмной материи — на /dark-matter. Оба стола символические ACP.",
    dm8Title: "8. Страхование",
    dm8Body: "Опциональное параметрическое покрытие может предлагаться как dark_matter_title на /insurance. Полисы не создают владения физической ТМ.",
    dm9Title: "9. Возвраты",
    dm9Body: "Расчёт ACP по ставкам следует политике возвратов ANCAP после записи sealed deal; см. /legal/refunds.",
    dm10Title: "10. Контакт",
    dm10Body: "Вопросы: legal@ancap.cloud. Продукт: /dark-matter.",
'''

UK_BLOCK = '''
    darkMatterLink: "Аукціон темної матерії",
    hubCardDarkMatter: "Символічні ACP-титули космології темної матерії (halo / filament / детектори) — не володіння фізичною ТМ.",
    darkMatterKicker: "Правове / аукціон темної матерії",
    darkMatterTitle: "Аукціон темної матерії — юридичне повідомлення",
    darkMatterIntro: "14 вересня 2026. Лоти темної матерії ANCAP — лише символічні ACP RFQ та космологічна грамотність.",
    dm1Title: "1. Роль платформи",
    dm1Body: "ANCAP приймає ставки ACP за символічні титули темної матерії та бріфи детекторів / космології. ANCAP не продає і не передає фізичну темну матерію.",
    dm2Title: "2. Немає фізичного володіння",
    dm2Body: "Виграшна ставка не дає права власності, володіння, зберігання чи вилучення будь-якої фізичної частинки чи поля темної матерії.",
    dm3Title: "3. Договір про космос / суверенітет",
    dm3Body: "Лоти не дають суверенітету, територіальних претензій чи прав за Outer Space Treaty або національним космічним правом.",
    dm4Title: "4. Не сертифікат детекції",
    dm4Body: "Тексти каталогу та чеки ставок не є науковими сертифікатами детекції, бронюваннями лабораторій чи peer-reviewed заявами.",
    dm5Title: "5. Партнери з детекторів",
    dm5Body: "Лоти про детектори — лише literacy / handoff. Ліцензовані лабораторні партнери незалежні.",
    dm6Title: "6. Без гарантії результату",
    dm6Body: "ANCAP не гарантує відкриттів, експозицій детекторів, публікацій чи інвестиційної дохідності.",
    dm7Title: "7. Пов’язані столи",
    dm7Body: "Титули тіл / випромінювання — на /galaxy. Космологія темної матерії — на /dark-matter.",
    dm8Title: "8. Страхування",
    dm8Body: "Опційне параметричне покриття може пропонуватися як dark_matter_title на /insurance.",
    dm9Title: "9. Повернення",
    dm9Body: "Розрахунок ACP за ставками відповідає політиці повернень ANCAP; див. /legal/refunds.",
    dm10Title: "10. Контакт",
    dm10Body: "Питання: legal@ancap.cloud. Продукт: /dark-matter.",
'''

DE_BLOCK = '''
    darkMatterLink: "Dunkle-Materie-Auktion",
    hubCardDarkMatter: "Symbolische ACP-Kosmologie-Titel für Halo/Filament/Detektor-Literacy — kein physisches DM-Eigentum.",
    darkMatterKicker: "Rechtliches / Dunkle-Materie-Auktion",
    darkMatterTitle: "Dunkle-Materie-Auktion — rechtlicher Hinweis",
    darkMatterIntro: "14. September 2026. ANCAP-Dunkle-Materie-Lose sind nur symbolische ACP-Titel-RFQs und Kosmologie-Literacy.",
    dm1Title: "1. Plattformrolle",
    dm1Body: "ANCAP verrechnet ACP-Gebote für symbolische Dunkle-Materie-Titel und Detektor-/Kosmologie-Briefs. ANCAP verkauft oder überträgt keine physische dunkle Materie.",
    dm2Title: "2. Kein physisches Eigentum",
    dm2Body: "Ein Gewinngebot begründet kein Eigentum, Besitz, Verwahrung oder Extraktionsrechte an physischer dunkler Materie.",
    dm3Title: "3. Outer Space Treaty / Souveränität",
    dm3Body: "Lose verleihen keine Souveränität, Gebietsansprüche oder Rechte nach dem Outer Space Treaty.",
    dm4Title: "4. Kein Detektionszertifikat",
    dm4Body: "Katalogtexte und Gebotsbelege sind keine wissenschaftlichen Detektionszertifikate oder Lab-Buchungen.",
    dm5Title: "5. Detektor-Partner",
    dm5Body: "Detektor-Lose sind nur Literacy/Handoff. Lizenzierte Laborpartner bleiben unabhängig.",
    dm6Title: "6. Keine Ergebnisgarantie",
    dm6Body: "ANCAP garantiert keine Entdeckungen, Detektor-Expositionen, Publikationen oder Renditen.",
    dm7Title: "7. Verwandte Desks",
    dm7Body: "Körper-/Strahlungs-Titel: /galaxy. Dunkle-Materie-Kosmologie: /dark-matter.",
    dm8Title: "8. Versicherung",
    dm8Body: "Optionale parametrische Deckung dark_matter_title über /insurance. Policen schaffen kein physisches DM-Eigentum.",
    dm9Title: "9. Rückerstattungen",
    dm9Body: "ACP-Abrechnung folgt der ANCAP-Refund-Policy; siehe /legal/refunds.",
    dm10Title: "10. Kontakt",
    dm10Body: "Fragen: legal@ancap.cloud. Produkt: /dark-matter.",
'''

ZH_BLOCK = '''
    darkMatterLink: "暗物質拍賣",
    hubCardDarkMatter: "暗物質暈／纖維／探測器素養的象徵性 ACP 宇宙學標題——非實體暗物質所有權。",
    darkMatterKicker: "法律／暗物質拍賣",
    darkMatterTitle: "暗物質拍賣 — 法律聲明",
    darkMatterIntro: "2026 年 9 月 14 日。ANCAP 暗物質標的僅為象徵性 ACP 標題 RFQ 與宇宙學素養。",
    dm1Title: "1. 平台角色",
    dm1Body: "ANCAP 以 ACP 結算象徵性暗物質標題與探測器／宇宙學簡報。ANCAP 不出售或移轉實體暗物質。",
    dm2Title: "2. 無實體所有權",
    dm2Body: "得標不構成對任何實體暗物質粒子、暈質量或宇宙場之所有、占有、保管或開採權。",
    dm3Title: "3. 外空條約／主權",
    dm3Body: "標的不授予主權、領土主張或 Outer Space Treaty 下之權利。",
    dm4Title: "4. 非探測證書",
    dm4Body: "目錄文案與出價收據不是科學探測證書、實驗室預約或同儕審查主張。",
    dm5Title: "5. 探測器夥伴",
    dm5Body: "探測器主題標的僅為素養／交接。持照實驗室夥伴獨立訂約。",
    dm6Title: "6. 無結果保證",
    dm6Body: "ANCAP 不保證發現、探測曝光、發表或投資報酬。",
    dm7Title: "7. 相關交易台",
    dm7Body: "天體／輻射標題在 /galaxy。暗物質宇宙學標題在 /dark-matter。",
    dm8Title: "8. 保險",
    dm8Body: "可選參數化保障 dark_matter_title 見 /insurance。保單不創造實體暗物質所有權。",
    dm9Title: "9. 退款",
    dm9Body: "出價 ACP 結算依 ANCAP 退款政策；見 /legal/refunds。",
    dm10Title: "10. 聯絡",
    dm10Body: "問題：legal@ancap.cloud。產品：/dark-matter。",
'''

if "darkMatterLink:" not in legal:
    # Insert after each counselLink block's cn10Body — more reliably after stardustLink
    inserts = [
        ('stardustLink: "Stardust weather control"', EN_BLOCK + '\n    stardustLink: "Stardust weather control"'),
        ('stardustLink: "Stardust — контроль погоды"', RU_BLOCK + '\n    stardustLink: "Stardust — контроль погоды"'),
        ('stardustLink: "Stardust — контроль погоди"', UK_BLOCK + '\n    stardustLink: "Stardust — контроль погоди"'),
        ('stardustLink: "Stardust Wetterkontrolle"', DE_BLOCK + '\n    stardustLink: "Stardust Wetterkontrolle"'),
        ('stardustLink: "Stardust 天氣控制"', ZH_BLOCK + '\n    stardustLink: "Stardust 天氣控制"'),
    ]
    for old, new in inserts:
        if old not in legal:
            # try softer match
            raise SystemExit(f"missing legal marker: {old}")
        legal = legal.replace(old, new, 1)
    lp.write_text(legal, encoding="utf-8")
    print("legal dark matter inserted")
else:
    print("legal already has darkMatterLink")
