from fastapi import (
    FastAPI,
)
from fastapi.testclient import (
    TestClient,
)

from app.core.security_headers import (
    SecurityHeadersMiddleware,
)
from app.main import app

client = TestClient(
    app
)


def test_security_headers_are_present(
) -> None:
    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert (
        response.headers[
            "x-content-type-options"
        ]
        == "nosniff"
    )

    assert (
        response.headers[
            "x-frame-options"
        ]
        == "DENY"
    )

    assert (
        response.headers[
            "referrer-policy"
        ]
        == "no-referrer"
    )

    assert (
        response.headers[
            "permissions-policy"
        ]
        == (
            "camera=(), "
            "microphone=(), "
            "geolocation=()"
        )
    )

    assert (
        response.headers[
            "cache-control"
        ]
        == "no-store"
    )


def test_content_security_policy_is_present(
) -> None:
    response = client.get(
        "/health"
    )

    policy = response.headers[
        "content-security-policy"
    ]

    assert (
        "frame-ancestors 'none'"
        in policy
    )

    assert (
        "object-src 'none'"
        in policy
    )

    assert (
        "base-uri 'none'"
        in policy
    )


def test_security_headers_are_present_on_404(
) -> None:
    response = client.get(
        "/route-that-does-not-exist"
    )

    assert response.status_code == 404

    assert (
        response.headers[
            "x-content-type-options"
        ]
        == "nosniff"
    )

    assert (
        response.headers[
            "x-frame-options"
        ]
        == "DENY"
    )


def test_hsts_is_disabled_in_development(
) -> None:
    response = client.get(
        "/health"
    )

    assert (
        "strict-transport-security"
        not in response.headers
    )


def test_hsts_can_be_enabled_for_https_deployment(
) -> None:
    test_app = FastAPI()

    test_app.add_middleware(
        SecurityHeadersMiddleware,
        enable_hsts=True,
        hsts_max_age=31536000,
    )

    @test_app.get(
        "/test"
    )
    def test_endpoint(
    ) -> dict[str, str]:
        return {
            "status": "ok"
        }

    test_client = TestClient(
        test_app
    )

    response = test_client.get(
        "/test"
    )

    assert (
        response.headers[
            "strict-transport-security"
        ]
        == "max-age=31536000"
    )


def test_deprecated_xss_protection_header_is_not_added(
) -> None:
    response = client.get(
        "/health"
    )

    assert (
        "x-xss-protection"
        not in response.headers
    )