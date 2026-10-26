# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "CLAUDE.md"
t = p.read_text(encoding="utf-8")
needle = "/legal/adhd-support`). Track:"
insert = (
    "/legal/adhd-support`), PulmoPure lung-care subscription (14,000 ACP / month; "
    "licensed pulmonology partner literacy; not a CE/FDA device, ozone therapy, "
    "medical-gas compounding, or guaranteed clean-lungs outcome; `/legal/pulmopure`). Track:"
)
if "PulmoPure lung-care subscription" in t:
    print("already updated")
else:
    if needle not in t:
        raise SystemExit("needle missing")
    t = t.replace(needle, insert, 1)
    t = t.replace(
        "oxygen-carrier / synthetic-blood / ADHD-support rails wired",
        "oxygen-carrier / synthetic-blood / ADHD-support / PulmoPure rails wired",
        1,
    )
    p.write_text(t, encoding="utf-8")
    print("updated")
