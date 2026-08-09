from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.station import StationResponse
from app.services.station_service import (
    get_all_stations,
    get_station,
)

router = APIRouter(
    prefix="/stations",
    tags=["Stations"],
)


@router.get(
    "",
    response_model=list[StationResponse],
)
async def list_stations(
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> list[StationResponse]:
    stations = await get_all_stations(session)

    return [
        StationResponse.model_validate(station)
        for station in stations
    ]


@router.get(
    "/{station_id}",
    response_model=StationResponse,
)
async def station_details(
    station_id: str,
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> StationResponse:
    station = await get_station(
        session,
        station_id,
    )

    if station is None:
        raise HTTPException(
            status_code=404,
            detail="Station not found.",
        )

    return StationResponse.model_validate(station)