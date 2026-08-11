from fastapi.testclient import (
    TestClient,
)

from app.core.config import settings
from app.main import app

client = TestClient(
    app
)


TRUSTED_ORIGIN = (
    "http://localhost:8501"
)

SECOND_TRUSTED_ORIGIN = (
    "http://127.0.0.1:8501"
)

UNTRUSTED_ORIGIN = (
    "https://evil.example"
)


def test_trusted_origin_receives_cors_header(
) -> None:
    response = client.get(
        "/health",
        headers={
            "Origin": TRUSTED_ORIGIN,
        },
    )

    assert response.status_code == 200

    assert (
        response.headers[
            "access-control-allow-origin"
        ]
        == TRUSTED_ORIGIN
    )


def test_second_trusted_origin_is_allowed(
) -> None:
    response = client.get(
        "/health",
        headers={
            "Origin": (
                SECOND_TRUSTED_ORIGIN
            ),
        },
    )

    assert response.status_code == 200

    assert (
        response.headers[
            "access-control-allow-origin"
        ]
        == SECOND_TRUSTED_ORIGIN
    )


def test_untrusted_origin_does_not_receive_cors_permission(
) -> None:
    response = client.get(
        "/health",
        headers={
            "Origin": (
                UNTRUSTED_ORIGIN
            ),
        },
    )

    assert response.status_code == 200

    assert (
        "access-control-allow-origin"
        not in response.headers
    )


def test_trusted_preflight_request_is_allowed(
) -> None:
    response = client.options(
        "/auth/login",
        headers={
            "Origin": TRUSTED_ORIGIN,
            (
                "Access-Control-"
                "Request-Method"
            ): "POST",
            (
                "Access-Control-"
                "Request-Headers"
            ): (
                "content-type"
            ),
        },
    )

    assert response.status_code == 200

    assert (
        response.headers[
            "access-control-allow-origin"
        ]
        == TRUSTED_ORIGIN
    )

    allowed_methods = (
        response.headers[
            "access-control-allow-methods"
        ]
    )

    assert "POST" in allowed_methods


def test_authorization_header_is_allowed_in_preflight(
) -> None:
    response = client.options(
        "/stations",
        headers={
            "Origin": TRUSTED_ORIGIN,
            (
                "Access-Control-"
                "Request-Method"
            ): "GET",
            (
                "Access-Control-"
                "Request-Headers"
            ): (
                "authorization"
            ),
        },
    )

    assert response.status_code == 200

    assert (
        response.headers[
            "access-control-allow-origin"
        ]
        == TRUSTED_ORIGIN
    )


def test_untrusted_preflight_is_rejected(
) -> None:
    response = client.options(
        "/auth/login",
        headers={
            "Origin": (
                UNTRUSTED_ORIGIN
            ),
            (
                "Access-Control-"
                "Request-Method"
            ): "POST",
            (
                "Access-Control-"
                "Request-Headers"
            ): (
                "content-type"
            ),
        },
    )

    assert response.status_code == 400

    assert (
        "access-control-allow-origin"
        not in response.headers
    )


def test_cors_configuration_has_no_wildcard(
) -> None:
    assert (
        "*"
        not in (
            settings
            .cors_allowed_origins_list
        )
    )


def test_credentials_are_not_enabled(
) -> None:
    response = client.get(
        "/health",
        headers={
            "Origin": TRUSTED_ORIGIN,
        },
    )

    assert (
        "access-control-allow-credentials"
        not in response.headers
    )