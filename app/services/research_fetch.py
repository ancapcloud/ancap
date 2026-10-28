"""Public HTML only: bounded, pinned TLS fetch; page text is never instructions."""
import asyncio
import hashlib
import ipaddress
import re
from difflib import SequenceMatcher
from html.parser import HTMLParser

import httpx
from app.services.webhook_url_policy import validate_webhook_url_async

MAX_BYTES = 262144
MAX_TEXT = 16000


def text_changes(before: str, after: str):
    old, new = before.split(), after.split()
    changes = []
    truncated = False
    for kind, a, b, c, d in SequenceMatcher(None, old, new, autojunk=True).get_opcodes():
        if kind == "equal":
            continue
        removed, added = " ".join(old[a:b]), " ".join(new[c:d])
        if len(changes) == 20:
            truncated = True
            break
        truncated |= len(removed) > 500 or len(added) > 500
        changes.append({"before": removed[:500], "after": added[:500]})
    return {"items": changes, "truncated": truncated, "classification": "text_difference_not_semantic_materiality"}


class PageText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg", "template"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg", "template"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def extract_page(raw: bytes):
    # UTF-8 HTML is the first supported source type; reject unsupported encodings.
    page = PageText()
    page.feed(raw.decode("utf-8-sig", errors="strict"))
    text = re.sub(r"\s+", " ", " ".join(page.parts)).strip()
    if not text or len(text) > MAX_TEXT:
        raise ValueError("Unsupported text size")
    return hashlib.sha256(raw).hexdigest(), hashlib.sha256(text.encode()).hexdigest(), text


async def fetch_page(url):
    async with asyncio.timeout(12):
        target = await validate_webhook_url_async(url)
        if target.scheme != "https" or target.port != 443 or not target.pinned_ip or not ipaddress.ip_address(target.pinned_ip).is_global:
            raise ValueError("Public HTTPS required")
        async with httpx.AsyncClient(timeout=8, follow_redirects=False, trust_env=False) as client:
            async with client.stream("GET", target.pinned_request_url(), headers={
                "Host": target.hostname, "User-Agent": "ANCAP-Research/1.0", "Accept": "text/html",
                "Accept-Encoding": "identity"}, extensions={"sni_hostname": target.hostname}) as response:
                if response.status_code != 200:
                    raise ValueError("Source unavailable or redirected")
                if response.headers.get("content-type", "").split(";")[0].strip().lower() != "text/html":
                    raise ValueError("HTML source required")
                if response.headers.get("content-encoding", "identity").lower() != "identity":
                    raise ValueError("Compressed source is unsupported")
                charset = response.charset_encoding
                if charset and charset.lower() not in {"utf-8", "utf8"}:
                    raise ValueError("UTF-8 HTML required")
                raw = bytearray()
                async for chunk in response.aiter_raw(chunk_size=65536):
                    raw.extend(chunk)
                    if len(raw) > MAX_BYTES:
                        raise ValueError("Source exceeds size limit")
                return extract_page(bytes(raw))
