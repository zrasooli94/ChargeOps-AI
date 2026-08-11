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
from jwt.exceptions import (
    InvalidTokenError,
)
from pwdlib import PasswordHash
from pydantic import (
    ValidationError,
)

from app.core.config import settings
from app.schemas.auth import (
    TokenClaims,
    UserRole,
)

password_hasher = (
    PasswordHash.recommended()
)


class TokenValidationError(
    Exception
):
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


def _get_jwt_secret(
) -> str:
    secret = (
        settings.jwt_secret_key
        .strip()
    )

    secret_bytes = (
        secret.encode(
            "utf-8"
        )
    )

    if len(secret_bytes) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must contain "
            "at least 32 bytes."
        )

    return secret


def _get_jwt_issuer(
) -> str:
    issuer = (
        settings.jwt_issuer
        .strip()
    )

    if not issuer:
        raise RuntimeError(
            "JWT_ISSUER must be configured."
        )

    return issuer


def _get_jwt_audience(
) -> str:
    audience = (
        settings.jwt_audience
        .strip()
    )

    if not audience:
        raise RuntimeError(
            "JWT_AUDIENCE must be configured."
        )

    return audience


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

    configured_lifetime = timedelta(
        minutes=(
            settings
            .access_token_expire_minutes
        )
    )

    lifetime = (
        expires_delta
        if expires_delta is not None
        else configured_lifetime
    )

    if lifetime > configured_lifetime:
        raise ValueError(
            "Access token lifetime cannot "
            "exceed configured maximum."
        )

    expiration = (
        now + lifetime
    )

    payload = {
        "sub": str(
            user_id
        ),
        "role": role,
        "iss": (
            _get_jwt_issuer()
        ),
        "aud": (
            _get_jwt_audience()
        ),
        "iat": now,
        "nbf": now,
        "exp": expiration,
        "jti": str(
            uuid4()
        ),
        "token_use": "access",
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
                settings.jwt_algorithm
            ],
            issuer=(
                _get_jwt_issuer()
            ),
            audience=(
                _get_jwt_audience()
            ),
            leeway=(
                settings
                .jwt_leeway_seconds
            ),
            options={
                "require": [
                    "sub",
                    "role",
                    "iss",
                    "aud",
                    "iat",
                    "nbf",
                    "exp",
                    "jti",
                    "token_use",
                ],
                "strict_aud": True,
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