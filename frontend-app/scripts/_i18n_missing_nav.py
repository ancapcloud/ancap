from __future__ import annotations

import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
nav = (root / "src/components/Navigation.tsx").read_text(encoding="utf-8")
keys = sorted(set(re.findall(r'i18nKey:\s*"([^"]+)"', nav)))

# Load audit flat keys via importing is hard; parse translations with regex for en.nav
trans = (root / "src/locales/translations.ts").read_text(encoding="utf-8")

# Extract first `nav: { ... }` block under en by scanning brace depth after "export const translations"
# Simpler: find all `key: "..."` under each locale's nav by splitting on "nav: {"

def nav_keys_for_locale_chunk(chunk: str) -> set[str]:
    # until next top-level sibling - take until we see "\n    },\n    hero:" or similar
    end = re.search(r"\n    \},\n    [a-zA-Z]", chunk)
    block = chunk[: end.start()] if end else chunk[:2000]
    return set(re.findall(r"^\s{6}([A-Za-z0-9_]+):", block, flags=re.M))


parts = trans.split("\nnav: {")
# first split piece is preamble; subsequent start with nav content — but zh-Hant etc also have nav
# Better approach: find all nav blocks
nav_blocks = re.findall(r"\n    nav: \{([\s\S]*?)\n    \},", trans)
print("nav_blocks", len(nav_blocks))
en_nav = set(re.findall(r"^\s{6}([A-Za-z0-9_]+):", nav_blocks[0], flags=re.M)) if nav_blocks else set()

missing = []
for k in keys:
    if k.startswith("nav."):
        leaf = k.split(".", 1)[1]
        if leaf not in en_nav:
            missing.append(k)
    # hero.* etc assumed present

print("referenced_nav", len([k for k in keys if k.startswith("nav.")]))
print("en_nav_count", len(en_nav))
print("MISSING_NAV", missing)
print("ALL_REFS")
for k in keys:
    print(k)

# top files
audit = json.loads((root / "tmp-i18n-hardcoded-audit.json").read_text(encoding="utf-8"))
print("TOP")
for x in audit["top_files"][:40]:
    print(f"{x['n']:4} {x['p']}")
