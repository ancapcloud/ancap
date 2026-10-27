# -*- coding: utf-8 -*-
"""Patch legal.ts with CoinGecko market-data disclosure (all locales)."""
from __future__ import annotations

from pathlib import Path

path = Path(__file__).resolve().parents[1] / "src" / "locales" / "legal.ts"
text = path.read_text(encoding="utf-8")
if text.count("marketDataLink:") >= 5:
    print("already patched")
    raise SystemExit(0)

LOCALES = [
    {
        "hub": 'hubCardRisk: "Honest disclosure: AI outputs, ACP utility nature, bridge/wallet risks, no guaranteed returns.",',
        "r6": 'r6Body: "Rules for crypto-assets, AI, data, and payments differ by country and can change. You are responsible for your own tax and compliance obligations. Geo or KYC restrictions may apply to some payment methods.",',
        "hub_extra": (
            '    marketDataLink: "Market data",\n'
            '    hubCardMarketData: "How ANCAP uses CoinGecko and other third-party price feeds — indicative only.",\n'
            '    footerMarketData: "Market data",\n'
        ),
        "rest": (
            '    r7Title: "7. Third-party market data",\n'
            '    r7Body: "Spot prices, charts, or FX context shown on ANCAP may come from third-party providers such as CoinGecko. Those figures are indicative only: they are not a settlement price, oracle guarantee, offer to buy or sell, or investment advice. Desk quotes, bridge conversions, and ACP accounting units can differ from external market screens.",\n'
            '    riskMarketDataMore: "Full market-data disclosure:",\n'
            '    p9Title: "9. Third-party market-data providers",\n'
            '    p9Body: "To show indicative crypto and FX context, ANCAP may call third-party market-data APIs (currently CoinGecko). Those requests use ANCAP server credentials and typically do not send your account password. Provider logs may include technical metadata under their own privacy terms. We do not sell your personal data to market-data vendors.",\n'
            '    marketDataKicker: "Client disclosure",\n'
            '    marketDataTitle: "Market data and CoinGecko",\n'
            '    marketDataIntro: "This notice explains how ANCAP uses third-party market-data providers on ancap.cloud. It complements the Risk Disclosure and Privacy Notice.",\n'
            '    md1Title: "1. What we show",\n'
            "    md1Body: \"ANCAP may display indicative spot prices (for example USDT, BTC, ETH, BNB) sourced from CoinGecko via ANCAP's backend. The public API surface is GET /api/v1/market/prices. Displays may appear on transparency pages such as Reserves.\",\n"
            '    md2Title: "2. Not settlement, not advice",\n'
            '    md2Body: "CoinGecko prices are not ANCAP settlement prices. They do not bind ACP desk rates, wACP 1:1 bridge conversions, sACP collateral math, Stripe top-ups, or OTC intakes. Nothing on the site is investment, trading, or financial advice.",\n'
            '    md3Title: "3. Accuracy and availability",\n'
            '    md3Body: "Feeds can be delayed, incomplete, rate-limited, or unavailable. Cache windows and Demo/Pro plan limits apply. If the feed fails, ANCAP may hide prices or fall back to static configuration without representing a live market.",\n'
            '    md4Title: "4. Attribution",\n'
            '    md4Body: "Where market data from CoinGecko is shown, ANCAP provides attribution to CoinGecko. CoinGecko is an independent third party; ANCAP is not affiliated with CoinGecko unless separately stated.",\n'
            '    md5Title: "5. Your responsibility",\n'
            '    md5Body: "Do not rely on indicative screens for irreversible transfers. Always verify official ANCAP contract addresses, reserve proofs, and in-product quotes before sending funds.",\n'
            '    marketDataAttributionTitle: "Provider",\n'
            "    marketDataAttributionBody: \"Market data provided by CoinGecko. Review CoinGecko's own terms and privacy policy on their website.\",\n"
        ),
    },
    {
        "hub": 'hubCardRisk: "Честное раскрытие: выводы ИИ, утилитарная природа ACP, риски моста/кошелька, без гарантии доходности.",',
        "r6": 'r6Body: "Правила по криптоактивам, ИИ, данным и платежам различаются по странам. Налоги и комплаенс — ваша ответственность. Для части методов оплаты возможны geo/KYC ограничения.",',
        "hub_extra": (
            '    marketDataLink: "Рыночные данные",\n'
            '    hubCardMarketData: "Как ANCAP использует CoinGecko и другие ценовые ленты — только ориентировочно.",\n'
            '    footerMarketData: "Рыночные данные",\n'
        ),
        "rest": (
            '    r7Title: "7. Сторонние рыночные данные",\n'
            '    r7Body: "Спотовые цены, графики или FX-контекст на ANCAP могут поступать от сторонних провайдеров, в том числе CoinGecko. Это только ориентиры: не цена расчёта, не оракул-гарантия, не оферта купли/продажи и не инвестиционный совет. Котировки desk, конверсии моста и учётные единицы ACP могут отличаться от внешних экранов.",\n'
            '    riskMarketDataMore: "Полное раскрытие по рыночным данным:",\n'
            '    p9Title: "9. Провайдеры рыночных данных",\n'
            '    p9Body: "Чтобы показывать ориентировочный крипто- и FX-контекст, ANCAP может вызывать сторонние API (сейчас CoinGecko). Запросы идут с серверными ключами ANCAP и обычно не передают ваш пароль. У провайдера могут оставаться технические логи по их политике. Мы не продаём ваши персональные данные вендорам рыночных данных.",\n'
            '    marketDataKicker: "Раскрытие для клиентов",\n'
            '    marketDataTitle: "Рыночные данные и CoinGecko",\n'
            '    marketDataIntro: "Как ANCAP использует сторонние рыночные данные на ancap.cloud. Дополняет раскрытие рисков и уведомление о конфиденциальности.",\n'
            '    md1Title: "1. Что мы показываем",\n'
            '    md1Body: "ANCAP может показывать ориентировочные спотовые цены (например USDT, BTC, ETH, BNB) из CoinGecko через backend. Публичный API: GET /api/v1/market/prices. Блоки могут быть на страницах прозрачности, например Reserves.",\n'
            '    md2Title: "2. Не расчёт и не совет",\n'
            '    md2Body: "Цены CoinGecko не являются ценами расчёта ANCAP. Они не определяют desk-ставки ACP, 1:1 мост wACP, коллатераль sACP, Stripe top-up или OTC. Это не инвестиционный и не торговый совет.",\n'
            '    md3Title: "3. Точность и доступность",\n'
            '    md3Body: "Ленты могут запаздывать, быть неполными, ограничиваться rate limit или быть недоступны. Действуют кэш и лимиты Demo/Pro. При сбое ANCAP может скрыть цены или использовать статичный конфиг без заявления о живом рынке.",\n'
            '    md4Title: "4. Атрибуция",\n'
            '    md4Body: "Там, где показаны данные CoinGecko, ANCAP указывает источник. CoinGecko — независимая сторона; ANCAP не аффилирован с CoinGecko, если отдельно не указано иное.",\n'
            '    md5Title: "5. Ваша ответственность",\n'
            '    md5Body: "Не опирайтесь на ориентировочные экраны для необратимых переводов. Перед отправкой средств проверяйте официальные адреса контрактов ANCAP, reserve proof и котировки в продукте.",\n'
            '    marketDataAttributionTitle: "Провайдер",\n'
            '    marketDataAttributionBody: "Рыночные данные предоставлены CoinGecko. Ознакомьтесь с условиями и политикой конфиденциальности CoinGecko на их сайте.",\n'
        ),
    },
    {
        "hub": 'hubCardRisk: "Чесне розкриття: результати ШІ, утилітарна природа ACP, ризики мосту/гаманця, без гарантії дохідності.",',
        "r6": 'r6Body: "Правила відрізняються за країнами. Податки — ваша відповідальність.",',
        "hub_extra": (
            '    marketDataLink: "Ринкові дані",\n'
            '    hubCardMarketData: "Як ANCAP використовує CoinGecko та інші цінові стрічки — лише орієнтовно.",\n'
            '    footerMarketData: "Ринкові дані",\n'
        ),
        "rest": (
            '    r7Title: "7. Сторонні ринкові дані",\n'
            '    r7Body: "Спотові ціни або FX-контекст на ANCAP можуть надходити від CoinGecko. Це лише орієнтири, не ціна розрахунку і не інвестиційна порада.",\n'
            '    riskMarketDataMore: "Повне розкриття щодо ринкових даних:",\n'
            '    p9Title: "9. Провайдери ринкових даних",\n'
            '    p9Body: "ANCAP може викликати CoinGecko API для орієнтовних котирувань. Запити йдуть із серверними ключами і зазвичай без вашого пароля.",\n'
            '    marketDataKicker: "Розкриття для клієнтів",\n'
            '    marketDataTitle: "Ринкові дані та CoinGecko",\n'
            '    marketDataIntro: "Як ANCAP використовує сторонні ринкові дані на ancap.cloud.",\n'
            '    md1Title: "1. Що ми показуємо",\n'
            '    md1Body: "Орієнтовні спотові ціни (USDT, BTC, ETH, BNB). API: GET /api/v1/market/prices.",\n'
            '    md2Title: "2. Не розрахунок і не порада",\n'
            '    md2Body: "Ціни CoinGecko не є цінами розрахунку ANCAP.",\n'
            '    md3Title: "3. Точність і доступність",\n'
            '    md3Body: "Стрічки можуть запізнюватися або бути недоступні.",\n'
            '    md4Title: "4. Атрибуція",\n'
            '    md4Body: "ANCAP вказує CoinGecko як джерело.",\n'
            '    md5Title: "5. Ваша відповідальність",\n'
            '    md5Body: "Не покладайтеся на орієнтовні екрани для незворотних переказів.",\n'
            '    marketDataAttributionTitle: "Провайдер",\n'
            '    marketDataAttributionBody: "Ринкові дані надано CoinGecko.",\n'
        ),
    },
    {
        "hub": 'hubCardRisk: "Offene Hinweise: KI-Ausgaben, Utility-Charakter von ACP, Bridge-/Wallet-Risiken, keine Renditegarantie.",',
        "r6": 'r6Body: "Regeln unterscheiden sich nach Land. Steuern liegen bei Ihnen.",',
        "hub_extra": (
            '    marketDataLink: "Marktdaten",\n'
            '    hubCardMarketData: "Wie ANCAP CoinGecko und andere Kursfeeds nutzt — nur indikativ.",\n'
            '    footerMarketData: "Marktdaten",\n'
        ),
        "rest": (
            '    r7Title: "7. Drittanbieter-Marktdaten",\n'
            '    r7Body: "Spotpreise auf ANCAP können von CoinGecko stammen und sind nur indikativ — kein Settlement-Preis und keine Anlageberatung.",\n'
            '    riskMarketDataMore: "Vollständige Marktdaten-Offenlegung:",\n'
            '    p9Title: "9. Marktdaten-Anbieter",\n'
            '    p9Body: "ANCAP kann CoinGecko-APIs für indikative Kurse nutzen. Anfragen verwenden Server-Credentials.",\n'
            '    marketDataKicker: "Kundenhinweis",\n'
            '    marketDataTitle: "Marktdaten und CoinGecko",\n'
            '    marketDataIntro: "Wie ANCAP Drittanbieter-Marktdaten auf ancap.cloud nutzt.",\n'
            '    md1Title: "1. Was wir zeigen",\n'
            '    md1Body: "Indikative Spotpreise (USDT, BTC, ETH, BNB). API: GET /api/v1/market/prices.",\n'
            '    md2Title: "2. Kein Settlement, keine Beratung",\n'
            '    md2Body: "CoinGecko-Preise sind keine ANCAP-Settlement-Preise.",\n'
            '    md3Title: "3. Genauigkeit und Verfügbarkeit",\n'
            '    md3Body: "Feeds können verzögert oder ausfallen.",\n'
            '    md4Title: "4. Attribution",\n'
            '    md4Body: "ANCAP nennt CoinGecko als Quelle.",\n'
            '    md5Title: "5. Ihre Verantwortung",\n'
            '    md5Body: "Verlassen Sie sich nicht auf indikative Screens für irreversible Transfers.",\n'
            '    marketDataAttributionTitle: "Anbieter",\n'
            '    marketDataAttributionBody: "Marktdaten von CoinGecko.",\n'
        ),
    },
    {
        "hub": 'hubCardRisk: "誠實揭露：AI 輸出、ACP 效用性質、橋接／錢包風險、無保證報酬。",',
        "r6": 'r6Body: "各國規則不同。稅務由您自行負責。",',
        "hub_extra": (
            '    marketDataLink: "市場數據",\n'
            '    hubCardMarketData: "ANCAP 如何使用 CoinGecko 等第三方報價——僅供參考。",\n'
            '    footerMarketData: "市場數據",\n'
        ),
        "rest": (
            '    r7Title: "7. 第三方市場數據",\n'
            '    r7Body: "ANCAP 上顯示的現貨價格可能來自 CoinGecko，僅供參考，非結算價亦非投資建議。",\n'
            '    riskMarketDataMore: "完整市場數據揭露：",\n'
            '    p9Title: "9. 市場數據供應商",\n'
            '    p9Body: "ANCAP 可能呼叫 CoinGecko API 顯示參考行情；請求使用伺服器憑證。",\n'
            '    marketDataKicker: "客戶揭露",\n'
            '    marketDataTitle: "市場數據與 CoinGecko",\n'
            '    marketDataIntro: "說明 ANCAP 如何使用第三方市場數據。",\n'
            '    md1Title: "1. 我們顯示什麼",\n'
            '    md1Body: "參考現貨價（USDT、BTC、ETH、BNB）。API：GET /api/v1/market/prices。",\n'
            '    md2Title: "2. 非結算、非建議",\n'
            '    md2Body: "CoinGecko 價格不是 ANCAP 結算價。",\n'
            '    md3Title: "3. 準確性與可用性",\n'
            '    md3Body: "資料源可能延遲或中斷。",\n'
            '    md4Title: "4. 出處標示",\n'
            '    md4Body: "顯示時標示 CoinGecko 來源。",\n'
            '    md5Title: "5. 您的責任",\n'
            '    md5Body: "請勿依賴參考畫面進行不可逆轉帳。",\n'
            '    marketDataAttributionTitle: "供應商",\n'
            '    marketDataAttributionBody: "市場數據由 CoinGecko 提供。",\n'
        ),
    },
]

for loc in LOCALES:
    a = loc["hub"] + "\n    hubCardRefunds:"
    b = loc["hub"] + "\n" + loc["hub_extra"] + "    hubCardRefunds:"
    if a not in text:
        raise SystemExit(f"hub missing: {loc['hub'][:40]}")
    text = text.replace(a, b, 1)
    c = loc["r6"] + "\n    refundsKicker:"
    d = loc["r6"] + "\n" + loc["rest"] + "    refundsKicker:"
    if c not in text:
        raise SystemExit(f"r6 missing: {loc['r6'][:40]}")
    text = text.replace(c, d, 1)

path.write_text(text, encoding="utf-8")
print("ok", path, "marketDataLink=", text.count("marketDataLink:"))
