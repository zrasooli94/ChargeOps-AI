import logging
from uuid import (
    UUID,
    uuid4,
)

from fastapi import (
    FastAPI,
    Request,
)
from fastapi.responses import (
    JSONResponse,
)

from app.core.security_audit import (
    log_security_event,
)

logger = logging.getLogger(
    "chargeops.errors"
)


SENSITIVE_ACTIONS = (
    (
        "POST",
        "/users",
    ),
    (
        "PATCH",
        "/users/",
    ),
    (
        "POST",
        "/knowledge/documents/upload",
    ),
    (
        "DELETE",
        "/knowledge/documents/",
    ),
    (
        "PATCH",
        "/incidents/",
    ),
    (
        "POST",
        "/agent/resume",
    ),
)


def create_request_id(
    supplied_value: str | None,
) -> str:
    if supplied_value:
        try:
            return str(
                UUID(
                    supplied_value
                )
            )

        except ValueError:
            pass

    return str(
        uuid4()
    )


def is_sensitive_action(
    method: str,
    path: str,
) -> bool:
    normalized_method = (
        method.upper()
    )

    for (
        expected_method,
        path_prefix,
    ) in SENSITIVE_ACTIONS:
        if (
            normalized_method
            == expected_method
            and path.startswith(
                path_prefix
            )
        ):
            return True

    return False


def register_error_handling(
    app: FastAPI,
) -> None:
    @app.middleware(
        "http"
    )
    async def request_security_context(
        request: Request,
        call_next,
    ):
        request_id = (
            create_request_id(
                request.headers.get(
                    "X-Request-ID"
                )
            )
        )

        request.state.request_id = (
            request_id
        )

        response = await call_next(
            request
        )

        response.headers[
            "X-Request-ID"
        ] = request_id

        if is_sensitive_action(
            request.method,
            request.url.path,
        ):
            status_code = (
                response.status_code
            )

            successful = (
                status_code
                < 400
            )

            log_security_event(
                event=(
                    "security."
                    "sensitive_action"
                ),
                outcome=(
                    "success"
                    if successful
                    else "failure"
                ),
                severity=(
                    "INFO"
                    if successful
                    else "WARNING"
                ),
                user_id=getattr(
                    request.state,
                    "user_id",
                    None,
                ),
                user_role=getattr(
                    request.state,
                    "user_role",
                    None,
                ),
                client_ip=(
                    request.client.host
                    if request.client
                    else "unknown"
                ),
                request_id=(
                    request_id
                ),
                target=(
                    f"{request.method} "
                    f"{request.url.path}"
                ),
                reason=(
                    f"http_{status_code}"
                ),
            )

        return response

    @app.exception_handler(
        Exception
    )
    async def unhandled_exception_handler(
        request: Request,
        exception: Exception,
    ) -> JSONResponse:
        request_id = getattr(
            request.state,
            "request_id",
            str(
                uuid4()
            ),
        )

        logger.exception(
            "Unhandled ChargeOps error "
            "request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
            exc_info=exception,
        )

        return JSONResponse(
            status_code=500,
            content={
                "detail": (
                    "Internal server error."
                ),
                "request_id": (
                    request_id
                ),
            },
            headers={
                "X-Request-ID": (
                    request_id
                ),
            },
        )