from unittest.mock import (
    AsyncMock,
    patch,
)

from fastapi.testclient import (
    TestClient,
)

from app.main import app

client = TestClient(
    app
)


def test_liveness_does_not_require_database(
) -> None:
    with patch(
        "app.api.health."
        "check_database_ready",
        new=AsyncMock(
            side_effect=AssertionError(
                "Database should not "
                "be called for liveness."
            )
        ),
    ):
        response = client.get(
            "/health/live"
        )

    assert response.status_code == 200

    assert (
        response.json()[
            "status"
        ]
        == "alive"
    )


def test_readiness_is_healthy_when_database_is_available(
) -> None:
    with patch(
        "app.api.health."
        "check_database_ready",
        new=AsyncMock(
            return_value=(
                True,
                "ok",
            )
        ),
    ):
        response = client.get(
            "/health/ready"
        )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ready",
        "database": "ok",
    }


def test_readiness_returns_503_when_database_is_unavailable(
) -> None:
    with patch(
        "app.api.health."
        "check_database_ready",
        new=AsyncMock(
            return_value=(
                False,
                "unavailable",
            )
        ),
    ):
        response = client.get(
            "/health/ready"
        )

    assert (
        response.status_code
        == 503
    )

    assert response.json() == {
        "status": "not_ready",
        "database": "unavailable",
        "reason": "unavailable",
    }