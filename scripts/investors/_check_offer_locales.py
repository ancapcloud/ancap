# -*- coding: utf-8 -*-
import re
from pathlib import Path

t = Path("frontend-app/src/lib/projectOffersCopy.ts").read_text(encoding="utf-8")


def parse(name: str) -> dict:
    if name == "zhHant":
        block = t.split("const zhHant: OfferCopyMap = {", 1)[1].split("\n};\n\nexport", 1)[0]
    else:
        block = t.split(f"const {name}: OfferCopyMap = {{", 1)[1]
        block = re.split(r"\n};\n\n(?:const|export)", block, 1)[0]
    out = {}
    for m in re.finditer(r'"(/(?:[^"]+))"\s*:\s*\{(.*?)\n  \},?', block, re.S):
        href = m.group(1)
        body = m.group(2)
        fields = {}
        for fm in re.finditer(r'(\w+):\s*"((?:\\.|[^"\\])*)"', body):
            fields[fm.group(1)] = fm.group(2)
        out[href] = fields
    return out


en, de, zh, uk, ru = parse("en"), parse("de"), parse("zhHant"), parse("uk"), parse("ru")
print("same_de_as_en", sum(1 for h in en if de[h] == en[h]), "of", len(en))
print("same_zh_as_en", sum(1 for h in en if zh[h] == en[h]), "of", len(en))
print("uk_diff_from_en", sum(1 for h in en if uk[h] != en[h]))
print("ru_diff_from_en", sum(1 for h in en if ru[h] != en[h]))
print("markets_de", de["/markets"]["buyer"])
