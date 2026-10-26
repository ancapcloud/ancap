from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]


def patch_lang_key(path: Path, lang: str, key: str, new_val: str) -> None:
    t = path.read_text(encoding="utf-8")
    # Find lang block: `  de: {` ... next `  xx:` or end
    pat = re.compile(rf"(\n  {re.escape(lang)}: \{{)([\s\S]*?)(\n  (?:[a-zA-Z\"-]+): |\n\}})", re.M)
    m = pat.search(t)
    if not m:
        print("no block", path.name, lang)
        return
    block = m.group(2)
    block2, n = re.subn(rf"(\n    {re.escape(key)}: )\"[^\"]*\"", rf'\1"{new_val}"', block, count=1)
    if n != 1:
        print("fail key", path.name, lang, key, n)
        return
    path.write_text(t[: m.start(2)] + block2 + t[m.end(2) :], encoding="utf-8")
    print("ok", path.name, lang, key, "->", new_val)


patch_lang_key(root / "src/locales/insurance.ts", "de", "wallet", "Brieftasche")
patch_lang_key(root / "src/locales/arena.ts", "de", "titleFallback", "Wettarena")

tr_path = root / "src/locales/translations.ts"
tr = tr_path.read_text(encoding="utf-8")
idx = tr.find('fauna: "Tierwelt"')
if idx < 0:
    print("Tierwelt missing")
else:
    start = tr.rfind("nav: {", 0, idx)
    end = tr.find("\n    },", idx)
    chunk = tr[start:end]
    chunk2 = chunk.replace('tech: "Tech"', 'tech: "Technik"', 1)
    if 'insurance: "' in chunk2 and "Versicherung" not in chunk2:
        chunk2 = re.sub(r'insurance: "[^"]+"', 'insurance: "Versicherung"', chunk2, count=1)
    tr_path.write_text(tr[:start] + chunk2 + tr[end:], encoding="utf-8")
    print("ok translations de nav")
