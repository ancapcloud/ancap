"""Homepage dialog via OpenRouter.

The API key never leaves this process. The first turn picks a free model; later
turns reuse `session_model` so one dialog stays on one free model. Paid ids are
rejected. If the pinned free model fails, another free catalog model is used.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import httpx

from app.config import get_settings
from app.schemas.home_chat import HomeChatMessageIn

log = logging.getLogger(__name__)

_FREE_ROUTER = "openrouter/free"
_ALLOWED_HOSTS = {"openrouter.ai", "www.openrouter.ai"}
_PREFER = (
    "google/gemma-3-27b-it:free",
    "google/gemma-3-12b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "mistralai/mistral-small-3.2-24b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "qwen/qwen-2.5-7b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
)
_LANG_NAMES = {
    "en": "English",
    "ru": "Russian",
    "uk": "Ukrainian",
    "de": "German",
    "zh-Hant": "Traditional Chinese",
}
_MODE_HINTS = {
    "chat": "Answer the user's latest message.",
    "howto": "Explain how ANCAP works for a new visitor: publish or buy defined AI workflow outputs settled in ACP. Keep it practical and short.",
    "workflows": "Help the user find or choose a paid AI workflow on ANCAP. Point to /ai/workflows when useful. Do not invent prices or availability.",
    "earn": "Explain how creators earn on ANCAP by selling workflow runs. Mention the seller workspace when useful. Do not promise earnings.",
}
# Free models (esp. Nemotron) sometimes echo classifier tags into the reply body.
_SAFETY_LINE = re.compile(
    r"^\s*(?:user|response|prompt|assistant)\s+safety\s*:\s*\S+\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_SAFETY_INLINE = re.compile(
    r"(?:^|\n)\s*(?:user|response|prompt|assistant)\s+safety\s*:\s*\S+\s*(?=\n|$)",
    re.IGNORECASE,
)

_router_disabled = False


class HomeChatError(Exception):
    def __init__(self, code: str, status_code: int):
        super().__init__(code)
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True)
class HomeChatResult:
    reply: str
    model: str
    label: str


def clear_home_chat_state() -> None:
    global _router_disabled
    _router_disabled = False


def home_chat_status() -> dict[str, Any]:
    settings = get_settings()
    enabled = bool(settings.home_chat_enabled)
    configured = enabled and bool((settings.openrouter_api_key or "").strip())
    return {
        "enabled": enabled,
        "configured": configured,
        "selection": "automatic",
        "provider": "openrouter",
        "label": "Free auto",
    }


def pretty_model(model_id: str) -> str:
    raw = (model_id or "").strip()
    if not raw or raw == _FREE_ROUTER:
        return "Free auto"
    slug = raw.split("/")[-1]
    slug = re.sub(r":free$", "", slug, flags=re.IGNORECASE)
    slug = re.sub(r"-(instruct|it|chat|preview)$", "", slug, flags=re.IGNORECASE)
    parts: list[str] = []
    for part in slug.split("-"):
        if not part:
            continue
        if re.fullmatch(r"\d+(?:\.\d+)?b", part, flags=re.IGNORECASE):
            parts.append(part[:-1] + "B")
            continue
        if re.fullmatch(r"\d+(?:\.\d+)?", part):
            parts.append(part)
            continue
        parts.append(part[:1].upper() + part[1:])
    return " ".join(parts) or "Free auto"


def free_model_ids(models: list[dict[str, Any]]) -> list[str]:
    found: list[str] = []
    for model in models:
        if not isinstance(model, dict) or not _is_free_text(model):
            continue
        mid = str(model.get("id") or "")
        if mid and mid not in found:
            found.append(mid)
    rank = {name: index for index, name in enumerate(_PREFER)}
    found.sort(key=lambda mid: (rank.get(mid, len(_PREFER)), mid))
    return found


def _is_free_text(model: dict[str, Any]) -> bool:
    mid = str(model.get("id") or "")
    if not mid.lower().endswith(":free"):
        return False
    pricing = model.get("pricing") or {}
    if not isinstance(pricing, dict):
        return False
    for key in ("prompt", "completion", "request"):
        raw = pricing.get(key, "0")
        if raw in (None, ""):
            continue
        try:
            if float(raw) != 0:
                return False
        except (TypeError, ValueError):
            return False
    architecture = model.get("architecture") or {}
    outputs = architecture.get("output_modalities") if isinstance(architecture, dict) else None
    if outputs and "text" not in outputs:
        return False
    return True


def _base_url() -> str:
    raw = (get_settings().openrouter_base_url or "").strip().rstrip("/")
    parsed = urlsplit(raw)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in _ALLOWED_HOSTS or parsed.username or parsed.password:
        raise HomeChatError("NOT_CONFIGURED", 503)
    return f"https://{host}{parsed.path}".rstrip("/")


def build_messages(*, messages: list[HomeChatMessageIn] | list[dict[str, str]], mode: str, lang: str) -> list[dict[str, str]]:
    lang_name = _LANG_NAMES.get(lang, "English")
    hint = _MODE_HINTS.get(mode, _MODE_HINTS["chat"])
    system = (
        "You are the ANCAP homepage assistant. "
        "ANCAP is an ACP-first platform where people buy, create, and sell defined AI workflow outputs. "
        f"Reply in {lang_name}. Be concise and practical. {hint} "
        "You cannot access wallets, sign transactions, move ACP, or start jobs. "
        "Never invent balances, prices, or legal status. If you are unsure, say so. "
        "Never output safety classifiers, labels, or metadata such as "
        "'User Safety: safe' or 'Response Safety: safe' — reply with the answer only."
    )
    wired = [{"role": "system", "content": system}]
    for message in list(messages)[-8:]:
        if isinstance(message, dict):
            role = str(message.get("role") or "")
            content = str(message.get("content") or "").strip()
        else:
            role = message.role
            content = message.content.strip()
        if role == "assistant":
            content = scrub_model_reply(content)
        if role in {"user", "assistant"} and content:
            wired.append({"role": role, "content": content})
    return wired


def scrub_model_reply(text: str) -> str:
    """Remove free-model safety classifier noise from visible reply text."""
    raw = (text or "").strip()
    if not raw:
        return ""
    cleaned = _SAFETY_LINE.sub("", raw)
    cleaned = _SAFETY_INLINE.sub("\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def _message_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    message = (choices[0].get("message") if choices and isinstance(choices[0], dict) else {}) or {}
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        bits: list[str] = []
        for part in content:
            if isinstance(part, str):
                bits.append(part)
            elif isinstance(part, dict):
                bits.append(str(part.get("text") or ""))
        return "\n".join(bit for bit in bits if bit).strip()
    return ""


def _unknown_model(status: int, payload: Any) -> bool:
    if status not in {400, 404}:
        return False
    message = ""
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = str(error.get("message") or "")
        elif error:
            message = str(error)
    lowered = message.lower()
    return "model" in lowered or "endpoint" in lowered or status == 404


async def _openrouter_request(method: str, path: str, json_body: dict[str, Any] | None = None) -> tuple[int, Any]:
    settings = get_settings()
    key = (settings.openrouter_api_key or "").strip()
    if not key:
        raise HomeChatError("NOT_CONFIGURED", 503)
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.openrouter_site_url or "https://ancap.cloud",
        "X-Title": settings.openrouter_app_name or "ANCAP",
    }
    timeout = httpx.Timeout(settings.home_chat_timeout_seconds)
    url = f"{_base_url()}{path}"
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False, trust_env=False) as client:
            response = await client.request(method, url, headers=headers, json=json_body)
    except httpx.HTTPError:
        raise HomeChatError("UPSTREAM", 502) from None
    try:
        payload: Any = response.json()
    except Exception:
        payload = {"error": {"message": "unreadable response"}}
    return response.status_code, payload


async def _load_free_ids() -> list[str]:
    status, payload = await _openrouter_request("GET", "/models")
    if status != 200 or not isinstance(payload, dict):
        log.warning("home_chat model list status=%s", status)
        return []
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    return free_model_ids(data)


def _normalize_free_session(model_id: str | None) -> str | None:
    raw = (model_id or "").strip()
    if not raw or raw.lower() == _FREE_ROUTER:
        return None
    if not raw.lower().endswith(":free"):
        return None
    if not re.fullmatch(r"[a-z0-9][a-z0-9._/-]{0,118}:free", raw, flags=re.IGNORECASE):
        return None
    return raw


async def complete_home_chat(
    *,
    messages: list[HomeChatMessageIn] | list[dict[str, str]],
    mode: str = "chat",
    lang: str = "en",
    session_model: str | None = None,
) -> HomeChatResult:
    global _router_disabled
    settings = get_settings()
    if not settings.home_chat_enabled:
        raise HomeChatError("DISABLED", 503)
    if not (settings.openrouter_api_key or "").strip():
        raise HomeChatError("NOT_CONFIGURED", 503)

    wired = build_messages(messages=messages, mode=mode, lang=lang)
    if len(wired) < 2:
        raise HomeChatError("EMPTY", 422)

    pinned = _normalize_free_session(session_model)
    candidates: list[str] = []
    if pinned:
        candidates.append(pinned)
    elif _router_disabled:
        candidates.extend((await _load_free_ids())[:2])
    else:
        candidates.append(_FREE_ROUTER)
    if not candidates:
        raise HomeChatError("UPSTREAM", 502)

    last_status = 502
    saw_rate_limit = False
    index = 0
    while index < len(candidates) and index < 3:
        model = candidates[index]
        body = {
            "model": model,
            "messages": wired,
            "max_tokens": max(64, min(int(settings.home_chat_max_tokens or 700), 800)),
            "temperature": 0.4,
        }
        try:
            status, payload = await _openrouter_request("POST", "/chat/completions", body)
        except HomeChatError as exc:
            if exc.code != "UPSTREAM":
                raise
            status, payload = exc.status_code, {}

        if status == 200 and isinstance(payload, dict):
            reply = scrub_model_reply(_message_text(payload))
            if reply:
                reply = re.sub(r"\n{3,}", "\n\n", reply).strip()
                if len(reply) > 4000:
                    reply = reply[:4000].rstrip() + "…"
                used = str(payload.get("model") or model)
                if pinned:
                    used = pinned
                elif not used or used == _FREE_ROUTER:
                    used = model if model != _FREE_ROUTER else used
                    if used == _FREE_ROUTER:
                        # Should not happen; fall back to a catalog free id if needed.
                        free_ids = await _load_free_ids()
                        used = free_ids[0] if free_ids else used
                return HomeChatResult(reply=reply, model=used, label=pretty_model(used))
            status = 502

        last_status = status
        log.warning("home_chat upstream status=%s", status)
        if status == 429:
            saw_rate_limit = True
        if model == _FREE_ROUTER and _unknown_model(status, payload):
            _router_disabled = True
        if status in {401, 403}:
            raise HomeChatError("UPSTREAM", 502)
        if index == 0 and (status == 429 or _unknown_model(status, payload) or status >= 500):
            for mid in await _load_free_ids():
                if mid not in candidates:
                    candidates.append(mid)
                if len(candidates) >= 3:
                    break
        elif status not in {429} and not _unknown_model(status, payload) and status < 500:
            break
        index += 1

    if saw_rate_limit or last_status == 429:
        raise HomeChatError("RATE_LIMITED", 429)
    raise HomeChatError("UPSTREAM", 502)
