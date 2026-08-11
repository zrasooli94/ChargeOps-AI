from typing import Annotated, cast

from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    OAuth2PasswordBearer,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.database import get_db
from app.core.security import (
    TokenValidationError,
    decode_access_token,
)
from app.models.user import User
from app.schemas.auth import UserRole
from app.services.auth_service import (
    get_user_by_id,
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login"
)


async def get_current_user(
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
        raise credentials_error from None

    user = await get_user_by_id(
        session=session,
        user_id=claims.sub,
    )

    if user is None:
        raise credentials_error

    if not user.is_active:
        raise credentials_error

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