"""Homepage dialog. Paid models cannot be requested; a free session model may be pinned."""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ChatRole = Literal["user", "assistant"]
ChatMode = Literal["chat", "howto", "workflows", "earn"]
ChatLang = Literal["en", "ru", "uk", "de", "zh-Hant"]

_SESSION_MODEL = re.compile(r"^[a-z0-9][a-z0-9._/-]{0,118}:free$", re.IGNORECASE)


class HomeChatMessageIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: ChatRole
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def _strip_content(cls, value: str) -> str:
        text = value.replace("\x00", "").strip()
        if not text:
            raise ValueError("empty message")
        return text


class HomeChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[HomeChatMessageIn] = Field(min_length=1, max_length=8)
    mode: ChatMode = "chat"
    lang: ChatLang = "en"
    # Concrete free model returned by a previous turn. Keeps one model for the whole dialog.
    session_model: str | None = Field(default=None, max_length=128)

    @field_validator("session_model")
    @classmethod
    def _free_session_only(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            return None
        if text.lower() == "openrouter/free" or not _SESSION_MODEL.fullmatch(text):
            raise ValueError("session_model must be a free OpenRouter model id")
        return text

    @model_validator(mode="after")
    def _last_message_is_user(self) -> "HomeChatRequest":
        if self.messages[-1].role != "user":
            raise ValueError("last message must be from the user")
        return self


class HomeChatResponse(BaseModel):
    reply: str
    model: str
    label: str
    selection: str = "automatic"


class HomeChatStatus(BaseModel):
    enabled: bool
    configured: bool
    selection: str = "automatic"
    provider: str = "openrouter"
    label: str = "Free auto"
