"""Public homepage dialog. Model choice stays on the server."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.config import get_settings
from app.schemas.home_chat import HomeChatRequest, HomeChatResponse, HomeChatStatus
from app.services.home_chat import HomeChatError, complete_home_chat, home_chat_status
from app.services.rate_limit import build_rate_limit_key, enforce_rate_limit, get_request_ip

router = APIRouter(prefix="/home-chat", tags=["Home chat"])


@router.get("/status", response_model=HomeChatStatus)
async def home_chat_status_route() -> HomeChatStatus:
    return HomeChatStatus(**home_chat_status())


@router.post("/messages", response_model=HomeChatResponse)
async def post_home_chat(payload: HomeChatRequest, request: Request) -> HomeChatResponse:
    settings = get_settings()
    if not settings.home_chat_enabled:
        raise HTTPException(status_code=503, detail={"code": "DISABLED", "message": "Home chat is disabled."})
    if not (settings.openrouter_api_key or "").strip():
        raise HTTPException(status_code=503, detail={"code": "NOT_CONFIGURED", "message": "Home chat is not configured."})

    await enforce_rate_limit(
        key=build_rate_limit_key(scope="home-chat", ip=get_request_ip(request)),
        limit=settings.home_chat_ip_limit,
        window_seconds=settings.home_chat_ip_window_seconds,
    )
    await enforce_rate_limit(
        key="home-chat:global",
        limit=settings.home_chat_global_limit,
        window_seconds=settings.home_chat_global_window_seconds,
    )

    try:
        result = await complete_home_chat(
            messages=payload.messages,
            mode=payload.mode,
            lang=payload.lang,
            session_model=payload.session_model,
        )
    except HomeChatError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": "Home chat is unavailable."},
        ) from None

    return HomeChatResponse(
        reply=result.reply,
        model=result.model,
        label=result.label,
        selection="automatic",
    )
