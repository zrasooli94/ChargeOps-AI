from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.station import Station


async def get_all_stations(
    session: AsyncSession,
) -> list[Station]:
    result = await session.execute(
        select(Station).order_by(Station.station_id)
    )

    return list(result.scalars().all())


async def get_station(
    session: AsyncSession,
    station_id: str,
) -> Station | None:
    result = await session.execute(
        select(Station).where(
            Station.station_id == station_id.upper()
        )
    )

    return result.scalar_one_or_none()

async def update_station_status(
    session: AsyncSession,
    station_id: str,
    status: str,
) -> Station | None:
    result = await session.execute(
        select(
            Station
        ).where(
            Station.station_id
            == station_id
        )
    )

    station = (
        result.scalar_one_or_none()
    )

    if station is None:
        return None

    station.status = status

    await session.commit()

    await session.refresh(
        station
    )

    return station