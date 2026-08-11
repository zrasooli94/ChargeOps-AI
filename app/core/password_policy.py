MIN_PASSWORD_LENGTH = 15
MAX_PASSWORD_LENGTH = 128


class WeakPasswordError(
    ValueError
):
    """Raised when a password fails policy validation."""


COMMON_PASSWORD_BLOCKLIST = frozenset(
    {
        "password",
        "password1",
        "password123",
        "password1234",
        "password12345",
        "password123456",
        "passwordpassword",
        "123456",
        "12345678",
        "123456789",
        "1234567890",
        "123456789012345",
        "111111",
        "000000",
        "abc123",
        "qwerty",
        "qwerty123",
        "qwertyqwertyqwerty",
        "letmein",
        "welcome",
        "welcome123",
        "admin",
        "administrator",
        "adminadminadminadmin",
        "changeme",
        "default",
        "iloveyou",
        "iloveyouiloveyou",
        "monkey",
        "dragon",
        "football",
        "baseball",
        "passw0rd",
        "p@ssw0rd",
        # ChargeOps-specific expected values
        "chargeops",
        "chargeopsai",
        "chargeops123",
        "chargeops123!",
        "chargeopschargeops",
    }
)


def validate_password_strength(
    password: str,
    *,
    email: str | None = None,
) -> None:
    """
    Validate a prospective ChargeOps password.

    The policy favors password length and a
    blocklist instead of composition rules.
    """

    if (
        len(password)
        < MIN_PASSWORD_LENGTH
    ):
        raise WeakPasswordError(
            "Password must be at least "
            f"{MIN_PASSWORD_LENGTH} characters."
        )

    if (
        len(password)
        > MAX_PASSWORD_LENGTH
    ):
        raise WeakPasswordError(
            "Password must be no more than "
            f"{MAX_PASSWORD_LENGTH} characters."
        )

    normalized_password = (
        password.casefold()
    )

    if (
        normalized_password
        in COMMON_PASSWORD_BLOCKLIST
    ):
        raise WeakPasswordError(
            "Choose a less common password "
            "or passphrase."
        )

    if email is None:
        return

    normalized_email = (
        email
        .strip()
        .casefold()
    )

    email_local_part = (
        normalized_email
        .split(
            "@",
            maxsplit=1,
        )[0]
    )

    if normalized_password in {
        normalized_email,
        email_local_part,
    }:
        raise WeakPasswordError(
            "Password must not match "
            "your email address or username."
        )