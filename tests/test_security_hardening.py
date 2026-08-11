import logging
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import (
    TestClient,
)

from app.core.config import settings
from app.core.error_handling import (
    create_request_id,
    is_sensitive_action,
    register_error_handling,
)
from app.core.production_security import (
    ProductionConfigurationError,
    validate_production_security,
)
from app.core.security_audit import (
    log_security_event,
)


def secure_production_settings():
    return settings.model_copy(
        update={
            "app_environment": (
                "production"
            ),
            "jwt_secret_key": (
                "x" * 32
            ),
            "openai_api_key": (
                "test-openai-key"
            ),
            "security_enable_hsts": (
                True
            ),
            "cors_allowed_origins": (
                "https://chargeops.example.com"
            ),
            "database_url": (
                "postgresql+psycopg://"
                "chargeops_prod:"
                "strong-password@"
                "postgres.internal:5432/"
                "chargeops"
            ),
        }
    )


def test_secure_production_configuration_passes(
) -> None:
    config = (
        secure_production_settings()
    )

    validate_production_security(
        config
    )


def test_unsafe_production_configuration_fails(
) -> None:
    config = (
        secure_production_settings()
        .model_copy(
            update={
                "jwt_secret_key": (
                    "short"
                ),
                "security_enable_hsts": (
                    False
                ),
                "cors_allowed_origins": (
                    "http://localhost:8501"
                ),
                "database_url": (
                    "postgresql+psycopg://"
                    "chargeops:chargeops@"
                    "localhost:5432/"
                    "chargeops"
                ),
            }
        )
    )

    try:
        validate_production_security(
            config
        )

    except ProductionConfigurationError as error:
        message = str(
            error
        )

        assert (
            "JWT secret"
            in message
        )

        assert (
            "HSTS"
            in message
        )

        assert (
            "HTTPS"
            in message
        )

        assert (
            "localhost"
            in message.lower()
        )

    else:
        raise AssertionError(
            "Unsafe production configuration "
            "was accepted."
        )


def test_development_configuration_does_not_require_production_values(
) -> None:
    config = settings.model_copy(
        update={
            "app_environment": (
                "development"
            ),
            "jwt_secret_key": "",
            "security_enable_hsts": (
                False
            ),
        }
    )

    validate_production_security(
        config
    )


def test_security_audit_does_not_log_raw_email(
    caplog,
) -> None:
    with caplog.at_level(
        logging.INFO,
        logger="chargeops.security",
    ):
        log_security_event(
            event=(
                "auth.login.success"
            ),
            outcome="success",
            email=(
                "Private.User@example.com"
            ),
        )

    assert (
        "Private.User@example.com"
        not in caplog.text
    )

    assert (
        "email_fingerprint"
        in caplog.text
    )


def test_request_id_is_valid_uuid(
) -> None:
    request_id = (
        create_request_id(
            None
        )
    )

    assert (
        str(
            UUID(
                request_id
            )
        )
        == request_id
    )


def test_valid_supplied_request_id_is_preserved(
) -> None:
    supplied = (
        "550e8400-e29b-41d4-"
        "a716-446655440000"
    )

    assert (
        create_request_id(
            supplied
        )
        == supplied
    )


def test_invalid_request_id_is_replaced(
) -> None:
    request_id = (
        create_request_id(
            "forged\nlog-entry"
        )
    )

    assert (
        request_id
        != "forged\nlog-entry"
    )

    UUID(
        request_id
    )


def test_sensitive_action_detection(
) -> None:
    assert is_sensitive_action(
        "PATCH",
        "/users/123/role",
    )

    assert is_sensitive_action(
        "DELETE",
        "/knowledge/documents/123",
    )

    assert is_sensitive_action(
        "POST",
        "/agent/resume",
    )

    assert not is_sensitive_action(
        "GET",
        "/health",
    )


def test_unhandled_errors_are_sanitized(
) -> None:
    test_app = FastAPI()

    register_error_handling(
        test_app
    )

    @test_app.get(
        "/boom"
    )
    def boom():
        raise RuntimeError(
            "database password="
            "super-secret-value"
        )

    client = TestClient(
        test_app,
        raise_server_exceptions=False,
    )

    response = client.get(
        "/boom"
    )

    assert (
        response.status_code
        == 500
    )

    payload = response.json()

    assert (
        payload["detail"]
        == "Internal server error."
    )

    assert (
        "super-secret-value"
        not in response.text
    )

    request_id = payload[
        "request_id"
    ]

    UUID(
        request_id
    )

    assert (
        response.headers[
            "x-request-id"
        ]
        == request_id
    )


def test_normal_responses_receive_request_id(
) -> None:
    test_app = FastAPI()

    register_error_handling(
        test_app
    )

    @test_app.get(
        "/ok"
    )
    def ok():
        return {
            "status": "ok"
        }

    client = TestClient(
        test_app
    )

    response = client.get(
        "/ok"
    )

    assert (
        response.status_code
        == 200
    )

    UUID(
        response.headers[
            "x-request-id"
        ]
    )