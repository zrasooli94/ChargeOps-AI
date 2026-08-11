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


def normalize_email(
    email: str,
) -> str:
    return (
        email
        .strip()
        .lower()
    )


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


async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    user = await get_user_by_email(
        session=session,
        email=email,
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user