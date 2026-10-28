from pathlib import Path
import re, os
from collections import Counter

tt = Path("src/locales/translations.ts").read_text(encoding='utf-8', errors='replace')
all_keys = re.findall(r'^\s*["\']([\w.-]+)["\']\s*:', tt, re.M)
prefs = Counter(k.split(".")[0] for k in all_keys)
print("EN_KEYS", len(set(all_keys)))
print("PREFIXES")
for p, c in prefs.most_common(50):
    print(f"  {c:3d} {p}")

pages = []
for dirpath, _, files in os.walk("src/app"):
    for f in files:
        if f == "page.tsx":
            pages.append(os.path.join(dirpath, f))
with_ul, without = [], []
for p in pages:
    txt = Path(p).read_text(encoding='utf-8', errors='replace')
    (with_ul if "useLanguage" in txt else without).append(p.replace("\\", "/"))
print("PAGES", len(pages), "WITH", len(with_ul), "WITHOUT", len(without))
print("WITH_LIST")
for p in sorted(with_ul):
    print(" ", p)

jsx_text = re.compile(r">([A-Z][^<{]{2,100})<")
str_lit = re.compile(r"(?<![\w.])([\"'])([A-Z][^\"']{2,120})\1")
skip_line = re.compile(r"^\s*(import|export|//|className|href=|from )")

def score(path):
    lines = Path(path).read_text(encoding='utf-8', errors='replace').splitlines()
    hits = set()
    for line in lines:
        if skip_line.search(line):
            continue
        if "t('" in line or 't("' in line:
            continue
        if "i18nKey" in line:
            continue
        for m in jsx_text.finditer(line):
            s = m.group(1).strip()
            if len(s) >= 3:
                hits.add(s)
        for m in str_lit.finditer(line):
            s = m.group(2)
            if re.match(r"^(Http|/|var\(--|React|Suspense|Metadata|Next)", s):
                continue
            if re.match(r"^(flex |grid |text-|bg-|border-|px-|py-|mt-|mb-|w-|h-|min-|max-)", s):
                continue
            hits.add(s)
    return len(hits), sorted(hits)[:6]

critical = [
 "src/app/pricing/page.tsx","src/app/marketplace/page.tsx","src/app/billing/page.tsx",
 "src/app/legal/cookies/page.tsx","src/app/legal/privacy/page.tsx","src/app/legal/terms/page.tsx",
 "src/app/wallet/acp/page.tsx","src/app/wallet/credits/page.tsx","src/app/wallet/simple/page.tsx",
 "src/app/onboarding/page.tsx","src/app/reset-password/page.tsx","src/app/buy-acp/page.tsx",
 "src/app/status/page.tsx","src/app/business/page.tsx","src/app/creators/page.tsx",
 "src/app/HomePage.tsx","src/app/login/LoginForm.tsx","src/components/Navigation.tsx",
 "src/components/CookieConsent.tsx","src/components/WalletConnectCard.tsx",
 "src/app/access/page.tsx","src/app/register/page.tsx","src/app/dashboard/seller/page.tsx",
 "src/app/bridge/page.tsx","src/app/bridge/acp-bsc/page.tsx","src/app/whitepaper/page.tsx",
 "src/app/docs/wacp/page.tsx","src/app/admin/overview/page.tsx","src/app/admin/audit/page.tsx",
 "src/app/admin/orbital-edge/page.tsx",
]
print("CRITICAL_SCORES")
for p in critical:
    if os.path.exists(p):
        n, samples = score(p)
        print(f"  {n:3d}  {p}  :: {samples}")

# broader estimate across all app+components tsx without useLanguage
unique = set()
files_hit = []
for base in ["src/app", "src/components"]:
    for dirpath, _, files in os.walk(base):
        for f in files:
            if not f.endswith(".tsx"):
                continue
            path = os.path.join(dirpath, f)
            txt = Path(path).read_text(encoding='utf-8', errors='replace')
            if "useLanguage" in txt and path.endswith(("HomePage.tsx","Navigation.tsx","CookieConsent.tsx","LoginForm.tsx","LanguageSwitcher.tsx","WalletConnectCard.tsx","HomeMcpSection.tsx")):
                # still count leftover
                pass
            n, hits = score(path)[0], None
            # recompute set
            lines = txt.splitlines()
            local=set()
            for line in lines:
                if skip_line.search(line):
                    continue
                if "t('" in line or 't("' in line:
                    continue
                if "i18nKey" in line:
                    continue
                for m in jsx_text.finditer(line):
                    s=m.group(1).strip()
                    if len(s)>=3: local.add(s)
                for m in str_lit.finditer(line):
                    s=m.group(2)
                    if re.match(r"^(Http|/|var\(--|React|Suspense|Metadata|Next)", s): continue
                    if re.match(r"^(flex |grid |text-|bg-|border-|px-|py-|mt-|mb-|w-|h-|min-|max-)", s): continue
                    local.add(s)
            if local:
                unique |= local
                files_hit.append((len(local), path.replace("\\","/")))

print("UNIQUE_GROUPS_EST", len(unique))
print("TOP_FILES")
for n,p in sorted(files_hit, reverse=True)[:40]:
    print(f"  {n:3d} {p}")
