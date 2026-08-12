from app.core.config import Settings


def test_postgresql_database_url_is_normalized(
) -> None:
    settings = Settings(
        database_url=(
            "postgresql://"
            "user:password@db.example.com:5432/"
            "chargeops"
        )
    )

    assert settings.database_url == (
        "postgresql+psycopg://"
        "user:password@db.example.com:5432/"
        "chargeops"
    )


def test_legacy_postgres_database_url_is_normalized(
) -> None:
    settings = Settings(
        database_url=(
            "postgres://"
            "user:password@db.example.com:5432/"
            "chargeops"
        )
    )

    assert settings.database_url == (
        "postgresql+psycopg://"
        "user:password@db.example.com:5432/"
        "chargeops"
    )


def test_psycopg_database_url_is_not_modified(
) -> None:
    database_url = (
        "postgresql+psycopg://"
        "user:password@db.example.com:5432/"
        "chargeops"
    )

    settings = Settings(
        database_url=database_url
    )

    assert (
        settings.database_url
        == database_url
    )