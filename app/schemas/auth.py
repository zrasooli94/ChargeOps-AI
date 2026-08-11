from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
)

UserRole = Literal[
    "viewer",
    "operator",
    "admin",
]


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


class UserRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime