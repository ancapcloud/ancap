# -*- coding: utf-8 -*-
"""Patch legal.ts + translations nav for StardustSRT weather-control desk."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGAL = ROOT / "frontend-app" / "src" / "locales" / "legal.ts"
TRANS = ROOT / "frontend-app" / "src" / "locales" / "translations.ts"

LEGAL_BLOCKS = {
    "en": '''
    stardustLink: "Stardust weather control",
    hubCardStardust:
      "ACP-settled worldwide weather-control and disaster-monitoring partner literacy. Not a live geoengineering console, not official meteorological warnings, not a guaranteed weather outcome.",
    stardustKicker: "Legal / weather control / earth monitoring",
    stardustTitle: "StardustSRT weather control — licensed partner rail",
    stardustIntro:
      "How ANCAP frames the Stardust desk as of 13 September 2026. These pages sell ACP-settled partner briefs for earth monitoring and weather-control architecture literacy, not a live weather remote control.",
    sd1Title: "1. Platform role",
    sd1Body:
      "ANCAP provides ACP settlement, consult briefs, and licensed-partner matching. ANCAP does not operate a geoengineering fleet, does not unilaterally modify weather worldwide, and does not replace national meteorological services.",
    sd2Title: "2. Not affiliated with StardustSRT by default",
    sd2Body:
      "Public StardustSRT artwork and stardustsrt.com are literacy references. ANCAP is not affiliated with StardustSRT unless a separate partner contract is executed.",
    sd3Title: "3. Not a live Weather Control console",
    sd3Body:
      "Rainfall enhancement, storm dissipation, temperature regulation, and snow management toggles on /stardust are product literacy UI. Buying ACP does not give operators a satellite kill-switch for storms.",
    sd4Title: "4. Forbidden outcome claims",
    sd4Body:
      "ANCAP does not guarantee better rainfall, weaker storms, stable temperatures, healthier climate outcomes, or earlier disaster alerts than official agencies.",
    sd5Title: "5. Not official meteorological warnings",
    sd5Body:
      "Extreme weather and disaster modules are partner coordination literacy. For critical decisions use AccuWeather, national weather authorities, or civil-protection channels. Widget weather remains indicative (/legal/market-data).",
    sd6Title: "6. Licensed partners only",
    sd6Body:
      "Any sensing, cloud-seeding, or weather ops remain partner acts after screening under environmental, aviation, and telecom law. Users must not treat these pages as DIY geoengineering instructions.",
    sd7Title: "7. Infographic literacy, not an ops SOP",
    sd7Body:
      "Satellite beams, tectonic overlays, and control panels are architecture literacy. ANCAP does not publish weaponized weather SOPs or classified sensing recipes.",
    sd8Title: "8. Insurance relationship",
    sd8Body:
      "Parametric ACP cover class weather_control on /insurance may reference Stardust intakes. It is not meteorological insurance, not a geoengineering warranty, and not a storm-dissipation guarantee.",
    sd9Title: "9. Payments",
    sd9Body:
      "ACP buys partner briefs from 18,000 ACP (extreme weather monitor) to 58,000 ACP (global weather-control brief) and a 45,000 ACP / month subscription — not hardware title and not a refundable weather outcome. Refunds follow /legal/refunds.",
    sd10Title: "10. Contact",
    sd10Body:
      "Legal notices: legal@ancap.cloud. Product: /stardust. Insurance: /insurance. Related: /legal/market-data, /legal/terms, /legal/risk.",
    footerStardust: "Stardust weather control",
''',
    "ru": '''
    stardustLink: "Stardust — контроль погоды",
    hubCardStardust:
      "ACP-брифы партнёра по мировому контролю погоды и мониторингу катастроф. Не живая консоль геоинженерии, не официальные метеопредупреждения, не гарантия исхода.",
    stardustKicker: "Юридическое / контроль погоды / мониторинг Земли",
    stardustTitle: "StardustSRT — контроль погоды, лицензированный партнёрский рейл",
    stardustIntro:
      "Как ANCAP оформляет desk Stardust на 13 сентября 2026. Страницы продают ACP-брифы грамотности, а не пульт удалённого управления погодой.",
    sd1Title: "1. Роль платформы",
    sd1Body:
      "ANCAP даёт расчёт ACP, брифы и матч партнёра. ANCAP не ведёт флот геоинженерии и не заменяет национальные метеослужбы.",
    sd2Title: "2. Нет аффилиации со StardustSRT по умолчанию",
    sd2Body:
      "Публичные материалы StardustSRT — справочная грамотность. Аффилиация только при отдельном договоре.",
    sd3Title: "3. Не живая консоль Weather Control",
    sd3Body:
      "Переключатели на /stardust — UI грамотности. Покупка ACP не даёт kill-switch для штормов.",
    sd4Title: "4. Запрещённые обещания исхода",
    sd4Body:
      "ANCAP не гарантирует дождь, ослабление штормов, стабильную температуру или более ранние тревоги, чем у официальных служб.",
    sd5Title: "5. Не официальные метеопредупреждения",
    sd5Body:
      "Для критических решений — AccuWeather, нацметеослужба или ГО. Виджет погоды — ориентир (/legal/market-data).",
    sd6Title: "6. Только лицензированные партнёры",
    sd6Body:
      "Сенсоры, засев облаков и погодные операции — акт партнёра после скрининга.",
    sd7Title: "7. Инфографика — не боевой SOP",
    sd7Body:
      "Спутники и панели — архитектурная грамотность, не инструкция по оружию погоды.",
    sd8Title: "8. Страховка",
    sd8Body:
      "Класс weather_control на /insurance может ссылаться на интейки Stardust. Это не гарантия рассеивания шторма.",
    sd9Title: "9. Платежи",
    sd9Body:
      "ACP от 18 000 (мониторинг) до 58 000 (глобальный контроль) и подписка 45 000 / месяц. Возвраты — /legal/refunds.",
    sd10Title: "10. Контакты",
    sd10Body:
      "legal@ancap.cloud · /stardust · /insurance · /legal/market-data",
    footerStardust: "Stardust — контроль погоды",
''',
    "uk": '''
    stardustLink: "Stardust — контроль погоди",
    hubCardStardust:
      "ACP-брифи партнера з світового контролю погоди. Не жива консоль геоінженерії і не гарантія результату.",
    stardustKicker: "Юридичне / контроль погоди",
    stardustTitle: "StardustSRT — контроль погоди, ліцензований партнерський рейл",
    stardustIntro:
      "Як ANCAP оформлює desk Stardust станом на 13 вересня 2026.",
    sd1Title: "1. Роль платформи",
    sd1Body: "ANCAP дає розрахунок ACP і матч партнера. Не замінює нацметеослужби.",
    sd2Title: "2. Немає афіліації зі StardustSRT за замовчуванням",
    sd2Body: "Публічні матеріали — грамотність. Афіліація лише за окремим договором.",
    sd3Title: "3. Не жива консоль Weather Control",
    sd3Body: "Перемикачі на /stardust — UI грамотності.",
    sd4Title: "4. Заборонені обіцянки",
    sd4Body: "ANCAP не гарантує дощ, слабші шторми чи кліматичний результат.",
    sd5Title: "5. Не офіційні метеопопередження",
    sd5Body: "Для критичних рішень — AccuWeather або нацслужба.",
    sd6Title: "6. Лише ліцензовані партнери",
    sd6Body: "Операції з погодою — акт партнера після скринінгу.",
    sd7Title: "7. Інфографіка — не бойовий SOP",
    sd7Body: "Архітектурна грамотність, не інструкція.",
    sd8Title: "8. Страхування",
    sd8Body: "Клас weather_control на /insurance може посилатися на інтейки Stardust.",
    sd9Title: "9. Платежі",
    sd9Body: "ACP від 18 000 до 58 000 і підписка 45 000 / місяць.",
    sd10Title: "10. Контакти",
    sd10Body: "legal@ancap.cloud · /stardust · /insurance",
    footerStardust: "Stardust — контроль погоди",
''',
    "de": '''
    stardustLink: "Stardust Wetterkontrolle",
    hubCardStardust:
      "ACP-Partnerbriefs für weltweite Wetterkontrolle. Keine Live-Geoengineering-Konsole, keine Erfolgsgarantie.",
    stardustKicker: "Recht / Wetterkontrolle / Erdmonitoring",
    stardustTitle: "StardustSRT Wetterkontrolle — lizenzierte Partnerschiene",
    stardustIntro:
      "Wie ANCAP den Stardust-Desk zum 13. September 2026 rahmt.",
    sd1Title: "1. Plattformrolle",
    sd1Body: "ANCAP stellt ACP-Settlement und Partner-Matching bereit — keine nationale Wetterbehörde.",
    sd2Title: "2. Keine Default-Affiliation mit StardustSRT",
    sd2Body: "Öffentliche StardustSRT-Materialien sind Literalität; Affiliation nur per Vertrag.",
    sd3Title: "3. Keine Live-Weather-Control-Konsole",
    sd3Body: "Schalter auf /stardust sind Produktliteralität.",
    sd4Title: "4. Verbotene Outcome-Claims",
    sd4Body: "Keine Garantie für Regen, schwächere Stürme oder Klimaoutcomes.",
    sd5Title: "5. Keine offiziellen Wetterwarnungen",
    sd5Body: "Kritische Entscheidungen: AccuWeather oder nationale Behörden.",
    sd6Title: "6. Nur lizenzierte Partner",
    sd6Body: "Wetteroperationen sind Partnerakte nach Screening.",
    sd7Title: "7. Infografik, kein Ops-SOP",
    sd7Body: "Architekturliteralität, keine Waffen-SOPs.",
    sd8Title: "8. Versicherung",
    sd8Body: "Coverage-Klasse weather_control auf /insurance kann Stardust-Intakes referenzieren.",
    sd9Title: "9. Zahlungen",
    sd9Body: "ACP von 18.000 bis 58.000 und Abo 45.000 / Monat.",
    sd10Title: "10. Kontakt",
    sd10Body: "legal@ancap.cloud · /stardust · /insurance",
    footerStardust: "Stardust Wetterkontrolle",
''',
    "zh": '''
    stardustLink: "Stardust 天氣控制",
    hubCardStardust:
      "ACP 全球天氣控制／災害監測夥伴素養。非即時地球工程控制台，非結果保證。",
    stardustKicker: "法律／天氣控制／地球監測",
    stardustTitle: "StardustSRT 天氣控制 — 持照夥伴軌道",
    stardustIntro:
      "ANCAP 於 2026 年 9 月 13 日對 Stardust 桌面的定位。",
    sd1Title: "1. 平台角色",
    sd1Body: "ANCAP 提供 ACP 結算與夥伴配對，不取代國家氣象服務。",
    sd2Title: "2. 預設未與 StardustSRT 加盟",
    sd2Body: "公開素材為素養參考；加盟須另訂契約。",
    sd3Title: "3. 非即時 Weather Control 控制台",
    sd3Body: "/stardust 開關為產品素養 UI。",
    sd4Title: "4. 禁止結果主張",
    sd4Body: "ANCAP 不保證降雨、減弱風暴或氣候結果。",
    sd5Title: "5. 非官方氣象警報",
    sd5Body: "關鍵決策請用 AccuWeather 或國家氣象單位。",
    sd6Title: "6. 僅限持照夥伴",
    sd6Body: "天氣作業為夥伴行為，須經篩檢。",
    sd7Title: "7. 資訊圖非作戰 SOP",
    sd7Body: "架構素養，非武器化天氣指令。",
    sd8Title: "8. 保險關係",
    sd8Body: "/insurance 的 weather_control 可對應 Stardust 進件。",
    sd9Title: "9. 付款",
    sd9Body: "ACP 自 18,000 至 58,000，訂閱每月 45,000。",
    sd10Title: "10. 聯絡",
    sd10Body: "legal@ancap.cloud · /stardust · /insurance",
    footerStardust: "Stardust 天氣控制",
''',
}


def patch_legal() -> None:
    text = LEGAL.read_text(encoding="utf-8")
    if "stardustLink" in text:
        print("legal already patched")
        return
    langs = ["en", "ru", "uk", "de", "zh"]
    needle = "footerInstallationProject:"
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
        raise SystemExit(f"expected 5 footerInstallationProject, got {len(positions)}")
    for lang, pos in zip(reversed(langs), reversed(positions)):
        text = text[:pos] + "\n" + LEGAL_BLOCKS[lang].lstrip("\n") + text[pos:]
    LEGAL.write_text(text, encoding="utf-8")
    print("legal ok")


def patch_nav() -> None:
    text = TRANS.read_text(encoding="utf-8")
    if "stardust:" in text and "nav" in text[text.find("stardust:") - 40 : text.find("stardust:") + 20]:
        # fragile — just insert near quantum if missing as nav.stardust
        pass
    if 'stardust: "Stardust"' in text or "nav.stardust" in text:
        # check en nav block
        if 'stardust: "Stardust"' in text:
            print("nav already patched")
            return
    # Insert after quantumSim or lunar in each language nav object
    # Find nav blocks - look for pattern after lunar or quantumSim keys
    markers = [
        ('    lunar: "Lunar",\n', '    lunar: "Lunar",\n    stardust: "Stardust",\n'),
        ('    lunar: "Луна",\n', '    lunar: "Луна",\n    stardust: "Stardust",\n'),
        ('    lunar: "Місяць",\n', '    lunar: "Місяць",\n    stardust: "Stardust",\n'),
        ('    lunar: "Mond",\n', '    lunar: "Mond",\n    stardust: "Stardust",\n'),
        ('    lunar: "月球",\n', '    lunar: "月球",\n    stardust: "Stardust",\n'),
    ]
    if 'stardust: "Stardust"' in text:
        print("nav already has stardust")
        return
    changed = 0
    for old, new in markers:
        if old in text:
            text = text.replace(old, new, 1)
            changed += 1
    if changed < 1:
        # fallback: insert after first fauna key occurrence sets
        raise SystemExit("could not patch nav.stardust")
    TRANS.write_text(text, encoding="utf-8")
    print(f"nav ok ({changed} langs)")


if __name__ == "__main__":
    patch_legal()
    patch_nav()
