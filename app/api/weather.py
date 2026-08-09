from fastapi import APIRouter, HTTPException

from app.schemas.weather import WeatherRequest, WeatherResponse
from app.services.weather_service import (
    WeatherServiceError,
    get_current_weather,
)

router = APIRouter(
    prefix="/weather",
    tags=["Weather"],
)


@router.post(
    "/current",
    response_model=WeatherResponse,
)
async def current_weather(
    request: WeatherRequest,
) -> WeatherResponse:
    try:
        observed_at, weather = await get_current_weather(
            latitude=request.latitude,
            longitude=request.longitude,
        )

        return WeatherResponse(
            station_id=request.station_id,
            latitude=request.latitude,
            longitude=request.longitude,
            observed_at=observed_at,
            weather=weather,
        )

    except WeatherServiceError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error