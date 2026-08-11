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
from app.services.auth_service import (
    UserAlreadyExistsError,
    create_user,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create the initial "
            "ChargeOps administrator."
        )
    )

    parser.add_argument(
        "--email",
        type=str,
        default=None,
        help=(
            "Administrator email address."
        ),
    )

    return parser.parse_args()


async def create_admin(
    email: str,
    password: str,
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
                    role="admin",
                )

            except UserAlreadyExistsError:
                print()
                print(
                    "A user with that "
                    "email already exists."
                )
                return

            print()
            print(
                "Administrator created."
            )

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

    email = (
        args.email
        or input(
            "Admin email: "
        )
    )

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

    await create_admin(
        email=email,
        password=password,
    )


if __name__ == "__main__":
    asyncio.run(
        main()
    )