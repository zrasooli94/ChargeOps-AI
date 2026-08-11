import argparse
import asyncio
from getpass import getpass

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

load_dotenv()

from app.core.config import settings
from app.schemas.auth import UserRole
from app.services.auth_service import (
    UserAlreadyExistsError,
    create_user,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a ChargeOps user."
        )
    )

    parser.add_argument(
        "--email",
        required=True,
        help="User email address.",
    )

    parser.add_argument(
        "--role",
        required=True,
        choices=[
            "viewer",
            "operator",
            "admin",
        ],
        help="ChargeOps user role.",
    )

    return parser.parse_args()


async def create_chargeops_user(
    email: str,
    password: str,
    role: UserRole,
) -> None:
    engine = create_async_engine(
        settings.database_url
    )

    session_factory = (
        async_sessionmaker(
            bind=engine,
            expire_on_commit=False,
        )
    )

    try:
        async with (
            session_factory()
            as session
        ):
            try:
                user = await create_user(
                    session=session,
                    email=email,
                    password=password,
                    role=role,
                )

            except UserAlreadyExistsError:
                print()
                print(
                    "A user with that "
                    "email already exists."
                )
                return

            print()
            print("User created.")
            print(
                "Email:",
                user.email,
            )
            print(
                "Role:",
                user.role,
            )
            print(
                "User ID:",
                user.id,
            )

    finally:
        await engine.dispose()


async def main() -> None:
    args = parse_args()

    password = getpass(
        "Password: "
    )

    if len(password) < 12:
        raise ValueError(
            "Password must contain "
            "at least 12 characters."
        )

    confirmation = getpass(
        "Confirm password: "
    )

    if password != confirmation:
        raise ValueError(
            "Passwords do not match."
        )

    role: UserRole = args.role

    await create_chargeops_user(
        email=args.email,
        password=password,
        role=role,
    )


if __name__ == "__main__":
    asyncio.run(
        main()
    )