import asyncio
import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger(
    __name__
)


class Base(
    DeclarativeBase
):
    pass


engine = create_async_engine(
    settings.database_url,
    echo=False,

    # Validate connections as they leave
    # the pool so stale connections are
    # replaced before application use.
    pool_pre_ping=True,

    pool_size=(
        settings.database_pool_size
    ),

    max_overflow=(
        settings.database_max_overflow
    ),

    pool_timeout=(
        settings
        .database_pool_timeout_seconds
    ),

    pool_recycle=(
        settings
        .database_pool_recycle_seconds
    ),
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db(
) -> AsyncGenerator[
    AsyncSession,
    None,
]:
    async with AsyncSessionLocal() as session:
        try:
            yield session

        except Exception:
            if session.in_transaction():
                await session.rollback()

            raise


async def check_database_ready(
) -> tuple[
    bool,
    str,
]:
    """
    Verify that PostgreSQL can accept a lightweight
    query within the configured readiness timeout.

    Returns only safe status information suitable
    for health endpoints.
    """

    try:
        async with asyncio.timeout(
            settings
            .database_ready_timeout_seconds
        ):
            async with engine.connect() as connection:
                await connection.execute(
                    text(
                        "SELECT 1"
                    )
                )

        return (
            True,
            "ok",
        )

    except TimeoutError:
        logger.warning(
            "Database readiness check timed out."
        )

        return (
            False,
            "timeout",
        )

    except Exception:
        logger.exception(
            "Database readiness check failed."
        )

        return (
            False,
            "unavailable",
        )


async def dispose_database(
) -> None:
    """
    Dispose the async SQLAlchemy engine and all
    checked-in pooled database connections.
    """

    await engine.dispose()