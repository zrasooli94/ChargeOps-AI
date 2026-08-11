from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import (
    UUID,
    uuid4,
)

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    TokenValidationError,
    create_access_token,
    decode_access_token,
)


@pytest.fixture
def jwt_settings(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        "x" * 32,
    )

    monkeypatch.setattr(
        settings,
        "jwt_issuer",
        "chargeops-ai",
    )

    monkeypatch.setattr(
        settings,
        "jwt_audience",
        "chargeops-api",
    )

    monkeypatch.setattr(
        settings,
        "jwt_leeway_seconds",
        30,
    )

    monkeypatch.setattr(
        settings,
        "access_token_expire_minutes",
        30,
    )


def test_access_token_contains_hardened_claims(
    jwt_settings,
) -> None:
    user_id = uuid4()

    token = create_access_token(
        user_id=user_id,
        role="operator",
    )

    claims = decode_access_token(
        token
    )

    assert claims.sub == user_id
    assert claims.role == "operator"

    assert (
        claims.iss
        == "chargeops-ai"
    )

    assert (
        claims.aud
        == "chargeops-api"
    )

    assert (
        claims.token_use
        == "access"
    )

    assert isinstance(
        claims.jti,
        UUID,
    )

    assert (
        claims.exp
        > claims.iat
    )

    assert (
        claims.nbf
        >= claims.iat
    )


def test_wrong_issuer_is_rejected(
    jwt_settings,
    monkeypatch,
) -> None:
    token = create_access_token(
        user_id=uuid4(),
        role="viewer",
    )

    monkeypatch.setattr(
        settings,
        "jwt_issuer",
        "another-service",
    )

    with pytest.raises(
        TokenValidationError
    ):
        decode_access_token(
            token
        )


def test_wrong_audience_is_rejected(
    jwt_settings,
    monkeypatch,
) -> None:
    token = create_access_token(
        user_id=uuid4(),
        role="viewer",
    )

    monkeypatch.setattr(
        settings,
        "jwt_audience",
        "another-api",
    )

    with pytest.raises(
        TokenValidationError
    ):
        decode_access_token(
            token
        )


def test_refresh_purpose_token_is_rejected(
    jwt_settings,
) -> None:
    now = datetime.now(
        timezone.utc
    )

    payload = {
        "sub": str(
            uuid4()
        ),
        "role": "viewer",
        "iss": "chargeops-ai",
        "aud": "chargeops-api",
        "iat": now,
        "nbf": now,
        "exp": (
            now
            + timedelta(
                minutes=30
            )
        ),
        "jti": str(
            uuid4()
        ),
        "token_use": "refresh",
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm="HS256",
    )

    with pytest.raises(
        TokenValidationError
    ):
        decode_access_token(
            token
        )


def test_missing_required_claim_is_rejected(
    jwt_settings,
) -> None:
    now = datetime.now(
        timezone.utc
    )

    payload = {
        "sub": str(
            uuid4()
        ),
        "role": "viewer",
        "iss": "chargeops-ai",
        "aud": "chargeops-api",
        "iat": now,
        "nbf": now,
        "exp": (
            now
            + timedelta(
                minutes=30
            )
        ),
        # jti intentionally missing
        "token_use": "access",
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm="HS256",
    )

    with pytest.raises(
        TokenValidationError
    ):
        decode_access_token(
            token
        )


def test_access_token_cannot_exceed_configured_lifetime(
    jwt_settings,
) -> None:
    with pytest.raises(
        ValueError,
        match="lifetime",
    ):
        create_access_token(
            user_id=uuid4(),
            role="viewer",
            expires_delta=timedelta(
                minutes=31
            ),
        )