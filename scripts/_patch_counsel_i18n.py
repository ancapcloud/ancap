# -*- coding: utf-8 -*-
from pathlib import Path

p = Path("frontend-app/src/locales/translations.ts")
t = p.read_text(encoding="utf-8")

nav_repls = [
    ('      humanitarian: "Aid",\n', '      humanitarian: "Aid",\n      counsel: "Counsel",\n'),
    ('      humanitarian: "Помощь",\n', '      humanitarian: "Помощь",\n      counsel: "Юристы",\n'),
    ('      humanitarian: "Допомога",\n', '      humanitarian: "Допомога",\n      counsel: "Юристи",\n'),
    ('      humanitarian: "Hilfe",\n', '      humanitarian: "Hilfe",\n      counsel: "Recht",\n'),
    ('      humanitarian: "人道援助",\n', '      humanitarian: "人道援助",\n      counsel: "法律顧問",\n'),
]
for a, b in nav_repls:
    if a not in t:
        raise SystemExit(f"missing nav {a!r}")
    # only insert if next line isn't already counsel
    idx = t.find(a)
    after = t[idx + len(a) : idx + len(a) + 40]
    if "counsel:" not in after:
        t = t.replace(a, b, 1)

page_repls = [
    ("    agencyPage: agencyByLang.en,", "    agencyPage: agencyByLang.en,\n    counselPage: counselByLang.en,"),
    ("    agencyPage: agencyByLang.ru,", "    agencyPage: agencyByLang.ru,\n    counselPage: counselByLang.ru,"),
    ("    agencyPage: agencyByLang.uk,", "    agencyPage: agencyByLang.uk,\n    counselPage: counselByLang.uk,"),
    ("    agencyPage: agencyByLang.de,", "    agencyPage: agencyByLang.de,\n    counselPage: counselByLang.de,"),
    (
        '    agencyPage: agencyByLang["zh-Hant"],',
        '    agencyPage: agencyByLang["zh-Hant"],\n    counselPage: counselByLang["zh-Hant"],',
    ),
]
for a, b in page_repls:
    if a not in t:
        raise SystemExit(f"missing page {a!r}")
    idx = t.find(a)
    after = t[idx + len(a) : idx + len(a) + 50]
    if "counselPage:" not in after:
        t = t.replace(a, b, 1)

if "from \"./counsel\"" not in t and "from './counsel'" not in t:
    if 'import { counselByLang } from "./counsel";' not in t:
        t = t.replace(
            'import { agencyByLang } from "./agency";',
            'import { agencyByLang } from "./agency";\nimport { counselByLang } from "./counsel";',
            1,
        )

p.write_text(t, encoding="utf-8")
print("ok counselPage", t.count("counselPage:"), "nav counsel", t.count('counsel: "'))
