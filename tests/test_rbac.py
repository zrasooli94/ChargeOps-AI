
from uuid import uuid4

import pytest
from fastapi import (
    HTTPException,
    Request,
)

from app.core.auth_dependencies import (
    require_admin,
    require_operator,
    require_viewer,
)
from app.models.user import User
from app.schemas.auth import UserRole


def make_user(
    role: UserRole,
) -> User:
    return User(
        id=uuid4(),
        email=(
            f"{role}@test.chargeops.local"
        ),
        password_hash="test-password-hash",
        role=role,
        is_active=True,
    )


def make_request() -> Request:
    scope = {
        "type": "http",
        "asgi": {
            "version": "3.0",
        },
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/test-rbac",
        "raw_path": b"/test-rbac",
        "query_string": b"",
        "headers": [],
        "client": (
            "127.0.0.1",
            12345,
        ),
        "server": (
            "testserver",
            80,
        ),
        "state": {},
    }

    return Request(
        scope
    )


def test_viewer_can_access_viewer_role(
) -> None:
    user = make_user(
        "viewer"
    )

    result = require_viewer(
        request=make_request(),
        current_user=user,
    )

    assert result is user


def test_operator_can_access_viewer_role(
) -> None:
    user = make_user(
        "operator"
    )

    result = require_viewer(
        request=make_request(),
        current_user=user,
    )

    assert result is user


def test_admin_can_access_viewer_role(
) -> None:
    user = make_user(
        "admin"
    )

    result = require_viewer(
        request=make_request(),
        current_user=user,
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
            request=make_request(),
            current_user=user,
        )

    assert (
        exc_info.value.status_code
        == 403
    )

    assert (
        exc_info.value.detail
        == (
            "You do not have permission "
            "to perform this action."
        )
    )


def test_operator_can_access_operator_role(
) -> None:
    user = make_user(
        "operator"
    )

    result = require_operator(
        request=make_request(),
        current_user=user,
    )

    assert result is user


def test_admin_can_access_operator_role(
) -> None:
    user = make_user(
        "admin"
    )

    result = require_operator(
        request=make_request(),
        current_user=user,
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
            request=make_request(),
            current_user=user,
        )

    assert (
        exc_info.value.status_code
        == 403
    )

    assert (
        exc_info.value.detail
        == (
            "You do not have permission "
            "to perform this action."
        )
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
            request=make_request(),
            current_user=user,
        )

    assert (
        exc_info.value.status_code
        == 403
    )

    assert (
        exc_info.value.detail
        == (
            "You do not have permission "
            "to perform this action."
        )
    )


def test_admin_can_access_admin_role(
) -> None:
    user = make_user(
        "admin"
    )

    result = require_admin(
        request=make_request(),
        current_user=user,
    )

    assert result is user