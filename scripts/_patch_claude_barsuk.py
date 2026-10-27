# -*- coding: utf-8 -*-
from pathlib import Path
p = Path(__file__).resolve().parents[1] / "CLAUDE.md"
t = p.read_text(encoding="utf-8")
if "Project Barsuk quantum-pen" in t:
    print("already")
else:
    old = "ADHD-support / PulmoPure rails wired"
    new = "ADHD-support / PulmoPure / Barsuk / teleport-earphones rails wired"
    if old not in t:
        raise SystemExit("wired marker missing")
    t = t.replace(old, new, 1)
    # insert before Track: docs/AETERNA
    marker = "Track: `docs/AETERNA_LONGEVITY_MARKETPLACE_ROADMAP.md`"
    insert = (
        ", Project Barsuk quantum-pen brief (36,000 ACP secure-comms literacy; not Parker/weapon; "
        "`/legal/barsuk`), teleport-earphones medevac fiction brief (58,000 ACP; not Apple/real teleport/"
        "weapon; `/legal/teleport-earphones`)"
    )
    if marker not in t:
        raise SystemExit("track marker missing")
    t = t.replace(marker, insert + ". Track: `docs/AETERNA_LONGEVITY_MARKETPLACE_ROADMAP.md`", 1)
    # fix double Track if any
    t = t.replace(". Track: `docs/AETERNA_LONGEVITY_MARKETPLACE_ROADMAP.md`. Track:", ". Track:", 1)
    p.write_text(t, encoding="utf-8")
    print("ok")
