"""Patch nav labels: NLP-magnet copy + explore group keys (all langs)."""
from __future__ import annotations

from pathlib import Path

PATH = Path("frontend-app/src/locales/translations.ts")
text = PATH.read_text(encoding="utf-8")


def patch_nav_block(src: str, lang_marker: str, mapping: dict[str, str], extras_after: str) -> str:
    start = src.find(lang_marker)
    if start < 0:
        raise SystemExit(f"missing {lang_marker}")
    nav_start = src.find("nav: {", start)
    if nav_start < 0:
        raise SystemExit(f"nav not found for {lang_marker}")
    hero = src.find("\n    hero: {", nav_start)
    if hero < 0:
        raise SystemExit(f"hero not found after nav for {lang_marker}")
    block = src[nav_start:hero]
    for old, new in mapping.items():
        if old not in block:
            raise SystemExit(f"missing key in {lang_marker}: {old!r}")
        block = block.replace(old, new, 1)
    if extras_after and "explore:" not in block:
        needle = 'themeToDark: "'
        idx = block.rfind(needle)
        if idx < 0:
            raise SystemExit(f"themeToDark missing in {lang_marker}")
        end = block.find("\n", idx)
        line_end = block[idx:end]
        if not line_end.rstrip().endswith(","):
            block = block[:end] + "," + block[end:]
            end = block.find("\n", idx)
        block = block[:end] + extras_after + block[end:]
    return src[:nav_start] + block + src[hero:]


EN = {
    'product: "Product"': 'product: "Enter now"',
    'vision: "Vision"': 'vision: "See the path"',
    'marketplace: "Marketplace"': 'marketplace: "Open market"',
    'workflows: "Workflows"': 'workflows: "Buy a result"',
    'humanitarian: "Aid"': 'humanitarian: "Help now"',
    'counsel: "Counsel"': 'counsel: "Counsel anywhere"',
    'agency: "Agency"': 'agency: "Scale with agents"',
    'stardust: "Stardust"': 'stardust: "Own the weather"',
    'flora: "Flora"': 'flora: "Any flower"',
    'fauna: "Fauna"': 'fauna: "Living world"',
    'lunar: "Lunar"': 'lunar: "Claim the Moon"',
    'galaxy: "Galaxy"': 'galaxy: "Go farther"',
    'tech: "Tech"': 'tech: "Build tech"',
    'startups: "Startups"': 'startups: "Fund startups"',
    'insurance: "Insurance"': 'insurance: "Cover risk"',
    'arena: "Arena"': 'arena: "Win here"',
    'legal: "Legal"': 'legal: "Trust & terms"',
    'whitepaper: "Whitepaper"': 'whitepaper: "Read the thesis"',
    'acpPaper: "ACP Paper"': 'acpPaper: "ACP rail"',
    'pricing: "Pricing"': 'pricing: "Clear prices"',
    'dashboard: "Dashboard"': 'dashboard: "Your command"',
    'agents: "Agents"': 'agents: "Your agents"',
    'strategies: "Strategies"': 'strategies: "Your edge"',
    'feed: "Feed"': 'feed: "Feel the pulse"',
    'reputation: "Reputation"': 'reputation: "Prove trust"',
    'growth: "Growth"': 'growth: "Grow faster"',
}
EN_EXTRA = """,
      explore: "Discover more",
      groupSpotlight: "Start here",
      groupDesks: "Paid desks",
      groupWorlds: "Worlds & markets",
      groupBuild: "Build & earn",
      groupSystem: "Ops & proof",
      groupTrust: "Trust & papers",
      dnaBank: "DNA vault",
      perimeter: "Clear perimeter",
      cryo: "Cryo future",
      salivaRx: "Saliva Rx",
      quantumSim: "Quantum SIM",
      literary: "Own the story",
      nexus: "Meet Nexus",
      entertainment: "Feel the show",
      mail: "Connect mail",
      passport: "Your passport\""""

RU = {
    'product: "Продукт"': 'product: "Войди сейчас"',
    'vision: "Видение"': 'vision: "Увидь путь"',
    'marketplace: "Маркетплейс"': 'marketplace: "Открой рынок"',
    'workflows: "Workflow-каталог"': 'workflows: "Купи результат"',
    'humanitarian: "Помощь"': 'humanitarian: "Помоги сейчас"',
    'counsel: "Юристы"': 'counsel: "Юрист везде"',
    'agency: "Агентство"': 'agency: "Масштаб с агентами"',
    'stardust: "Stardust"': 'stardust: "Погода в руки"',
    'flora: "Флора"': 'flora: "Любой цветок"',
    'fauna: "Фауна"': 'fauna: "Живой мир"',
    'lunar: "Луна"': 'lunar: "Заяви Луну"',
    'galaxy: "Галактика"': 'galaxy: "Дальше"',
    'tech: "Технологии"': 'tech: "Создай tech"',
    'startups: "Стартапы"': 'startups: "Финансируй стартапы"',
    'insurance: "Страхование"': 'insurance: "Закрой риск"',
    'arena: "Арена"': 'arena: "Побеждай"',
    'legal: "Правовые документы"': 'legal: "Доверие и условия"',
    'whitepaper: "Whitepaper"': 'whitepaper: "Прочитай тезис"',
    'acpPaper: "Документ ACP"': 'acpPaper: "Рельс ACP"',
    'pricing: "Цены"': 'pricing: "Прозрачные цены"',
    'dashboard: "Панель"': 'dashboard: "Твой пульт"',
    'agents: "Агенты"': 'agents: "Твои агенты"',
    'strategies: "Стратегии"': 'strategies: "Твоё преимущество"',
    'feed: "Лента"': 'feed: "Почувствуй пульс"',
    'reputation: "Репутация"': 'reputation: "Докажи доверие"',
    'growth: "Рост"': 'growth: "Расти быстрее"',
}
RU_EXTRA = """,
      explore: "Ещё больше",
      groupSpotlight: "Начни здесь",
      groupDesks: "Платные столы",
      groupWorlds: "Миры и рынки",
      groupBuild: "Строй и зарабатывай",
      groupSystem: "Операции и proof",
      groupTrust: "Доверие и документы",
      dnaBank: "DNA-хранилище",
      perimeter: "Чистый периметр",
      cryo: "Cryo-будущее",
      salivaRx: "Saliva Rx",
      quantumSim: "Quantum SIM",
      literary: "Владей историей",
      nexus: "Войди в Nexus",
      entertainment: "Почувствуй шоу",
      mail: "Подключи почту",
      passport: "Твой паспорт\""""

UK = {
    'product: "Продукт"': 'product: "Увійди зараз"',
    'vision: "Бачення"': 'vision: "Побач шлях"',
    'marketplace: "Маркетплейс"': 'marketplace: "Відкрий ринок"',
    'workflows: "Workflow-каталог"': 'workflows: "Купи результат"',
    'humanitarian: "Допомога"': 'humanitarian: "Допоможи зараз"',
    'counsel: "Юристи"': 'counsel: "Юрист всюди"',
    'agency: "Агентство"': 'agency: "Масштаб з агентами"',
    'stardust: "Stardust"': 'stardust: "Погода в руки"',
    'flora: "Флора"': 'flora: "Будь-яка квітка"',
    'fauna: "Фауна"': 'fauna: "Живий світ"',
    'lunar: "Місяць"': 'lunar: "Заяви Місяць"',
    'galaxy: "Галактика"': 'galaxy: "Далі"',
    'tech: "Технології"': 'tech: "Створи tech"',
    'startups: "Стартапи"': 'startups: "Фінансуй стартапи"',
    'insurance: "Страхування"': 'insurance: "Закрий ризик"',
    'arena: "Арена"': 'arena: "Перемагай"',
    'legal: "Правові документи"': 'legal: "Довіра і умови"',
    'whitepaper: "Whitepaper"': 'whitepaper: "Прочитай тезу"',
    'acpPaper: "Документ ACP"': 'acpPaper: "Рейка ACP"',
    'pricing: "Ціни"': 'pricing: "Прозорі ціни"',
    'dashboard: "Панель"': 'dashboard: "Твій пульт"',
    'agents: "Агенти"': 'agents: "Твої агенти"',
    'strategies: "Стратегії"': 'strategies: "Твоя перевага"',
    'feed: "Стрічка"': 'feed: "Відчуй пульс"',
    'reputation: "Репутація"': 'reputation: "Доведи довіру"',
    'growth: "Зростання"': 'growth: "Зросай швидше"',
}
UK_EXTRA = """,
      explore: "Ще більше",
      groupSpotlight: "Почни тут",
      groupDesks: "Платні столи",
      groupWorlds: "Світи й ринки",
      groupBuild: "Будуй і заробляй",
      groupSystem: "Операції і proof",
      groupTrust: "Довіра і документи",
      dnaBank: "DNA-сховище",
      perimeter: "Чистий периметр",
      cryo: "Cryo-майбутнє",
      salivaRx: "Saliva Rx",
      quantumSim: "Quantum SIM",
      literary: "Володій історією",
      nexus: "Увійди в Nexus",
      entertainment: "Відчуй шоу",
      mail: "Підключи пошту",
      passport: "Твій паспорт\""""

DE = {
    'product: "Produkt"': 'product: "Jetzt eintreten"',
    'vision: "Leitbild"': 'vision: "Pfad sehen"',
    'marketplace: "Marktplatz"': 'marketplace: "Markt öffnen"',
    'workflows: "Arbeitsabläufe"': 'workflows: "Ergebnis kaufen"',
    'humanitarian: "Hilfe"': 'humanitarian: "Jetzt helfen"',
    'counsel: "Recht"': 'counsel: "Recht überall"',
    'agency: "Agentur"': 'agency: "Mit Agents skalieren"',
    'stardust: "Stardust"': 'stardust: "Wetter in der Hand"',
    'flora: "Flora"': 'flora: "Jede Blume"',
    'fauna: "Tierwelt"': 'fauna: "Lebende Welt"',
    'lunar: "Mond"': 'lunar: "Mond beanspruchen"',
    'galaxy: "Galaxie"': 'galaxy: "Weiter hinaus"',
    'tech: "Technik"': 'tech: "Tech bauen"',
    'startups: "Startups"': 'startups: "Startups finanzieren"',
    'insurance: "Versicherung"': 'insurance: "Risiko decken"',
    'arena: "Arena"': 'arena: "Hier gewinnen"',
    'legal: "Rechtliches"': 'legal: "Vertrauen & AGB"',
    'whitepaper: "Whitepaper"': 'whitepaper: "These lesen"',
    'acpPaper: "ACP-Dokument"': 'acpPaper: "ACP-Schiene"',
    'pricing: "Preise"': 'pricing: "Klare Preise"',
    'dashboard: "Übersicht"': 'dashboard: "Dein Cockpit"',
    'agents: "Agenten"': 'agents: "Deine Agents"',
    'strategies: "Strategien"': 'strategies: "Dein Edge"',
    'feed: "Aktivität"': 'feed: "Puls spüren"',
    'reputation: "Ruf"': 'reputation: "Vertrauen beweisen"',
    'growth: "Wachstum"': 'growth: "Schneller wachsen"',
}
DE_EXTRA = """,
      explore: "Mehr entdecken",
      groupSpotlight: "Hier starten",
      groupDesks: "Bezahlte Desks",
      groupWorlds: "Welten & Märkte",
      groupBuild: "Bauen & verdienen",
      groupSystem: "Ops & Proof",
      groupTrust: "Vertrauen & Papers",
      dnaBank: "DNA-Tresor",
      perimeter: "Perimeter klären",
      cryo: "Cryo-Zukunft",
      salivaRx: "Saliva Rx",
      quantumSim: "Quantum SIM",
      literary: "Geschichte besitzen",
      nexus: "Nexus betreten",
      entertainment: "Show spüren",
      mail: "Mail verbinden",
      passport: "Dein Pass\""""

ZH = {
    'product: "產品"': 'product: "立刻進入"',
    'vision: "願景"': 'vision: "看見路徑"',
    'marketplace: "市集"': 'marketplace: "打開市場"',
    'workflows: "工作流程"': 'workflows: "買下成果"',
    'humanitarian: "人道援助"': 'humanitarian: "立刻援助"',
    'counsel: "法律顧問"': 'counsel: "全球律師"',
    'agency: "代理商"': 'agency: "代理人擴張"',
    'stardust: "Stardust"': 'stardust: "掌握天氣"',
    'flora: "植物"': 'flora: "任何花朵"',
    'fauna: "動物"': 'fauna: "生命世界"',
    'lunar: "月球"': 'lunar: "宣告月球"',
    'galaxy: "銀河"': 'galaxy: "走得更遠"',
    'tech: "技術"': 'tech: "打造科技"',
    'startups: "新創"': 'startups: "資助新創"',
    'insurance: "保險"': 'insurance: "覆蓋風險"',
    'arena: "競技場"': 'arena: "在此獲勝"',
    'legal: "法律"': 'legal: "信任與條款"',
    'whitepaper: "白皮書"': 'whitepaper: "閱讀論點"',
    'acpPaper: "ACP 白皮書"': 'acpPaper: "ACP 軌道"',
    'pricing: "定價"': 'pricing: "透明價格"',
    'dashboard: "儀表板"': 'dashboard: "你的指揮台"',
    'agents: "代理人"': 'agents: "你的代理人"',
    'strategies: "策略"': 'strategies: "你的優勢"',
    'feed: "動態"': 'feed: "感受脈動"',
    'reputation: "信譽"': 'reputation: "證明信任"',
    'growth: "成長"': 'growth: "更快成長"',
}
ZH_EXTRA = """,
      explore: "探索更多",
      groupSpotlight: "從這裡開始",
      groupDesks: "付費服務台",
      groupWorlds: "世界與市場",
      groupBuild: "建造與賺取",
      groupSystem: "營運與證明",
      groupTrust: "信任與文件",
      dnaBank: "DNA 金庫",
      perimeter: "淨化邊界",
      cryo: "冷凍未來",
      salivaRx: "Saliva Rx",
      quantumSim: "Quantum SIM",
      literary: "掌握故事",
      nexus: "進入 Nexus",
      entertainment: "感受表演",
      mail: "連接郵件",
      passport: "你的護照\""""

text = text.replace("\n    stardust:", "\n      stardust:")

for lang_marker, mapping, extra in [
    ("en: {", EN, EN_EXTRA),
    ("ru: {", RU, RU_EXTRA),
    ("uk: {", UK, UK_EXTRA),
    ("de: {", DE, DE_EXTRA),
    ('"zh-Hant": {', ZH, ZH_EXTRA),
]:
    text = patch_nav_block(text, lang_marker, mapping, extra)

PATH.write_text(text, encoding="utf-8")
print("patched nav NLP i18n OK")
