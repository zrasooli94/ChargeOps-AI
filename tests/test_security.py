from datetime import timedelta
from uuid import uuid4

import pytest

from app.core.config import settings
from app.core.security import (
    TokenValidationError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing() -> None:
    password = (
        "ChargeOps-Test-Password-123!"
    )

    hashed = hash_password(
        password
    )

    assert hashed != password

    assert verify_password(
        password,
        hashed,
    )

    assert not verify_password(
        "wrong-password",
        hashed,
    )


def test_access_token_round_trip() -> None:
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
    assert claims.exp > claims.iat


def test_expired_access_token_is_rejected(
) -> None:
    user_id = uuid4()

    token = create_access_token(
        user_id=user_id,
        role="viewer",
        expires_delta=timedelta(
            seconds=(
                -settings.jwt_leeway_seconds
                - 1
            )
        ),
    )

    with pytest.raises(
        TokenValidationError
    ):
        decode_access_token(
            token
        )


def test_modified_access_token_is_rejected(
) -> None:
    user_id = uuid4()

    token = create_access_token(
        user_id=user_id,
        role="admin",
    )

    header, payload, signature = (
        token.split(".")
    )

    modified_signature = (
        (
            "A"
            if signature[0] != "A"
            else "B"
        )
        + signature[1:]
    )

    modified_token = (
        f"{header}."
        f"{payload}."
        f"{modified_signature}"
    )

    with pytest.raises(
        TokenValidationError
    ):
        decode_access_token(
            modified_token
        )