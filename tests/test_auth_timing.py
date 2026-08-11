import asyncio
from types import SimpleNamespace
from unittest.mock import (
    AsyncMock,
    patch,
)

from app.services.auth_service import (
    DUMMY_PASSWORD_HASH,
    authenticate_user,
)


def test_unknown_user_still_verifies_password(
) -> None:
    async def run_test() -> None:
        session = AsyncMock()

        with (
            patch(
                "app.services.auth_service.get_user_by_email",
                new=AsyncMock(
                    return_value=None
                ),
            ),
            patch(
                "app.services.auth_service.verify_password",
                return_value=False,
            ) as verify_mock,
        ):
            result = await authenticate_user(
                session=session,
                email=(
                    "missing@chargeops.local"
                ),
                password=(
                    "WrongPassword123!"
                ),
            )

        assert result is None

        verify_mock.assert_called_once_with(
            "WrongPassword123!",
            DUMMY_PASSWORD_HASH,
        )

    asyncio.run(
        run_test()
    )


def test_existing_user_verifies_real_hash(
) -> None:
    async def run_test() -> None:
        session = AsyncMock()

        user = SimpleNamespace(
            email=(
                "viewer@chargeops.local"
            ),
            password_hash=(
                "real-password-hash"
            ),
            role="viewer",
            is_active=True,
        )

        with (
            patch(
                "app.services.auth_service.get_user_by_email",
                new=AsyncMock(
                    return_value=user
                ),
            ),
            patch(
                "app.services.auth_service.verify_password",
                return_value=False,
            ) as verify_mock,
        ):
            result = await authenticate_user(
                session=session,
                email=(
                    "viewer@chargeops.local"
                ),
                password=(
                    "WrongPassword123!"
                ),
            )

        assert result is None

        verify_mock.assert_called_once_with(
            "WrongPassword123!",
            "real-password-hash",
        )

    asyncio.run(
        run_test()
    )


def test_inactive_user_still_verifies_password(
) -> None:
    async def run_test() -> None:
        session = AsyncMock()

        user = SimpleNamespace(
            email=(
                "disabled@chargeops.local"
            ),
            password_hash=(
                "disabled-user-hash"
            ),
            role="viewer",
            is_active=False,
        )

        with (
            patch(
                "app.services.auth_service.get_user_by_email",
                new=AsyncMock(
                    return_value=user
                ),
            ),
            patch(
                "app.services.auth_service.verify_password",
                return_value=True,
            ) as verify_mock,
        ):
            result = await authenticate_user(
                session=session,
                email=(
                    "disabled@chargeops.local"
                ),
                password=(
                    "CorrectPassword123!"
                ),
            )

        assert result is None

        verify_mock.assert_called_once_with(
            "CorrectPassword123!",
            "disabled-user-hash",
        )

    asyncio.run(
        run_test()
    )


def test_active_user_with_valid_password_authenticates(
) -> None:
    async def run_test() -> None:
        session = AsyncMock()

        user = SimpleNamespace(
            email=(
                "viewer@chargeops.local"
            ),
            password_hash=(
                "real-password-hash"
            ),
            role="viewer",
            is_active=True,
        )

        with (
            patch(
                "app.services.auth_service.get_user_by_email",
                new=AsyncMock(
                    return_value=user
                ),
            ),
            patch(
                "app.services.auth_service.verify_password",
                return_value=True,
            ) as verify_mock,
        ):
            result = await authenticate_user(
                session=session,
                email=(
                    "viewer@chargeops.local"
                ),
                password=(
                    "CorrectPassword123!"
                ),
            )

        assert result is user

        verify_mock.assert_called_once_with(
            "CorrectPassword123!",
            "real-password-hash",
        )

    asyncio.run(
        run_test()
    )