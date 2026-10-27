import re, os, json
from collections import Counter

tt = open("src/locales/translations.ts", encoding="utf-8", errors="replace").read()
# Find en: { ... } block roughly - look for keys inside en section
m = re.search(r'\ben\s*:\s*\{', tt)
print("en_anchor", bool(m), "at", m.start() if m else None)
# keys like "foo.bar": "text"
all_keys = re.findall(r'["\']([\w.-]+)["\']\s*:\s*["\']', tt)
# also template without quotes on key? 
prefs = Counter(k.split(".")[0] for k in all_keys)
print("ALL_KEY_HITS", len(all_keys), "UNIQUE", len(set(all_keys)))
for p,c in prefs.most_common(40):
    print(f"  {c:3d} {p}")

# sample first 20 keys
print("SAMPLE", sorted(set(all_keys))[:25])

jsx_text = re.compile(r">([A-Z][^<{]{2,100})<")
str_lit = re.compile(r"(?<![\w.])([\"'])([A-Z][^\"']{2,120})\1")
skip_line = re.compile(r"^\s*(import|export|//|className|href=|from )")

def collect(path):
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    hits=set()
    for line in lines:
        if skip_line.search(line):
            continue
        if "t('" in line or 't("' in line:
            continue
        if "i18nKey" in line:
            continue
        for m in jsx_text.finditer(line):
            s=m.group(1).strip()
            if len(s)>=3: hits.add(s)
        for m in str_lit.finditer(line):
            s=m.group(2)
            if re.match(r"^(Http|/|var\(--|React|Suspense|Metadata|Next|Fragment)", s): continue
            if re.match(r"^(flex |grid |text-|bg-|border-|px-|py-|mt-|mb-|w-|h-|min-|max-|absolute|relative)", s): continue
            if re.match(r"^[A-Z0-9_./:-]{2,}$", s) and " " not in s and len(s)<40:
                # keep short title-case words like Login, Pricing
                if s.isupper() or "_" in s or "/" in s or s.endswith(".tsx"):
                    continue
            hits.add(s)
    return hits

critical = {
 "pricing":"src/app/pricing/page.tsx",
 "marketplace":"src/app/marketplace/page.tsx",
 "billing":"src/app/billing/page.tsx",
 "legal_cookies":"src/app/legal/cookies/page.tsx",
 "legal_privacy":"src/app/legal/privacy/page.tsx",
 "legal_terms":"src/app/legal/terms/page.tsx",
 "wallet_acp":"src/app/wallet/acp/page.tsx",
 "wallet_credits":"src/app/wallet/credits/page.tsx",
 "wallet_simple":"src/app/wallet/simple/page.tsx",
 "onboarding":"src/app/onboarding/page.tsx",
 "reset_password":"src/app/reset-password/page.tsx",
 "buy_acp":"src/app/buy-acp/page.tsx",
 "status":"src/app/status/page.tsx",
 "home":"src/app/HomePage.tsx",
 "login":"src/app/login/LoginForm.tsx",
 "nav":"src/components/Navigation.tsx",
 "cookie":"src/components/CookieConsent.tsx",
 "wallet_card":"src/components/WalletConnectCard.tsx",
 "seller":"src/app/dashboard/seller/page.tsx",
 "bridge_bsc":"src/app/bridge/acp-bsc/page.tsx",
 "admin_overview":"src/app/admin/overview/page.tsx",
 "admin_audit":"src/app/admin/audit/page.tsx",
 "admin_orbital":"src/app/admin/orbital-edge/page.tsx",
 "access":"src/app/access/page.tsx",
 "business":"src/app/business/page.tsx",
 "creators":"src/app/creators/page.tsx",
 "workflow_store":"src/app/workflow-store/page.tsx",
 "pay":"src/app/pay/page.tsx",
 "search":"src/app/search/page.tsx",
 "notifications":"src/app/notifications/page.tsx",
}

out = {}
for k,p in critical.items():
    if os.path.exists(p):
        h=collect(p)
        out[k]={"path":p,"count":len(h),"samples":sorted(h)[:8]}

# global unique estimate excluding already-translated-heavy files' t() lines
unique=set(); top=[]
for base in ["src/app","src/components"]:
  for dp,_,fs in os.walk(base):
    for f in fs:
      if not f.endswith('.tsx'): continue
      path=os.path.join(dp,f)
      h=collect(path)
      if h:
        unique |= h
        top.append((len(h), path.replace('\\','/')))

# pages useLanguage including bracket paths
pages_with=[]; pages_without=[]
for dp,_,fs in os.walk('src/app'):
  for f in fs:
    if f!='page.tsx': continue
    path=os.path.join(dp,f)
    txt=open(path,encoding='utf-8',errors='replace').read()
    rel=path.replace('\\','/')
    (pages_with if 'useLanguage' in txt else pages_without).append(rel)

# co-located client UI with useLanguage
other_ul=[]
for dp,_,fs in os.walk('src'):
  for f in fs:
    if not f.endswith('.tsx'): continue
    path=os.path.join(dp,f)
    if path.endswith('page.tsx'): continue
    txt=open(path,encoding='utf-8',errors='replace').read()
    if 'useLanguage' in txt:
      other_ul.append(path.replace('\\','/'))

result={
  "pages_total": len(pages_with)+len(pages_without),
  "pages_with_useLanguage": sorted(pages_with),
  "pages_with_count": len(pages_with),
  "pages_without_count": len(pages_without),
  "other_components_with_useLanguage": sorted(other_ul),
  "unique_english_groups_est": len(unique),
  "top_files": [{"n":n,"p":p} for n,p in sorted(top, reverse=True)[:50]],
  "critical": out,
  "translation_key_unique_est": len(set(all_keys)),
  "translation_prefixes": prefs.most_common(40),
}
open('tmp-i18n-hardcoded-audit.json','w',encoding='utf-8').write(json.dumps(result, indent=2, ensure_ascii=False))
print('wrote tmp-i18n-hardcoded-audit.json')
print('unique', len(unique), 'pages_with', len(pages_with), 'without', len(pages_without), 'keys', len(set(all_keys)))
