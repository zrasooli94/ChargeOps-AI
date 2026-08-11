from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.core.password_policy import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    validate_password_strength,
)

UserRole = Literal[
    "viewer",
    "operator",
    "admin",
]


# =================================================
# JWT / authentication
# =================================================


class TokenClaims(BaseModel):
    sub: UUID
    role: UserRole

    iss: str
    aud: str

    iat: datetime
    nbf: datetime
    exp: datetime

    jti: UUID

    token_use: Literal[
        "access"
    ]


class AccessToken(BaseModel):
    access_token: str

    token_type: Literal[
        "bearer"
    ] = "bearer"


# =================================================
# User responses
# =================================================


class UserRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime


# =================================================
# Admin user management
# =================================================


class UserCreateRequest(BaseModel):
    email: str = Field(
        min_length=3,
        max_length=320,
    )

    password: str = Field(
        min_length=(
            MIN_PASSWORD_LENGTH
        ),
        max_length=(
            MAX_PASSWORD_LENGTH
        ),
    )

    role: UserRole = "viewer"

    @model_validator(
        mode="after"
    )
    def enforce_password_policy(
        self,
    ) -> "UserCreateRequest":
        validate_password_strength(
            self.password,
            email=self.email,
        )

        return self


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserStatusUpdate(BaseModel):
    is_active: bool