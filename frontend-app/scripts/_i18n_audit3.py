from pathlib import Path
import re, os, json
from collections import Counter

def flatten(obj, prefix=""):
    out=[]
    if isinstance(obj, dict):
        for k,v in obj.items():
            p=f"{prefix}.{k}" if prefix else k
            out.extend(flatten(v,p))
    elif isinstance(obj, str):
        out.append((prefix, obj))
    return out

text=Path('src/locales/translations.ts').read_text(encoding='utf-8')
idx=text.find('en: {')
i=idx+len('en:')
while text[i]!='{': i+=1
start=i
depth=0
for j in range(start,len(text)):
    c=text[j]
    if c=='{': depth+=1
    elif c=='}':
        depth-=1
        if depth==0:
            end=j+1
            break
en_block=text[start:end]

def ts_obj_to_dict(s):
    s2=re.sub(r',(\s*[}\]])', r'\1', s)
    s2=re.sub(r'([\{,]\s*)([A-Za-z_][\w-]*)(\s*:)', r'\1"\2"\3', s2)
    return json.loads(s2)

try:
    en=ts_obj_to_dict(en_block)
    flat=flatten(en)
    print('LEAF', len(flat))
    prefs=Counter(k.split('.')[0] for k,_ in flat)
    for p,c in prefs.most_common(40):
        print(f'  {c:3d} {p}')
    for name in ['pricing','legal','wallet','billing','marketplace','cookies','auth','nav','hero','homePage']:
        print(f'HAS {name}', any(k==name or k.startswith(name+'.') for k,_ in flat))
except Exception as e:
    print('parse_fail', type(e).__name__, e)
    leaves=re.findall(r':\s*"((?:\\.|[^"\\])*)"', en_block)
    print('LEAF_FALLBACK', len(leaves))

jsx_text=re.compile(r'>([^<{]{3,120})<')
str_lit=re.compile(r'(?<![\w.])(["\'])([^"\']{3,160})\1')
skip=re.compile(r'^\s*(import|export|//|/\*|className|href=|src=|from )')

def is_ui(s):
    s=s.strip()
    if not s or s.startswith('{') or s.startswith('$'): return False
    if s.startswith('http') or s.startswith('/') or s.startswith('var(--'): return False
    if re.match(r'^(flex|grid|text-|bg-|border-|px-|py-|mt-|mb-|w-|h-|min-|max-|absolute|relative|fixed|hidden|block|inline|gap-|rounded|shadow|opacity|transition|animate|cursor|select|overflow|z-|top-|left-|right-|bottom-|sm:|md:|lg:)', s): return False
    if not re.search(r'[A-Za-z]', s): return False
    if ' ' in s or s.endswith(('...','.','!','?')): return True
    if re.match(r'^[A-Z][a-zA-Z0-9+/\-]{1,24}$', s) and s.lower() not in {'true','false','null','undefined'}:
        return True
    return False

unique=set()
by_bucket={k:set() for k in ['critical_public','auth','product','admin','other']}
file_scores=[]

def bucket(path):
    p=path.replace('\\','/').lower()
    if any(x in p for x in ['/admin/','orbital-edge','operations-noc']): return 'admin'
    if any(x in p for x in ['login','register','reset-password','access','onboarding']): return 'auth'
    if any(x in p for x in ['pricing','legal','cookie','homepage','navigation','marketplace','business','creators','status','buy-acp','whitepaper','docs/']): return 'critical_public'
    if any(x in p for x in ['wallet','billing','dashboard','bridge','pay','orders','listings','organizations','developers','workflow','strategy','ai-','/ai/','treasury','staking','governance','merchant','referrals','notifications','search','feed','contracts','funds','pools','projects','agents','runs','ledger','reputation','explorer','claim','convert','payment']): return 'product'
    return 'other'

for base in ['src/app','src/components']:
  for dp,_,fs in os.walk(base):
    for f in fs:
      if not f.endswith('.tsx'): continue
      if 'Language' in f: continue
      path=os.path.join(dp,f)
      lines=Path(path).read_text(encoding='utf-8', errors='replace').splitlines()
      local=set()
      for line in lines:
        if skip.search(line): continue
        if "t('" in line or 't("' in line: continue
        if 'i18nKey' in line: continue
        for m in jsx_text.finditer(line):
          s=m.group(1).strip()
          if is_ui(s): local.add(s)
        for m in str_lit.finditer(line):
          s=m.group(2).strip()
          if is_ui(s): local.add(s)
      if local:
        unique |= local
        b=bucket(path)
        by_bucket[b] |= local
        file_scores.append((len(local), path.replace('\\','/'), b))

print('REFINED_UNIQUE', len(unique))
for b,s in by_bucket.items():
    print(f'  bucket {b}: {len(s)}')
print('TOP25')
for n,p,b in sorted(file_scores, reverse=True)[:25]:
    print(f'  {n:3d} [{b}] {p}')

for p in ['src/app/HomePage.tsx','src/components/Navigation.tsx','src/components/CookieConsent.tsx','src/app/login/LoginForm.tsx','src/app/register/page.tsx']:
    h=set()
    lines=Path(p).read_text(encoding='utf-8', errors='replace').splitlines()
    for line in lines:
        if skip.search(line): continue
        if "t('" in line or 't("' in line: continue
        if 'i18nKey' in line: continue
        for m in jsx_text.finditer(line):
            s=m.group(1).strip()
            if is_ui(s): h.add(s)
        for m in str_lit.finditer(line):
            s=m.group(2).strip()
            if is_ui(s): h.add(s)
    print('WIRED_LEFTOVER', p, len(h), sorted(list(h))[:15])
