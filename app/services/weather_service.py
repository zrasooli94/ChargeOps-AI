import logging
from datetime import datetime

import httpx

from app.core.config import settings
from app.schemas.weather import WeatherData

logger = logging.getLogger(__name__)


class WeatherServiceError(Exception):
    """Raised when weather data cannot be retrieved."""


async def get_current_weather(
    latitude: float,
    longitude: float,
) -> tuple[datetime, WeatherData]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "precipitation,"
            "wind_speed_10m,"
            "weather_code"
        ),
        "timezone": "UTC",
    }

    try:
        logger.info(
            "Fetching weather data for latitude=%s longitude=%s",
            latitude,
            longitude,
        )

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                settings.weather_base_url,
                params=params,
            )

            response.raise_for_status()

        payload = response.json()
        current = payload["current"]

        weather = WeatherData(
            temperature_c=current["temperature_2m"],
            precipitation_mm=current["precipitation"],
            wind_speed_kmh=current["wind_speed_10m"],
            weather_code=current["weather_code"],
        )

        observed_at = datetime.fromisoformat(current["time"])

        return observed_at, weather

    except (
        httpx.HTTPError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        logger.exception("Weather API request failed")

        raise WeatherServiceError(
            "Failed to retrieve weather data."
        ) from error