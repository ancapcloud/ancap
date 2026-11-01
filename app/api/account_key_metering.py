"""Count credential requests after request transactions and response cleanup finish."""
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

from app.services.account_api_keys import metered_key_id, record_key_request


class AccountKeyUsageMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = Headers(scope=scope)
        raw = headers.get("x-api-key")
        bearer = headers.get("authorization", "")
        if raw is None and bearer.lower().startswith("bearer ancap_"):
            raw = bearer[7:]
        key_id = await metered_key_id(raw)
        status = 500

        async def metered_send(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, metered_send)
        finally:
            # Never wait for our own key row while a request transaction still holds it.
            await record_key_request(key_id, status)
        return None
