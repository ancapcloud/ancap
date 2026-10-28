from pathlib import Path
import re, os
from collections import defaultdict

jsx_text=re.compile(r'>([^<{]{4,160})<')
# string literals that look like UI copy: contain a space and a letter
str_lit=re.compile(r'(?<![\w.])(["\'])([^"\']*[A-Za-z][^"\']*)\1')
skip=re.compile(r'^\s*(import|export|//|/\*| \*|className|href=|src=|from |type )')

def is_copy(s):
    s=s.strip()
    if len(s)<4: return False
    if not re.search(r'[A-Za-z]', s): return False
    # exclude pure CSS-ish
    if re.search(r'(px|rem|em|%|vh|vw|rgba?\(|var\(--)', s) and not re.search(r'\s[a-z]{3,}\s', s.lower()):
        if re.match(r'^[\d\s.,%pxremvhw/#()\-]+$', s): return False
        if 'solid' in s or 'flex' in s or 'border' in s: return False
    if s.startswith('http') or s.startswith('/') or s.startswith('M') and ' ' in s and len(s)>40: return False
    if s in {'use client','use server'}: return False
    # prefer phrases with spaces OR sentence punctuation
    if ' ' in s or s.endswith(('...','?','!')):
        # filter code fragments
        if s.count('{') or s.count('`') or '=>' in s or '?.' in s: return False
        if re.match(r'^[a-z].*=', s): return False
        return True
    return False

groups=set()
by_file=[]
buckets=defaultdict(set)

def bucket(path):
    p=path.replace('\\','/').lower()
    if '/admin/' in p or 'operations-noc' in p: return 'admin'
    if any(x in p for x in ['login','register','reset-password','access','onboarding']): return 'auth'
    if any(x in p for x in ['pricing','legal','cookieconsent','homepage','navigation','marketplace','business','creators','status','buy-acp','whitepaper','/docs/']): return 'critical_public'
    return 'product' if '/app/' in p or '/components/' in p else 'other'

for base in ['src/app','src/components']:
  for dp,_,fs in os.walk(base):
    for f in fs:
      if not f.endswith('.tsx'): continue
      if f in ('LanguageProvider.tsx','LanguageSwitcher.tsx'): continue
      path=os.path.join(dp,f)
      local=set()
      for line in Path(path).read_text(encoding='utf-8', errors='replace').splitlines(keepends=True):
        if skip.search(line): continue
        if "t('" in line or 't("' in line: continue
        if 'i18nKey' in line: continue
        for m in jsx_text.finditer(line):
          s=m.group(1).strip()
          if is_copy(s): local.add(re.sub(r'\s+',' ',s))
        for m in str_lit.finditer(line):
          s=m.group(2).strip()
          if is_copy(s): local.add(re.sub(r'\s+',' ',s))
      if local:
        groups |= local
        b=bucket(path)
        buckets[b] |= local
        by_file.append((len(local), path.replace('\\','/'), b))

print('PHRASE_UNIQUE', len(groups))
for b in ['critical_public','auth','product','admin']:
    print(f'  {b}: {len(buckets[b])}')
print('TOP by file:')
for n,p,b in sorted(by_file, reverse=True)[:30]:
    print(f'  {n:3d} [{b}] {p}')

# critical file phrase counts
crit=[
'src/app/pricing/page.tsx','src/app/marketplace/page.tsx','src/app/billing/page.tsx',
'src/app/legal/cookies/page.tsx','src/app/legal/privacy/page.tsx','src/app/legal/terms/page.tsx',
'src/app/wallet/acp/page.tsx','src/app/wallet/credits/page.tsx','src/app/onboarding/page.tsx',
'src/app/reset-password/page.tsx','src/app/buy-acp/page.tsx','src/app/status/page.tsx',
'src/app/business/page.tsx','src/app/creators/page.tsx','src/app/access/page.tsx',
'src/components/Navigation.tsx','src/app/HomePage.tsx','src/app/login/LoginForm.tsx',
'src/components/CookieConsent.tsx','src/app/dashboard/seller/page.tsx',
'src/app/bridge/acp-bsc/page.tsx','src/app/admin/overview/page.tsx',
'src/app/workflow-store/page.tsx','src/app/pay/page.tsx','src/app/search/page.tsx',
]
print('CRITICAL_PHRASES')
for p in crit:
  if not os.path.exists(p): continue
  local=set()
  for line in Path(p).read_text(encoding='utf-8', errors='replace').splitlines(keepends=True):
    if skip.search(line): continue
    if "t('" in line or 't("' in line: continue
    for m in jsx_text.finditer(line):
      s=m.group(1).strip()
      if is_copy(s): local.add(s)
    for m in str_lit.finditer(line):
      s=m.group(2).strip()
      if is_copy(s): local.add(s)
  print(f'  {len(local):3d} {p}')
  for s in sorted(local)[:5]:
    print('     -', s[:90])
