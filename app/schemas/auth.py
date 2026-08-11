from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
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
    iat: datetime
    exp: datetime


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
        min_length=12,
        max_length=128,
    )

    role: UserRole = "viewer"


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserStatusUpdate(BaseModel):
    is_active: bool