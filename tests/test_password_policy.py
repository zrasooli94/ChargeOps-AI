import asyncio
from unittest.mock import (
    AsyncMock,
    patch,
)

import pytest

from app.core.password_policy import (
    WeakPasswordError,
    validate_password_strength,
)
from app.services.auth_service import (
    create_user,
)


def test_long_passphrase_is_allowed(
) -> None:
    validate_password_strength(
        "orbit lantern meadow copper"
    )


def test_password_does_not_require_composition_rules(
) -> None:
    validate_password_strength(
        "this is a long lowercase passphrase"
    )


def test_short_password_is_rejected(
) -> None:
    with pytest.raises(
        WeakPasswordError,
        match="at least 15",
    ):
        validate_password_strength(
            "too-short"
        )


def test_excessively_long_password_is_rejected(
) -> None:
    with pytest.raises(
        WeakPasswordError,
        match="no more than 128",
    ):
        validate_password_strength(
            "a" * 129
        )


def test_common_password_is_rejected(
) -> None:
    with pytest.raises(
        WeakPasswordError,
        match="less common",
    ):
        validate_password_strength(
            "passwordpassword"
        )


def test_common_password_check_is_case_insensitive(
) -> None:
    with pytest.raises(
        WeakPasswordError,
        match="less common",
    ):
        validate_password_strength(
            "PasswordPassword"
        )


def test_chargeops_specific_password_is_rejected(
) -> None:
    with pytest.raises(
        WeakPasswordError,
        match="less common",
    ):
        validate_password_strength(
            "chargeopschargeops"
        )


def test_email_username_as_password_is_rejected(
) -> None:
    with pytest.raises(
        WeakPasswordError,
        match="email address or username",
    ):
        validate_password_strength(
            "administratoraccount",
            email=(
                "administratoraccount"
                "@chargeops.local"
            ),
        )


def test_create_user_service_enforces_policy(
) -> None:
    async def run_test() -> None:
        session = AsyncMock()

        lookup_mock = AsyncMock()

        with patch(
            "app.services.auth_service.get_user_by_email",
            new=lookup_mock,
        ), pytest.raises(
            WeakPasswordError
        ):
            await create_user(
                session=session,
                email=(
                    "newuser@chargeops.local"
                ),
                password="too-short",
                role="viewer",
            )

        lookup_mock.assert_not_awaited()

    asyncio.run(
        run_test()
    )