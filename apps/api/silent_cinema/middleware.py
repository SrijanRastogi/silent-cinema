"""Request correlation middleware."""

from __future__ import annotations

import re
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


class RequestIDMiddleware:
    """Attach a trustworthy request id to every HTTP response.

    A caller-supplied id is honoured only when it matches a strict character
    and length allowlist; otherwise a fresh UUID is generated. This prevents
    log injection and unbounded header propagation.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        candidate = Headers(scope=scope).get("x-request-id")
        request_id = (
            candidate
            if candidate is not None and _REQUEST_ID_PATTERN.fullmatch(candidate)
            else str(uuid4())
        )
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)["X-Request-ID"] = request_id
            await send(message)

        await self.app(scope, receive, send_with_request_id)
