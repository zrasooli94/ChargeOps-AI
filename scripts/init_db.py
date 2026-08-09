import asyncio

from sqlalchemy import text

from app.core.database import Base, engine
from app.models.incident import Incident
from app.models.knowledge import KnowledgeChunk
from app.models.station import Station


async def main() -> None:
    _ = (
        Station,
        Incident,
        KnowledgeChunk,
    )

    async with engine.begin() as connection:
        await connection.execute(
            text(
                "CREATE EXTENSION IF NOT EXISTS vector"
            )
        )

        await connection.run_sync(
            Base.metadata.create_all
        )

    print(
        "Database tables and vector extension created."
    )


if __name__ == "__main__":
    asyncio.run(main())