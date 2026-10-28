from __future__ import annotations

import json
from typing import Any, Callable, Awaitable
from uuid import UUID

from app.services.cache import get_redis_client


# Channel names
CHANNEL_WORKFLOW_RUNS = "workflow:run:events"
CHANNEL_NOTIFICATIONS = "notifications:fanout"
CHANNEL_SYSTEM = "system:events"


async def publish(channel: str, message: dict[str, Any]) -> bool:
    """Publish a message to a Redis pub/sub channel. No-op if Redis unavailable."""
    client = await get_redis_client()
    if client is None:
        return False
    try:
        await client.publish(channel, json.dumps(message, default=str))
        await client.aclose()
        return True
    except Exception:
        return False


async def publish_workflow_run_event(run_id: str | UUID, event_type: str, data: dict[str, Any]) -> bool:
    return await publish(CHANNEL_WORKFLOW_RUNS, {
        "run_id": str(run_id),
        "event_type": event_type,
        "data": data,
    })


async def publish_notification_event(notification_id: str | UUID, notification_type: str, recipient_user_id: str | UUID | None = None, recipient_agent_id: str | UUID | None = None) -> bool:
    return await publish(CHANNEL_NOTIFICATIONS, {
        "notification_id": str(notification_id),
        "type": notification_type,
        "recipient_user_id": str(recipient_user_id) if recipient_user_id else None,
        "recipient_agent_id": str(recipient_agent_id) if recipient_agent_id else None,
    })


async def subscribe(
    channels: list[str],
    callback: Callable[[str, dict[str, Any]], Awaitable[None]],
) -> None:
    """Subscribe to Redis pub/sub channels. Runs indefinitely. Call in a background task."""
    client = await get_redis_client()
    if client is None:
        return

    pubsub = client.pubsub()
    try:
        await pubsub.subscribe(*channels)
        async for raw_message in pubsub.listen():
            if raw_message["type"] == "message":
                channel = raw_message["channel"]
                try:
                    data = json.loads(raw_message["data"])
                except Exception:
                    data = raw_message["data"]
                await callback(str(channel), data)
    finally:
        await pubsub.unsubscribe(*channels)
        await pubsub.aclose()
        await client.aclose()


class WorkflowRunEventBroadcaster:
    """Broadcasts workflow run events to all subscribers via Redis pub/sub.

    Usage:
        broadcaster = WorkflowRunEventBroadcaster()
        await broadcaster.publish(run_id="...", event_type="running", data={...})

    On the consumer side, a background task subscribes:
        asyncio.create_task(broadcaster.subscribe_to_all(my_callback))
    """

    def __init__(self, channel: str = CHANNEL_WORKFLOW_RUNS):
        self.channel = channel

    async def publish(self, run_id: str, event_type: str, data: dict[str, Any] | None = None) -> bool:
        return await publish_workflow_run_event(run_id, event_type, data or {})

    async def subscribe(self, callback: Callable[[str, str, dict[str, Any]], Awaitable[None]]) -> None:
        """Subscribe to workflow run events and call callback(channel, event_type, data)."""
        async def _handler(ch: str, msg: dict[str, Any]) -> None:
            await callback(ch, msg.get("event_type", ""), msg.get("data", {}))
        await subscribe([self.channel], _handler)


class NotificationBroadcaster:
    """Broadcasts notification events for email/Telegram fanout processing."""

    async def publish(
        self,
        notification_id: str,
        notification_type: str,
        recipient_user_id: str | None = None,
        recipient_agent_id: str | None = None,
    ) -> bool:
        return await publish_notification_event(
            notification_id, notification_type, recipient_user_id, recipient_agent_id
        )