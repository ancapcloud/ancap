from __future__ import annotations

import structlog
from structlog.typing import EventDict, WrappedLogger
from datetime import datetime, timezone

from app.config import get_settings


def add_timestamp(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    return event_dict


def add_service_name(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["service"] = "ancap-api"
    return event_dict


def rename_event_key(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    if "event" in event_dict:
        event_dict["type"] = event_dict.pop("event")
    return event_dict


def configure_logging() -> None:
    get_settings()

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        add_timestamp,
        add_service_name,
        rename_event_key,
        structlog.processors.JSONRenderer(
            serializer=lambda obj, **kw: __import__("json").dumps(
                obj, default=str, separators=(",", ":")
            )
        ),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)