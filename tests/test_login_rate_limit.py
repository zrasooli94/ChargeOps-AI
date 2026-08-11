from types import SimpleNamespace
from unittest.mock import (
    AsyncMock,
    patch,
)
from uuid import uuid4

import pytest
from fastapi.testclient import (
    TestClient,
)

from app.core.config import settings
from app.core.database import get_db
from app.core.login_rate_limiter import (
    LoginRateLimiter,
    login_rate_limiter,
)
from app.main import app

client = TestClient(
    app
)


@pytest.fixture(
    autouse=True
)
def reset_login_rate_limiter():
    login_rate_limiter.reset()

    yield

    login_rate_limiter.reset()


@pytest.fixture
def isolated_login_database():
    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[
        get_db
    ] = override_get_db

    yield

    app.dependency_overrides.pop(
        get_db,
        None,
    )


def test_repeated_failed_login_is_throttled(
    monkeypatch,
    isolated_login_database,
) -> None:
    monkeypatch.setattr(
        settings,
        "login_rate_limit_account_attempts",
        2,
    )

    monkeypatch.setattr(
        settings,
        "login_rate_limit_ip_attempts",
        100,
    )

    with patch(
        "app.api.auth.authenticate_user",
        new=AsyncMock(
            return_value=None
        ),
    ):
        first = client.post(
            "/auth/login",
            data={
                "username": (
                    "viewer@chargeops.local"
                ),
                "password": "wrong",
            },
        )

        second = client.post(
            "/auth/login",
            data={
                "username": (
                    "viewer@chargeops.local"
                ),
                "password": "wrong",
            },
        )

        blocked = client.post(
            "/auth/login",
            data={
                "username": (
                    "viewer@chargeops.local"
                ),
                "password": "wrong",
            },
        )

    assert first.status_code == 401
    assert second.status_code == 401

    assert (
        blocked.status_code
        == 429
    )

    assert (
        blocked.json()["detail"]
        == (
            "Too many login attempts. "
            "Try again later."
        )
    )

    retry_after = int(
        blocked.headers[
            "Retry-After"
        ]
    )

    assert retry_after >= 1


def test_successful_login_clears_account_bucket(
    monkeypatch,
    isolated_login_database,
) -> None:
    monkeypatch.setattr(
        settings,
        "login_rate_limit_account_attempts",
        2,
    )

    monkeypatch.setattr(
        settings,
        "login_rate_limit_ip_attempts",
        100,
    )

    fake_user = SimpleNamespace(
        id=uuid4(),
        role="viewer",
    )

    authenticate_mock = AsyncMock(
        side_effect=[
            None,
            fake_user,
            None,
            None,
        ]
    )

    with (
        patch(
            "app.api.auth.authenticate_user",
            new=authenticate_mock,
        ),
        patch(
            "app.api.auth.create_access_token",
            return_value="test-token",
        ),
    ):
        first_failure = client.post(
            "/auth/login",
            data={
                "username": (
                    "viewer@chargeops.local"
                ),
                "password": "wrong",
            },
        )

        success = client.post(
            "/auth/login",
            data={
                "username": (
                    "viewer@chargeops.local"
                ),
                "password": "correct",
            },
        )

        failure_after_success = (
            client.post(
                "/auth/login",
                data={
                    "username": (
                        "viewer@chargeops.local"
                    ),
                    "password": "wrong",
                },
            )
        )

        second_failure_after_success = (
            client.post(
                "/auth/login",
                data={
                    "username": (
                        "viewer@chargeops.local"
                    ),
                    "password": "wrong",
                },
            )
        )

        blocked = client.post(
            "/auth/login",
            data={
                "username": (
                    "viewer@chargeops.local"
                ),
                "password": "wrong",
            },
        )

    assert (
        first_failure.status_code
        == 401
    )

    assert success.status_code == 200

    assert (
        failure_after_success.status_code
        == 401
    )

    assert (
        second_failure_after_success.status_code
        == 401
    )

    assert blocked.status_code == 429


def test_ip_limit_blocks_account_spraying(
) -> None:
    current_time = [
        100.0
    ]

    limiter = LoginRateLimiter(
        clock=lambda: (
            current_time[0]
        )
    )

    for index in range(3):
        retry_after = (
            limiter.get_retry_after(
                client_ip="192.0.2.10",
                email=(
                    f"user{index}"
                    "@chargeops.local"
                ),
                ip_attempt_limit=3,
                account_attempt_limit=5,
                window_seconds=60,
            )
        )

        assert retry_after is None

        limiter.record_failure(
            client_ip="192.0.2.10",
            email=(
                f"user{index}"
                "@chargeops.local"
            ),
            window_seconds=60,
        )

    retry_after = (
        limiter.get_retry_after(
            client_ip="192.0.2.10",
            email=(
                "another"
                "@chargeops.local"
            ),
            ip_attempt_limit=3,
            account_attempt_limit=5,
            window_seconds=60,
        )
    )

    assert retry_after == 60

    current_time[0] += 61

    retry_after = (
        limiter.get_retry_after(
            client_ip="192.0.2.10",
            email=(
                "another"
                "@chargeops.local"
            ),
            ip_attempt_limit=3,
            account_attempt_limit=5,
            window_seconds=60,
        )
    )

    assert retry_after is None