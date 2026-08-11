from collections.abc import (
    Callable,
    Iterator,
)
from uuid import uuid4

import pytest

from app.core.auth_dependencies import (
    get_current_user,
)
from app.main import app
from app.models.user import User
from app.schemas.auth import UserRole

AuthenticateAs = Callable[
    [UserRole],
    User,
]


@pytest.fixture
def authenticate_as(
) -> Iterator[AuthenticateAs]:
    def authenticate(
        role: UserRole,
    ) -> User:
        user = User(
            id=uuid4(),
            email=(
                f"{role}-test"
                "@chargeops.local"
            ),
            password_hash=(
                "test-password-hash"
            ),
            role=role,
            is_active=True,
        )

        async def override_current_user(
        ) -> User:
            return user

        app.dependency_overrides[
            get_current_user
        ] = override_current_user

        return user

    yield authenticate

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


@pytest.fixture
def authenticated_viewer(
    authenticate_as: AuthenticateAs,
) -> User:
    return authenticate_as(
        "viewer"
    )


@pytest.fixture
def authenticated_operator(
    authenticate_as: AuthenticateAs,
) -> User:
    return authenticate_as(
        "operator"
    )


@pytest.fixture
def authenticated_admin(
    authenticate_as: AuthenticateAs,
) -> User:
    return authenticate_as(
        "admin"
    )