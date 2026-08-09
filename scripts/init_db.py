import asyncio

from app.core.database import engine
from app.models.station import Station


async def main() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(
            Station.metadata.create_all
        )

    print("Database tables created.")


if __name__ == "__main__":
    asyncio.run(main())