from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.security import (
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import UserRole


class UserAlreadyExistsError(
    Exception
):
    """Raised when an email is already registered."""


# =================================================
# Authentication timing protection
# =================================================
#
# Unknown accounts must still perform an expensive
# password verification operation.
#
# This prevents the authentication path from
# immediately returning when an email does not
# exist, which would create a useful timing
# difference for account enumeration.
#
# This value is not a real credential and does not
# need to be secret.
# =================================================


DUMMY_PASSWORD_HASH = hash_password(
    "chargeops-authentication-timing-dummy-password"
)


def normalize_email(
    email: str,
) -> str:
    return (
        email
        .strip()
        .lower()
    )


# =================================================
# User lookup
# =================================================


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    normalized_email = (
        normalize_email(
            email
        )
    )

    result = await session.execute(
        select(User).where(
            User.email
            == normalized_email
        )
    )

    return (
        result
        .scalar_one_or_none()
    )


async def get_user_by_id(
    session: AsyncSession,
    user_id: UUID,
) -> User | None:
    result = await session.execute(
        select(User).where(
            User.id == user_id
        )
    )

    return (
        result
        .scalar_one_or_none()
    )


# =================================================
# User listing
# =================================================


async def list_users(
    session: AsyncSession,
) -> list[User]:
    result = await session.execute(
        select(User).order_by(
            User.created_at.asc()
        )
    )

    return list(
        result.scalars().all()
    )


# =================================================
# User creation
# =================================================


async def create_user(
    session: AsyncSession,
    email: str,
    password: str,
    role: UserRole = "viewer",
) -> User:
    normalized_email = (
        normalize_email(
            email
        )
    )

    existing_user = (
        await get_user_by_email(
            session=session,
            email=normalized_email,
        )
    )

    if existing_user is not None:
        raise UserAlreadyExistsError(
            "A user with this email "
            "already exists."
        )

    user = User(
        email=normalized_email,
        password_hash=(
            hash_password(
                password
            )
        ),
        role=role,
        is_active=True,
    )

    session.add(
        user
    )

    await session.commit()

    await session.refresh(
        user
    )

    return user


# =================================================
# Role management
# =================================================


async def update_user_role(
    session: AsyncSession,
    user_id: UUID,
    role: UserRole,
) -> User | None:
    user = await get_user_by_id(
        session=session,
        user_id=user_id,
    )

    if user is None:
        return None

    user.role = role

    await session.commit()

    await session.refresh(
        user
    )

    return user


# =================================================
# Account status management
# =================================================


async def update_user_status(
    session: AsyncSession,
    user_id: UUID,
    is_active: bool,
) -> User | None:
    user = await get_user_by_id(
        session=session,
        user_id=user_id,
    )

    if user is None:
        return None

    user.is_active = is_active

    await session.commit()

    await session.refresh(
        user
    )

    return user


# =================================================
# Authentication
# =================================================


async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    user = await get_user_by_email(
        session=session,
        email=email,
    )

    # Always perform password verification.
    #
    # Existing account:
    #     verify against the real password hash.
    #
    # Unknown account:
    #     verify against the dummy Argon2 hash.
    #
    # This avoids the fast "unknown user" return
    # path that could expose account existence
    # through response timing.

    password_hash = (
        user.password_hash
        if user is not None
        else DUMMY_PASSWORD_HASH
    )

    password_is_valid = (
        verify_password(
            password,
            password_hash,
        )
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    if not password_is_valid:
        return None

    return user