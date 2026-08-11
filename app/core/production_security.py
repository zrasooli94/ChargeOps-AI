from app.core.config import (
    Settings,
)


class ProductionConfigurationError(
    RuntimeError
):
    """Raised when production security is unsafe."""


def validate_production_security(
    config: Settings,
) -> None:
    """
    Fail fast when ChargeOps starts with an
    unsafe production configuration.

    Development and test environments are not
    affected.
    """

    if (
        config.app_environment
        != "production"
    ):
        return

    problems: list[str] = []

    jwt_secret = (
        config.jwt_secret_key
        .strip()
    )

    if (
        len(
            jwt_secret.encode(
                "utf-8"
            )
        )
        < 32
    ):
        problems.append(
            "JWT secret is missing "
            "or shorter than 32 bytes."
        )

    openai_key = (
        config.openai_api_key
        or ""
    )

    if not openai_key.strip():
        problems.append(
            "OpenAI API key is missing."
        )

    if not config.security_enable_hsts:
        problems.append(
            "HSTS must be enabled."
        )

    origins = (
        config
        .cors_allowed_origins_list
    )

    if not origins:
        problems.append(
            "At least one production "
            "CORS origin is required."
        )

    for origin in origins:
        normalized_origin = (
            origin.lower()
        )

        if (
            normalized_origin
            .startswith("http://")
        ):
            problems.append(
                "Production CORS origins "
                "must use HTTPS."
            )

        if (
            "localhost"
            in normalized_origin
            or "127.0.0.1"
            in normalized_origin
        ):
            problems.append(
                "Localhost CORS origins "
                "are not allowed in production."
            )

    database_url = (
        config.database_url
        .lower()
    )

    if (
        "localhost"
        in database_url
    ):
        problems.append(
            "Production database must "
            "not use localhost."
        )

    if (
        "chargeops:chargeops@"
        in database_url
    ):
        problems.append(
            "Default database credentials "
            "are not allowed in production."
        )

    if problems:
        message = (
            "Unsafe ChargeOps production "
            "configuration:\n- "
            + "\n- ".join(
                problems
            )
        )

        raise ProductionConfigurationError(
            message
        )