from pathlib import Path

p = Path("frontend-app/src/locales/translations.ts")
t = p.read_text(encoding="utf-8")

replacements = [
    (
        'ctaSnapshot: "Run Free Token Snapshot"',
        'ctaSnapshot: "Snapshot your token — free",\n      ctaSnapshotEyebrow: "Start free",\n      ctaProReportEyebrow: "Go deeper"',
    ),
    ('ctaProReport: "Buy Pro Risk Report"', 'ctaProReport: "Claim the Pro risk report"'),
    ('ctaPayLink: "Create Payment Link"', 'ctaPayLink: "Create your pay link"'),
    ('ctaApi: "Integrate ANCAP API"', 'ctaApi: "Unlock ANCAP API"'),
    ('wacpAddMetaMask: "Add wACP to MetaMask"', 'wacpAddMetaMask: "Slip wACP into MetaMask"'),
    (
        'ctaSnapshot: "Бесплатный снимок токена"',
        'ctaSnapshot: "Сними токен — бесплатно",\n      ctaSnapshotEyebrow: "Старт бесплатно",\n      ctaProReportEyebrow: "Глубже"',
    ),
    ('ctaProReport: "Купить Pro-отчёт о рисках"', 'ctaProReport: "Возьми Pro-отчёт"'),
    ('ctaPayLink: "Создать платёжную ссылку"', 'ctaPayLink: "Создай ссылку на оплату"'),
    ('ctaApi: "Подключить ANCAP API"', 'ctaApi: "Открой ANCAP API"'),
    ('wacpAddMetaMask: "Добавить wACP в MetaMask"', 'wacpAddMetaMask: "Добавь wACP в MetaMask"'),
    (
        'ctaSnapshot: "Безкоштовний знімок токена"',
        'ctaSnapshot: "Зніми токен — безкоштовно",\n      ctaSnapshotEyebrow: "Старт безкоштовно",\n      ctaProReportEyebrow: "Глибше"',
    ),
    ('ctaProReport: "Купити Pro-звіт про ризики"', 'ctaProReport: "Візьми Pro-звіт"'),
    ('ctaPayLink: "Створити платіжне посилання"', 'ctaPayLink: "Створи посилання на оплату"'),
    ('ctaApi: "Підключити ANCAP API"', 'ctaApi: "Відкрий ANCAP API"'),
    ('wacpAddMetaMask: "Додати wACP в MetaMask"', 'wacpAddMetaMask: "Додай wACP у MetaMask"'),
    (
        'ctaSnapshot: "Kostenlosen Token-Snapshot starten"',
        'ctaSnapshot: "Token-Snapshot — gratis",\n      ctaSnapshotEyebrow: "Gratis starten",\n      ctaProReportEyebrow: "Tiefer gehen"',
    ),
    ('ctaProReport: "Pro-Risikobericht kaufen"', 'ctaProReport: "Pro-Risikobericht holen"'),
    ('ctaPayLink: "Zahlungslink erstellen"', 'ctaPayLink: "Deinen Pay-Link erstellen"'),
    ('ctaApi: "ANCAP-API integrieren"', 'ctaApi: "ANCAP-API freischalten"'),
    ('wacpAddMetaMask: "wACP zu MetaMask hinzufügen"', 'wacpAddMetaMask: "wACP in MetaMask legen"'),
    (
        'ctaSnapshot: "執行免費代幣快照"',
        'ctaSnapshot: "免費掃描你的代幣",\n      ctaSnapshotEyebrow: "免費開始",\n      ctaProReportEyebrow: "深入一層"',
    ),
    ('ctaProReport: "購買 Pro 風險報告"', 'ctaProReport: "拿下 Pro 風險報告"'),
    ('ctaPayLink: "建立付款連結"', 'ctaPayLink: "建立你的付款連結"'),
    ('ctaApi: "整合 ANCAP API"', 'ctaApi: "解鎖 ANCAP API"'),
    ('wacpAddMetaMask: "將 wACP 加入 MetaMask"', 'wacpAddMetaMask: "把 wACP 放進 MetaMask"'),
]

for old, new in replacements:
    if old not in t:
        raise SystemExit(f"missing: {old}")
    t = t.replace(old, new, 1)

p.write_text(t, encoding="utf-8")
print("cta i18n patched")
