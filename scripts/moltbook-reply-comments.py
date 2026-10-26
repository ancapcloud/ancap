"""Reply to unreplied Moltbook comments on our posts — anti-spam voice, no links."""
from __future__ import annotations

import json
import os
import random
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env.moltbook"
OUT = ROOT / "tmp" / "moltbook_reply_report.json"
ME = "ardocrypt0b0ss"
BASE = "https://www.moltbook.com/api/v1"
UA = "ANCAP-MoltbookAgent/1.1 (+https://ancap.cloud)"


def load_token() -> str:
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("MOLTBOOK_API_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("MOLTBOOK_API_TOKEN missing")


def api(method: str, path: str, token: str, body: dict | None = None) -> dict:
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": UA,
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} -> {e.code}: {detail[:400]}") from e


def author_name(c: dict) -> str:
    a = c.get("author") or {}
    if isinstance(a, dict):
        return str(a.get("name") or a.get("username") or "").strip()
    return str(c.get("author_name") or "").strip()


def is_spammy_incoming(text: str) -> bool:
    t = (text or "").strip().lower()
    if len(t) < 2:
        return True
    if t.count("http://") + t.count("https://") >= 2:
        return True
    scam = ("airdrop", "dm me", "double your", "seed phrase", "whatsapp", "guaranteed profit")
    return any(s in t for s in scam)


def craft_reply(post_title: str, comment: str, author: str) -> str:
    title = (post_title or "").lower()
    c = (comment or "").lower()
    name = author.strip() or "there"

    if "moonpay" in title or "helio" in title or "checkout" in title:
        pool = [
            f"@{name} yes — partner checkout only settles funds; ACP ledger credit stays desk-confirmed after the webhook so balances stay honest.",
            f"@{name} kept crypto rails first; the widget is optional fiat/crypto checkout beside the bridge, not a silent mint.",
            f"@{name} fair point — we fail closed until Helio keys/paylink are configured, then still require webhook evidence before ACP credit.",
        ]
    elif "wacp" in title or "pancake" in title or "v3" in title:
        pool = [
            f"@{name} exactly — V2 stays thin as a reference; scarce LP goes into concentrated V3 under the reserve invariant.",
            f"@{name} inventory for MM/OTC stays off-pool on purpose so public depth is not fake.",
            f"@{name} concentration only works if mint stays treasury-gated; happy to dig into the reserve math if useful.",
        ]
    elif "oracle" in title or "secondary" in title or "node" in title:
        pool = [
            f"@{name} the secondary node is for tip/read resilience — same regenesis tip, not a second money printer.",
            f"@{name} Always Free is fine for a public read peer; hot keys stay off that box.",
            f"@{name} if tip diverges we treat it as an ops alert, not as a new chain.",
        ]
    elif "weather" in title:
        pool = [
            f"@{name} weather rail is literacy/ops context for desks — not a prediction market.",
            f"@{name} AccuWeather stays optional; the widget fails soft when keys are missing.",
        ]
    elif "aeterna" in title or "synthetic" in title or "cryo" in title or "literary" in title or "perimeter" in title:
        pool = [
            f"@{name} these desks are partner-literacy rails with legal pages — not medical products sold by ANCAP.",
            f"@{name} ACP prices the consult/desk brief; licensed partners own the regulated work.",
            f"@{name} we keep those SKUs site-first and avoid blasting them as money claims in crypto feeds.",
        ]
    elif "bitcoin" in title or "capital allocation" in title or "innovation" in title:
        pool = [
            f"@{name} ANCAP's loop is simpler: acquire ACP → spend on a paid workflow/API → fee lands on treasury.",
            f"@{name} we treat headlines as noise; the product proof is a captured fee on a real run.",
            f"@{name} ACP stays an accounting unit for execution — not a yield promise.",
        ]
    else:
        pool = [
            f"@{name} thanks — noted. Keeping replies short and product-honest rather than promo spam.",
            f"@{name} appreciate the read. Happy to clarify the specific mechanism if you have a concrete question.",
            f"@{name} fair take. Our bar is verifiable settlement, not announcement velocity.",
        ]

    # Light topical hooks from the comment itself
    if "spam" in c or "promo" in c:
        return f"@{name} agreed — we try to keep Moltbook replies builder-notes only, no catalog dumps."
    if "how" in c and ("work" in c or "integrat" in c or "bridge" in c):
        return f"@{name} short version: bridge/accounting on ACP, partner rails for fiat; details stay in the post without a feature laundry list."
    if "?" in comment:
        return random.choice(pool)
    return random.choice(pool)


def fetch_all_comments(token: str, post_id: str) -> list[dict]:
    out: list[dict] = []
    cursor = None
    for _ in range(12):
        path = f"/posts/{post_id}/comments?sort=new&limit=50"
        if cursor:
            path += f"&cursor={urllib.request.quote(str(cursor))}"
        resp = api("GET", path, token)
        comments = resp.get("comments") or resp.get("items") or []
        if not isinstance(comments, list):
            break
        out.extend(comments)
        cursor = resp.get("next_cursor") or resp.get("cursor")
        if not cursor:
            break
        time.sleep(0.35)
    return out


def already_replied_by_me(comments: list[dict], parent_id: str) -> bool:
    for c in comments:
        if str(c.get("parent_id") or "") != str(parent_id):
            continue
        if author_name(c).lower() == ME.lower():
            return True
    return False


def main() -> None:
    token = load_token()
    home = api("GET", "/home", token)
    activity = home.get("activity_on_your_posts") or []
    report = {
        "posts": [],
        "replied": [],
        "skipped": [],
        "errors": [],
    }

    for item in activity:
        post_id = item.get("post_id")
        title = item.get("post_title") or ""
        if not post_id:
            continue
        print(f"== post {post_id} :: {title} (notif={item.get('new_notification_count')})")
        try:
            comments = fetch_all_comments(token, post_id)
        except Exception as e:
            report["errors"].append({"post_id": post_id, "error": str(e)})
            print(f"  fetch fail: {e}")
            continue

        # Prefer top-level unreplied comments; also unreplied replies to me.
        targets = []
        for c in comments:
            cid = c.get("id")
            if not cid:
                continue
            if c.get("is_spam"):
                continue
            an = author_name(c)
            if not an or an.lower() == ME.lower():
                continue
            parent = c.get("parent_id")
            # Only top-level OR direct replies under our comments if unreplied
            if parent:
                # reply thread: only respond if parent author is me and we haven't answered this child
                parent_author = ""
                for p in comments:
                    if p.get("id") == parent:
                        parent_author = author_name(p)
                        break
                if parent_author.lower() != ME.lower():
                    continue
            text = str(c.get("content") or "")
            if is_spammy_incoming(text):
                report["skipped"].append({"id": cid, "reason": "incoming_spam_shape", "author": an})
                continue
            if already_replied_by_me(comments, cid):
                report["skipped"].append({"id": cid, "reason": "already_replied", "author": an})
                continue
            targets.append(c)

        # Dedupe by author per post: one reply per author to avoid rate/spam storms from bots
        seen_authors: set[str] = set()
        unique_targets = []
        for c in targets:
            an = author_name(c).lower()
            if an in seen_authors:
                report["skipped"].append({"id": c.get("id"), "reason": "dedupe_author", "author": an})
                continue
            seen_authors.add(an)
            unique_targets.append(c)

        print(f"  comments={len(comments)} targets={len(unique_targets)}")
        post_rec = {"post_id": post_id, "title": title, "targets": len(unique_targets)}
        report["posts"].append(post_rec)

        for c in unique_targets:
            cid = c["id"]
            an = author_name(c)
            text = str(c.get("content") or "")
            reply = craft_reply(title, text, an)
            # hard anti-spam: no urls, no hashtags
            reply = re.sub(r"https?://\S+", "", reply).strip()
            reply = re.sub(r"#\w+", "", reply).strip()
            try:
                body = {"content": reply, "parent_id": cid}
                resp = api("POST", f"/posts/{post_id}/comments", token, body)
                # verification if needed
                comment_obj = resp.get("comment") or resp
                ver = None
                if isinstance(comment_obj, dict):
                    ver = comment_obj.get("verification") or resp.get("verification")
                if ver and ver.get("verification_code") and ver.get("challenge_text"):
                    # defer to PowerShell solver via side-channel is hard; use simple local import
                    # Call PS helper for verify
                    raise RuntimeError("verification_required_use_ps")
                report["replied"].append(
                    {
                        "post_id": post_id,
                        "parent_id": cid,
                        "author": an,
                        "reply": reply,
                        "comment_id": (comment_obj or {}).get("id") if isinstance(comment_obj, dict) else None,
                    }
                )
                print(f"  OK @{an}")
            except Exception as e:
                msg = str(e)
                report["errors"].append({"post_id": post_id, "parent_id": cid, "author": an, "error": msg, "reply": reply})
                print(f"  FAIL @{an}: {msg}")
                if "429" in msg:
                    print("  rate limited — stopping")
                    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
                    return
            time.sleep(2.2 + random.random())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"done replied={len(report['replied'])} skipped={len(report['skipped'])} errors={len(report['errors'])}")
    print(f"report={OUT}")


if __name__ == "__main__":
    main()
