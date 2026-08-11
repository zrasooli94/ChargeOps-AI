import pytest
from fastapi import HTTPException

from app.core.auth_dependencies import (
    require_admin,
    require_operator,
    require_viewer,
)
from app.models.user import User


def make_user(
    role: str,
) -> User:
    return User(
        email=(
            f"{role}@chargeops.local"
        ),
        password_hash=(
            "test-password-hash"
        ),
        role=role,
        is_active=True,
    )


def test_viewer_can_access_viewer_role(
) -> None:
    user = make_user(
        "viewer"
    )

    result = require_viewer(
        user
    )

    assert result is user


def test_operator_can_access_viewer_role(
) -> None:
    user = make_user(
        "operator"
    )

    result = require_viewer(
        user
    )

    assert result is user


def test_admin_can_access_viewer_role(
) -> None:
    user = make_user(
        "admin"
    )

    result = require_viewer(
        user
    )

    assert result is user


def test_viewer_cannot_access_operator_role(
) -> None:
    user = make_user(
        "viewer"
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        require_operator(
            user
        )

    assert (
        exc_info.value.status_code
        == 403
    )


def test_operator_can_access_operator_role(
) -> None:
    user = make_user(
        "operator"
    )

    result = require_operator(
        user
    )

    assert result is user


def test_admin_can_access_operator_role(
) -> None:
    user = make_user(
        "admin"
    )

    result = require_operator(
        user
    )

    assert result is user


def test_viewer_cannot_access_admin_role(
) -> None:
    user = make_user(
        "viewer"
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        require_admin(
            user
        )

    assert (
        exc_info.value.status_code
        == 403
    )


def test_operator_cannot_access_admin_role(
) -> None:
    user = make_user(
        "operator"
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        require_admin(
            user
        )

    assert (
        exc_info.value.status_code
        == 403
    )


def test_admin_can_access_admin_role(
) -> None:
    user = make_user(
        "admin"
    )

    result = require_admin(
        user
    )

    assert result is user