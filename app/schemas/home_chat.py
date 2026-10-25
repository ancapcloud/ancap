"""Homepage dialog. The client cannot choose a model."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ChatRole = Literal["user", "assistant"]
ChatMode = Literal["chat", "plan", "multitask", "cloud"]
ChatLang = Literal["en", "ru", "uk", "de", "zh-Hant"]


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
