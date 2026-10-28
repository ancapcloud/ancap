from pathlib import Path
import re
text=Path("src/components/Navigation.tsx").read_text(encoding='utf-8')
missing=[]
for block in re.finditer(r"\{[^{}]*\}", text):
    b=block.group(0)
    if "label:" in b and "href:" in b:
        lab=re.search(r'label:\s*"([^"]+)"', b)
        if lab and "i18nKey" not in b:
            missing.append(lab.group(1))
print("missing i18nKey", missing)
for m in re.finditer(r'(Open menu|Close menu)', text):
    print("hardcoded", m.group(1))
