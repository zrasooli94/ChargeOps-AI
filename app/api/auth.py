from typing import (
    Annotated,
    cast,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.auth_dependencies import (
    CurrentUser,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.login_rate_limiter import (
    login_rate_limiter,
)
from app.core.security import (
    create_access_token,
)
from app.core.security_audit import (
    log_security_event,
)
from app.schemas.auth import (
    AccessToken,
    UserRead,
    UserRole,
)
from app.services.auth_service import (
    authenticate_user,
    normalize_email,
)

router = APIRouter(
    prefix="/auth",
    tags=[
        "Authentication",
    ],
)


def get_client_ip(
    request: Request,
) -> str:
    """
    Return the direct network peer address.

    Do not trust X-Forwarded-For here yet because
    client-supplied forwarding headers can be
    spoofed unless a trusted proxy configuration
    is established.
    """

    if request.client is None:
        return "unknown"

    return request.client.host


@router.post(
    "/login",
    response_model=AccessToken,
)
async def login(
    request: Request,
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    session: Annotated[
        AsyncSession,
        Depends(
            get_db
        ),
    ],
) -> AccessToken:
    client_ip = get_client_ip(
        request
    )

    email = normalize_email(
        form_data.username
    )

    retry_after = (
        login_rate_limiter
        .get_retry_after(
            client_ip=client_ip,
            email=email,
            ip_attempt_limit=(
                settings
                .login_rate_limit_ip_attempts
            ),
            account_attempt_limit=(
                settings
                .login_rate_limit_account_attempts
            ),
            window_seconds=(
                settings
                .login_rate_limit_window_seconds
            ),
        )
    )

    if retry_after is not None:
        log_security_event(
            event=(
                "auth.login.rate_limited"
            ),
            outcome="denied",
            severity="WARNING",
            client_ip=client_ip,
            email=email,
            request_id=getattr(
                request.state,
                "request_id",
                None,
            ),
            reason="rate_limit",
        )

        raise HTTPException(
            status_code=(
                status
                .HTTP_429_TOO_MANY_REQUESTS
            ),
            detail=(
                "Too many login attempts. "
                "Try again later."
            ),
            headers={
                "Retry-After": str(
                    retry_after
                ),
            },
        )

    user = await authenticate_user(
        session=session,
        email=email,
        password=form_data.password,
    )

    if user is None:
        login_rate_limiter.record_failure(
            client_ip=client_ip,
            email=email,
            window_seconds=(
                settings
                .login_rate_limit_window_seconds
            ),
        )

        log_security_event(
            event="auth.login.failed",
            outcome="failure",
            severity="WARNING",
            client_ip=client_ip,
            email=email,
            request_id=getattr(
                request.state,
                "request_id",
                None,
            ),
            reason=(
                "invalid_credentials"
            ),
        )

        raise HTTPException(
            status_code=(
                status
                .HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Incorrect email "
                "or password."
            ),
            headers={
                "WWW-Authenticate": (
                    "Bearer"
                ),
            },
        )

    login_rate_limiter.clear_account_failures(
        client_ip=client_ip,
        email=email,
    )

    role = cast(
        UserRole,
        user.role,
    )

    access_token = (
        create_access_token(
            user_id=user.id,
            role=role,
        )
    )

    log_security_event(
        event="auth.login.success",
        outcome="success",
        user_id=user.id,
        user_role=user.role,
        client_ip=client_ip,
        email=email,
        request_id=getattr(
            request.state,
            "request_id",
            None,
        ),
    )

    return AccessToken(
        access_token=(
            access_token
        )
    )


@router.get(
    "/me",
    response_model=UserRead,
)
async def get_me(
    current_user: CurrentUser,
) -> UserRead:
    return UserRead.model_validate(
        current_user
    )