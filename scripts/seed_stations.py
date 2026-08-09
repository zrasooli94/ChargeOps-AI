import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.station import Station

STATIONS = [
    {
        "station_id": "KL-205",
        "name": "ChargeOps Central",
        "charger_model": "ABB Terra 54",
        "location": "Kuala Lumpur, Malaysia",
        "latitude": 3.1390,
        "longitude": 101.6869,
        "status": "active",
    },
    {
        "station_id": "KL-101",
        "name": "ChargeOps North",
        "charger_model": "Siemens Sicharge D",
        "location": "Petaling Jaya, Malaysia",
        "latitude": 3.1073,
        "longitude": 101.6067,
        "status": "active",
    },
    {
        "station_id": "KL-330",
        "name": "ChargeOps South",
        "charger_model": "Delta DC Wallbox",
        "location": "Putrajaya, Malaysia",
        "latitude": 2.9264,
        "longitude": 101.6964,
        "status": "maintenance",
    },
]


async def main() -> None:
    async with AsyncSessionLocal() as session:
        for station_data in STATIONS:
            result = await session.execute(
                select(Station).where(
                    Station.station_id
                    == station_data["station_id"]
                )
            )

            existing = result.scalar_one_or_none()

            if existing is None:
                session.add(
                    Station(**station_data)
                )

        await session.commit()

    print("Demo stations seeded.")


if __name__ == "__main__":
    asyncio.run(main())