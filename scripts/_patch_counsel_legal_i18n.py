# -*- coding: utf-8 -*-
from pathlib import Path

LEGAL = {
    "en": """
    counselLink: "Worldwide counsel",
    hubCardCounsel: "ACP legal briefs and licensed counsel matching in any covered country — ANCAP is not a law firm.",
    counselKicker: "Legal / worldwide counsel desk",
    counselTitle: "Worldwide legal services — legal notice",
    counselIntro: "14 September 2026. ANCAP does not practice law and does not form an attorney–client relationship.",
    cn1Title: "1. Platform role",
    cn1Body: "ANCAP settles ACP for jurisdiction-match and legal intake briefs, then issues a handoff to independently licensed counsel. ANCAP is not a law firm.",
    cn2Title: "2. No attorney–client relationship with ANCAP",
    cn2Body: "Paying ACP does not create an attorney–client relationship with ANCAP, its operators, or its AI systems.",
    cn3Title: "3. Local counsel independence",
    cn3Body: "Matched counsel remain independent. They set engagement letters, fees beyond the ANCAP brief, conflicts checks, and advice under local bar rules.",
    cn4Title: "4. Worldwide coverage",
    cn4Body: "The desk aims to match counsel in any covered country or region listed on /counsel. Availability depends on partner counsel capacity and local licensing.",
    cn5Title: "5. Not legal advice from ANCAP",
    cn5Body: "Catalog copy, AI intake outputs, and workflow artifacts are literacy / intake only — not legal advice, not a court filing, and not a regulatory opinion.",
    cn6Title: "6. No outcome guarantee",
    cn6Body: "ANCAP does not guarantee visas, incorporations, judgments, tax positions, IP registrations, or regulatory approvals.",
    cn7Title: "7. Sanctions and conflicts",
    cn7Body: "Clients and matched counsel must run their own sanctions, export-control, and conflict checks. ANCAP may refuse desk service where prohibited.",
    cn8Title: "8. Confidentiality",
    cn8Body: "Do not upload privileged documents to ANCAP workflows unless your counsel instructs otherwise. Prefer hash or redacted intake where possible.",
    cn9Title: "9. Fees",
    cn9Body: "ACP prices on /counsel cover the desk brief and handoff. Ongoing counsel fees are separate and billed by the matched professional.",
    cn10Title: "10. Contact",
    cn10Body: "Questions: legal@ancap.cloud. Product: /counsel.",
""",
    "ru": """
    counselLink: "Юристы по миру",
    hubCardCounsel: "Юридические брифы ACP и подбор лицензированного юриста в любой покрытой стране — ANCAP не юрфирма.",
    counselKicker: "Юридическое / desk юристов по миру",
    counselTitle: "Юридические услуги по миру — уведомление",
    counselIntro: "14 сентября 2026. ANCAP не занимается адвокатской практикой и не создаёт отношений адвокат–клиент.",
    cn1Title: "1. Роль платформы",
    cn1Body: "ANCAP проводит расчёт в ACP за брифы подбора юрисдикции и intake, затем выдаёт handoff независимому лицензированному юристу. ANCAP не юрфирма.",
    cn2Title: "2. Нет отношений адвокат–клиент с ANCAP",
    cn2Body: "Оплата ACP не создаёт отношений адвокат–клиент с ANCAP, операторами или ИИ-системами.",
    cn3Title: "3. Независимость местного юриста",
    cn3Body: "Подобранный юрист независим. Он заключает договор, берёт дальнейшие гонорары, проверяет конфликт интересов и даёт советы по местным правилам профессии.",
    cn4Title: "4. Покрытие по миру",
    cn4Body: "Desk стремится подобрать юриста в любой покрытой стране или регионе на /counsel. Доступность зависит от партнёров и местной лицензии.",
    cn5Title: "5. Это не юрсовет от ANCAP",
    cn5Body: "Тексты каталога, ИИ-intake и артефакты workflow — только грамотность / intake, не юридический совет и не судебный документ.",
    cn6Title: "6. Без гарантии исхода",
    cn6Body: "ANCAP не гарантирует визы, регистрацию компаний, судебные решения, налоговые позиции, регистрацию IP или разрешения регуляторов.",
    cn7Title: "7. Санкции и конфликты",
    cn7Body: "Клиент и юрист сами проводят санкционный и конфликтный скрининг. ANCAP может отказать в услуге desk, где это запрещено.",
    cn8Title: "8. Конфиденциальность",
    cn8Body: "Не загружайте privileged-документы в workflow ANCAP без указания вашего юриста. Предпочитайте хеш или редacted intake.",
    cn9Title: "9. Гонорары",
    cn9Body: "Цены ACP на /counsel покрывают бриф desk и handoff. Дальнейшие гонорары юриста отдельны.",
    cn10Title: "10. Контакт",
    cn10Body: "Вопросы: legal@ancap.cloud. Продукт: /counsel.",
""",
    "uk": """
    counselLink: "Юристи світом",
    hubCardCounsel: "Юридичні брифи ACP і підбір ліцензованого юриста в будь-якій покритій країні — ANCAP не юрфірма.",
    counselKicker: "Юридичне / desk юристів світом",
    counselTitle: "Юридичні послуги світом — повідомлення",
    counselIntro: "14 вересня 2026. ANCAP не займається адвокатською практикою і не створює відносин адвокат–клієнт.",
    cn1Title: "1. Роль платформи",
    cn1Body: "ANCAP проводить розрахунок в ACP за брифи підбору юрисдикції та intake, потім видає handoff незалежному ліцензованому юристу.",
    cn2Title: "2. Немає відносин адвокат–клієнт з ANCAP",
    cn2Body: "Оплата ACP не створює відносин адвокат–клієнт з ANCAP, операторами або ШІ-системами.",
    cn3Title: "3. Незалежність місцевого юриста",
    cn3Body: "Підібраний юрист незалежний. Він укладає договір, бере подальші гонорари і дає поради за місцевими правилами професії.",
    cn4Title: "4. Покриття світом",
    cn4Body: "Desk прагне підібрати юриста в будь-якій покритій країні або регіоні на /counsel.",
    cn5Title: "5. Це не юрпорада від ANCAP",
    cn5Body: "Тексти каталогу та артефакти workflow — лише грамотність / intake, не юридична порада.",
    cn6Title: "6. Без гарантії результату",
    cn6Body: "ANCAP не гарантує візи, реєстрацію компаній, судові рішення чи податкові позиції.",
    cn7Title: "7. Санкції та конфлікти",
    cn7Body: "Клієнт і юрист самі проводять санкційний і конфліктний скринінг.",
    cn8Title: "8. Конфіденційність",
    cn8Body: "Не завантажуйте privileged-документи у workflow ANCAP без вказівки вашого юриста.",
    cn9Title: "9. Гонорари",
    cn9Body: "Ціни ACP на /counsel покривають бриф desk і handoff. Подальші гонорари юриста окремі.",
    cn10Title: "10. Контакт",
    cn10Body: "Питання: legal@ancap.cloud. Продукт: /counsel.",
""",
    "de": """
    counselLink: "Weltweite Counsel",
    hubCardCounsel: "ACP-Rechtsbriefs und Matching zu lizenziertem Counsel in jedem abgedeckten Land — ANCAP ist keine Kanzlei.",
    counselKicker: "Recht / weltweiter Counsel-Desk",
    counselTitle: "Weltweite Rechtsdienstleistungen — Rechtshinweis",
    counselIntro: "14. September 2026. ANCAP praktiziert kein Recht und begruendet kein Anwalt-Mandanten-Verhaeltnis.",
    cn1Title: "1. Plattformrolle",
    cn1Body: "ANCAP settelt ACP fuer Jurisdiktions-Match- und Intake-Briefs und stellt einen Handoff an unabhaengigen lizenzierten Counsel aus.",
    cn2Title: "2. Kein Anwalt-Mandanten-Verhaeltnis mit ANCAP",
    cn2Body: "ACP-Zahlung begruendet kein Anwalt-Mandanten-Verhaeltnis mit ANCAP, Betreibern oder KI-Systemen.",
    cn3Title: "3. Unabhaengigkeit lokaler Anwaelte",
    cn3Body: "Gematchter Counsel bleibt unabhaengig und setzt Mandatsvertraege, Folgehonorare und Beratung nach lokalen Berufsregeln.",
    cn4Title: "4. Weltweite Abdeckung",
    cn4Body: "Der Desk strebt Matching in jedem auf /counsel gelisteten Land oder Region an.",
    cn5Title: "5. Keine Rechtsberatung durch ANCAP",
    cn5Body: "Katalogtexte und Workflow-Artefakte sind Literacy/Intake — keine Rechtsberatung.",
    cn6Title: "6. Keine Ergebnisgarantie",
    cn6Body: "ANCAP garantiert keine Visa, Gesellschaftsgruendungen, Urteile oder Steuerpositionen.",
    cn7Title: "7. Sanktionen und Konflikte",
    cn7Body: "Klient und Counsel fuehren eigene Sanktions- und Konfliktpruefungen durch.",
    cn8Title: "8. Vertraulichkeit",
    cn8Body: "Laden Sie keine privileged Dokumente in ANCAP-Workflows ohne Anweisung Ihres Counsel.",
    cn9Title: "9. Honorare",
    cn9Body: "ACP-Preise auf /counsel decken Desk-Brief und Handoff. Folgehonorare sind separat.",
    cn10Title: "10. Kontakt",
    cn10Body: "Fragen: legal@ancap.cloud. Produkt: /counsel.",
""",
    "zh": """
    counselLink: "全球法律顧問",
    hubCardCounsel: "ACP 法律簡報並媒合持照律師至任何覆蓋國家 — ANCAP 不是律師事務所。",
    counselKicker: "法律／全球顧問 desk",
    counselTitle: "全球法律服務 — 法律聲明",
    counselIntro: "2026 年 9 月 14 日。ANCAP 不執業，亦不形成律師—客戶關係。",
    cn1Title: "1. 平台角色",
    cn1Body: "ANCAP 以 ACP 結算司法管轄媒合與 intake 簡報，並向獨立持照律師交接。ANCAP 不是律師事務所。",
    cn2Title: "2. 與 ANCAP 無律師—客戶關係",
    cn2Body: "支付 ACP 不會與 ANCAP、營運方或 AI 系統形成律師—客戶關係。",
    cn3Title: "3. 當地律師獨立",
    cn3Body: "媒合律師保持獨立，自行訂立委任、後續費用與依當地職業規範提供意見。",
    cn4Title: "4. 全球覆蓋",
    cn4Body: "Desk 旨在於 /counsel 所列任一覆蓋國家或地區媒合律師。",
    cn5Title: "5. 非 ANCAP 法律意見",
    cn5Body: "目錄文案與 workflow 產物僅為素養／intake，非法律意見。",
    cn6Title: "6. 無結果保證",
    cn6Body: "ANCAP 不保證簽證、公司設立、判決或稅務立場。",
    cn7Title: "7. 制裁與利益衝突",
    cn7Body: "客戶與律師須自行進行制裁與利益衝突檢查。",
    cn8Title: "8. 保密",
    cn8Body: "未經律師指示，請勿將 privileged 文件上傳至 ANCAP workflow。",
    cn9Title: "9. 費用",
    cn9Body: "/counsel 上的 ACP 價格涵蓋 desk 簡報與交接。後續律師費另行計收。",
    cn10Title: "10. 聯絡",
    cn10Body: "問題：legal@ancap.cloud。產品：/counsel。",
""",
}

path = Path("frontend-app/src/locales/legal.ts")
text = path.read_text(encoding="utf-8")
# Insert before each stardustLink (already used before) — use humanitarianLink as anchor after it
marker = "    humanitarianLink:"
parts = text.split(marker)
if len(parts) != 6:
    raise SystemExit(f"expected 6 parts got {len(parts)}")
order = ["en", "ru", "uk", "de", "zh"]
out = []
for i, lang in enumerate(order):
    seg = parts[i]
    # append counsel block at end of previous segment? Better: after humanitarian hub card area
    # Insert counsel keys right before stardustLink within each language by using smarker
    out.append(seg)
    out.append(marker)
out.append(parts[-1])
text2 = "".join(out)

# Now insert before stardustLink in each lang
smarker = "    stardustLink:"
sparts = text2.split(smarker)
if len(sparts) != 6:
    raise SystemExit(f"stardust expected 6 got {len(sparts)}")
final = []
for i, lang in enumerate(order):
    seg = sparts[i]
    if "counselLink:" not in seg[-3500:]:
        seg = seg.rstrip() + "\n" + LEGAL[lang] + "\n"
    final.append(seg)
    final.append(smarker)
final.append(sparts[-1])
path.write_text("".join(final), encoding="utf-8")
print("legal counselLink", "".join(final).count("counselLink:"))
