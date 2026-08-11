from typing import Annotated, cast

from fastapi import (
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    TokenValidationError,
    decode_access_token,
)
from app.core.security_audit import (
    log_security_event,
)
from app.models.user import User
from app.schemas.auth import UserRole
from app.services.auth_service import (
    get_user_by_id,
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login"
)


def get_request_client_ip(
    request: Request,
) -> str:
    if request.client is None:
        return "unknown"

    return request.client.host


async def get_current_user(
    request: Request,
    token: Annotated[
        str,
        Depends(
            oauth2_scheme
        ),
    ],
    session: Annotated[
        AsyncSession,
        Depends(
            get_db
        ),
    ],
) -> User:
    credentials_error = HTTPException(
        status_code=(
            status.HTTP_401_UNAUTHORIZED
        ),
        detail=(
            "Could not validate "
            "authentication credentials."
        ),
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    try:
        claims = decode_access_token(
            token
        )

    except TokenValidationError:
        log_security_event(
            event="auth.token.rejected",
            outcome="denied",
            severity="WARNING",
            client_ip=(
                get_request_client_ip(
                    request
                )
            ),
            request_id=getattr(
                request.state,
                "request_id",
                None,
            ),
            reason=(
                "invalid_or_expired_token"
            ),
        )

        raise credentials_error from None

    user = await get_user_by_id(
        session=session,
        user_id=claims.sub,
    )

    if (
        user is None
        or not user.is_active
    ):
        log_security_event(
            event="auth.user.rejected",
            outcome="denied",
            severity="WARNING",
            user_id=claims.sub,
            client_ip=(
                get_request_client_ip(
                    request
                )
            ),
            request_id=getattr(
                request.state,
                "request_id",
                None,
            ),
            reason=(
                "missing_or_inactive_user"
            ),
        )

        raise credentials_error

    request.state.user_id = str(
        user.id
    )

    request.state.user_role = (
        user.role
    )

    return user


CurrentUser = Annotated[
    User,
    Depends(
        get_current_user
    ),
]


ROLE_LEVELS: dict[
    UserRole,
    int,
] = {
    "viewer": 1,
    "operator": 2,
    "admin": 3,
}


class RequireRole:
    def __init__(
        self,
        minimum_role: UserRole,
    ) -> None:
        self.minimum_role: UserRole = (
            minimum_role
        )

    def __call__(
        self,
        request: Request,
        current_user: CurrentUser,
    ) -> User:
        current_role = cast(
            UserRole,
            current_user.role,
        )

        current_level = (
            ROLE_LEVELS.get(
                current_role,
                0,
            )
        )

        required_level = (
            ROLE_LEVELS[
                self.minimum_role
            ]
        )

        if (
            current_level
            < required_level
        ):
            log_security_event(
                event="authz.role.denied",
                outcome="denied",
                severity="WARNING",
                user_id=current_user.id,
                user_role=(
                    current_user.role
                ),
                client_ip=(
                    get_request_client_ip(
                        request
                    )
                ),
                request_id=getattr(
                    request.state,
                    "request_id",
                    None,
                ),
                target=(
                    f"{request.method} "
                    f"{request.url.path}"
                ),
                reason=(
                    "requires_"
                    f"{self.minimum_role}"
                ),
            )

            raise HTTPException(
                status_code=(
                    status
                    .HTTP_403_FORBIDDEN
                ),
                detail=(
                    "You do not have "
                    "permission to perform "
                    "this action."
                ),
            )

        return current_user


require_viewer = RequireRole(
    "viewer"
)

require_operator = RequireRole(
    "operator"
)

require_admin = RequireRole(
    "admin"
)


ViewerUser = Annotated[
    User,
    Depends(
        require_viewer
    ),
]

OperatorUser = Annotated[
    User,
    Depends(
        require_operator
    ),
]

AdminUser = Annotated[
    User,
    Depends(
        require_admin
    ),
]