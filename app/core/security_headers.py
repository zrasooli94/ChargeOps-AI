from collections.abc import (
    Awaitable,
    Callable,
)

from starlette.datastructures import (
    MutableHeaders,
)
from starlette.types import (
    Message,
    Receive,
    Scope,
    Send,
)

ASGIApp = Callable[
    [
        Scope,
        Receive,
        Send,
    ],
    Awaitable[None],
]


class SecurityHeadersMiddleware:
    """
    Add browser-oriented security headers to
    ChargeOps HTTP responses.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        enable_hsts: bool = False,
        hsts_max_age: int = 31536000,
    ) -> None:
        self.app = app

        self.enable_hsts = (
            enable_hsts
        )

        self.hsts_max_age = (
            hsts_max_age
        )

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(
                scope,
                receive,
                send,
            )
            return

        async def send_with_security_headers(
            message: Message,
        ) -> None:
            if (
                message["type"]
                == "http.response.start"
            ):
                headers = MutableHeaders(
                    scope=message
                )

                headers[
                    "X-Content-Type-Options"
                ] = "nosniff"

                headers[
                    "X-Frame-Options"
                ] = "DENY"

                headers[
                    "Referrer-Policy"
                ] = "no-referrer"

                headers[
                    "Permissions-Policy"
                ] = (
                    "camera=(), "
                    "microphone=(), "
                    "geolocation=()"
                )

                headers[
                    "Content-Security-Policy"
                ] = (
                    "frame-ancestors 'none'; "
                    "object-src 'none'; "
                    "base-uri 'none'"
                )

                headers[
                    "Cache-Control"
                ] = "no-store"

                if self.enable_hsts:
                    headers[
                        "Strict-Transport-Security"
                    ] = (
                        "max-age="
                        f"{self.hsts_max_age}"
                    )

            await send(
                message
            )

        await self.app(
            scope,
            receive,
            send_with_security_headers,
        )