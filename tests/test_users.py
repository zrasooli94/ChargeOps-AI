from datetime import (
    datetime,
    timezone,
)
from unittest.mock import (
    AsyncMock,
    patch,
)
from uuid import uuid4

from fastapi.testclient import (
    TestClient,
)

from app.main import app
from app.models.user import User
from app.services.auth_service import (
    UserAlreadyExistsError,
)

client = TestClient(app)


def make_user(
    *,
    email: str,
    role: str,
    is_active: bool = True,
) -> User:
    return User(
        id=uuid4(),
        email=email,
        password_hash="test-password-hash",
        role=role,
        is_active=is_active,
        created_at=datetime.now(
            timezone.utc
        ),
    )


# =================================================
# Authentication / RBAC
# =================================================


def test_users_requires_authentication(
) -> None:
    response = client.get(
        "/users"
    )

    assert response.status_code == 401


def test_viewer_cannot_list_users(
    authenticated_viewer,
) -> None:
    response = client.get(
        "/users"
    )

    assert response.status_code == 403


def test_operator_cannot_list_users(
    authenticated_operator,
) -> None:
    response = client.get(
        "/users"
    )

    assert response.status_code == 403


# =================================================
# List users
# =================================================


def test_admin_can_list_users(
    authenticated_admin,
) -> None:
    users = [
        make_user(
            email=(
                "admin@chargeops.local"
            ),
            role="admin",
        ),
        make_user(
            email=(
                "viewer@chargeops.local"
            ),
            role="viewer",
        ),
    ]

    with patch(
        "app.api.users.list_users",
        new=AsyncMock(
            return_value=users
        ),
    ):
        response = client.get(
            "/users"
        )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert (
        data[0]["email"]
        == "admin@chargeops.local"
    )

    assert (
        data[0]["role"]
        == "admin"
    )

    assert (
        data[1]["role"]
        == "viewer"
    )

    assert (
        "password_hash"
        not in data[0]
    )


# =================================================
# Create user
# =================================================


def test_admin_can_create_user(
    authenticated_admin,
) -> None:
    created_user = make_user(
        email=(
            "newviewer@chargeops.local"
        ),
        role="viewer",
    )

    create_mock = AsyncMock(
        return_value=created_user
    )

    with patch(
        "app.api.users.create_user",
        new=create_mock,
    ):
        response = client.post(
            "/users",
            json={
                "email": (
                    "newviewer@chargeops.local"
                ),
                "password": (
                    "StrongPassword123!"
                ),
                "role": "viewer",
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert (
        data["email"]
        == "newviewer@chargeops.local"
    )

    assert data["role"] == "viewer"

    assert data["is_active"] is True

    assert "password_hash" not in data

    create_mock.assert_awaited_once()


def test_duplicate_user_returns_409(
    authenticated_admin,
) -> None:
    with patch(
        "app.api.users.create_user",
        new=AsyncMock(
            side_effect=(
                UserAlreadyExistsError(
                    "A user with this email "
                    "already exists."
                )
            )
        ),
    ):
        response = client.post(
            "/users",
            json={
                "email": (
                    "existing@chargeops.local"
                ),
                "password": (
                    "StrongPassword123!"
                ),
                "role": "viewer",
            },
        )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "A user with this email "
            "already exists."
        )
    }


def test_create_user_rejects_short_password(
    authenticated_admin,
) -> None:
    response = client.post(
        "/users",
        json={
            "email": (
                "test@chargeops.local"
            ),
            "password": "short",
            "role": "viewer",
        },
    )

    assert response.status_code == 422


def test_create_user_rejects_invalid_role(
    authenticated_admin,
) -> None:
    response = client.post(
        "/users",
        json={
            "email": (
                "test@chargeops.local"
            ),
            "password": (
                "StrongPassword123!"
            ),
            "role": "superuser",
        },
    )

    assert response.status_code == 422


# =================================================
# Role updates
# =================================================


def test_admin_can_change_user_role(
    authenticated_admin,
) -> None:
    user_id = uuid4()

    updated_user = User(
        id=user_id,
        email=(
            "viewer@chargeops.local"
        ),
        password_hash=(
            "test-password-hash"
        ),
        role="operator",
        is_active=True,
        created_at=datetime.now(
            timezone.utc
        ),
    )

    update_mock = AsyncMock(
        return_value=updated_user
    )

    with patch(
        "app.api.users.update_user_role",
        new=update_mock,
    ):
        response = client.patch(
            f"/users/{user_id}/role",
            json={
                "role": "operator",
            },
        )

    assert response.status_code == 200

    assert (
        response.json()["role"]
        == "operator"
    )

    update_mock.assert_awaited_once()


def test_missing_user_role_update_returns_404(
    authenticated_admin,
) -> None:
    user_id = uuid4()

    with patch(
        "app.api.users.update_user_role",
        new=AsyncMock(
            return_value=None
        ),
    ):
        response = client.patch(
            f"/users/{user_id}/role",
            json={
                "role": "operator",
            },
        )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "User not found."
    }


def test_admin_cannot_demote_self(
    authenticated_admin,
) -> None:
    response = client.patch(
        (
            f"/users/"
            f"{authenticated_admin.id}"
            "/role"
        ),
        json={
            "role": "viewer",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "You cannot remove your own "
            "administrator role."
        )
    }


# =================================================
# Account activation / deactivation
# =================================================


def test_admin_can_deactivate_user(
    authenticated_admin,
) -> None:
    user_id = uuid4()

    updated_user = User(
        id=user_id,
        email=(
            "operator@chargeops.local"
        ),
        password_hash=(
            "test-password-hash"
        ),
        role="operator",
        is_active=False,
        created_at=datetime.now(
            timezone.utc
        ),
    )

    update_mock = AsyncMock(
        return_value=updated_user
    )

    with patch(
        "app.api.users.update_user_status",
        new=update_mock,
    ):
        response = client.patch(
            f"/users/{user_id}/status",
            json={
                "is_active": False,
            },
        )

    assert response.status_code == 200

    assert (
        response.json()[
            "is_active"
        ]
        is False
    )

    update_mock.assert_awaited_once()


def test_missing_user_status_update_returns_404(
    authenticated_admin,
) -> None:
    user_id = uuid4()

    with patch(
        "app.api.users.update_user_status",
        new=AsyncMock(
            return_value=None
        ),
    ):
        response = client.patch(
            f"/users/{user_id}/status",
            json={
                "is_active": False,
            },
        )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "User not found."
    }


def test_admin_cannot_deactivate_self(
    authenticated_admin,
) -> None:
    response = client.patch(
        (
            f"/users/"
            f"{authenticated_admin.id}"
            "/status"
        ),
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "You cannot deactivate "
            "your own account."
        )
    }