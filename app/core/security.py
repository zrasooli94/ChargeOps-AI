from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.auth import (
    TokenClaims,
    UserRole,
)

password_hasher = (
    PasswordHash.recommended()
)


class TokenValidationError(Exception):
    """Raised when an access token is invalid."""


def hash_password(
    password: str,
) -> str:
    return password_hasher.hash(
        password
    )


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hasher.verify(
        plain_password,
        hashed_password,
    )


def _get_jwt_secret() -> str:
    secret = (
        settings.jwt_secret_key
        .strip()
    )

    if len(secret) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be "
            "configured with a strong "
            "secret before authentication "
            "can be used."
        )

    return secret


def create_access_token(
    user_id: UUID,
    role: UserRole,
    expires_delta: (
        timedelta | None
    ) = None,
) -> str:
    now = datetime.now(
        timezone.utc
    )

    expiration = (
        now + expires_delta
        if expires_delta
        is not None
        else (
            now
            + timedelta(
                minutes=(
                    settings
                    .access_token_expire_minutes
                )
            )
        )
    )

    payload = {
        "sub": str(
            user_id
        ),
        "role": role,
        "iat": now,
        "exp": expiration,
    }

    return jwt.encode(
        payload,
        _get_jwt_secret(),
        algorithm=(
            settings.jwt_algorithm
        ),
    )


def decode_access_token(
    token: str,
) -> TokenClaims:
    try:
        payload = jwt.decode(
            token,
            _get_jwt_secret(),
            algorithms=[
                settings.jwt_algorithm,
            ],
            options={
                "require": [
                    "sub",
                    "role",
                    "iat",
                    "exp",
                ],
            },
        )

        return (
            TokenClaims
            .model_validate(
                payload
            )
        )

    except (
        InvalidTokenError,
        ValidationError,
        ValueError,
        TypeError,
    ) as error:
        raise TokenValidationError(
            "Access token is invalid "
            "or expired."
        ) from error