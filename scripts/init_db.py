import asyncio

from app.core.database import Base, engine
from app.models.incident import Incident
from app.models.station import Station


async def main() -> None:
    # Importing both models registers their tables
    # with SQLAlchemy metadata.
    _ = Station, Incident

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )

    print("Database tables created.")


if __name__ == "__main__":
    asyncio.run(main())