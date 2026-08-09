import asyncio

from sqlalchemy import text

from app.core.database import engine


async def main() -> None:
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "CREATE EXTENSION IF NOT EXISTS vector"
            )
        )

    print(
        "Database extensions ready. "
        "Use `python -m alembic upgrade head` "
        "for schema migrations."
    )


if __name__ == "__main__":
    asyncio.run(main())