import asyncio
import logging
from datetime import datetime

import httpx

from app.core.config import settings
from app.schemas.weather import (
    WeatherData,
)

logger = logging.getLogger(
    __name__
)


TRANSIENT_STATUS_CODES = {
    408,
    429,
    500,
    502,
    503,
    504,
}


class WeatherServiceError(
    Exception
):
    """Raised when weather data cannot be retrieved."""


_weather_client: (
    httpx.AsyncClient
    | None
) = None


def _create_weather_client(
) -> httpx.AsyncClient:
    timeout = httpx.Timeout(
        connect=(
            settings
            .weather_connect_timeout_seconds
        ),
        read=(
            settings
            .weather_read_timeout_seconds
        ),
        write=(
            settings
            .weather_write_timeout_seconds
        ),
        pool=(
            settings
            .weather_pool_timeout_seconds
        ),
    )

    limits = httpx.Limits(
        max_connections=(
            settings
            .weather_max_connections
        ),
        max_keepalive_connections=(
            settings
            .weather_max_keepalive_connections
        ),
    )

    return httpx.AsyncClient(
        timeout=timeout,
        limits=limits,
        follow_redirects=False,
    )


def get_weather_client(
) -> httpx.AsyncClient:
    global _weather_client

    if (
        _weather_client is None
        or _weather_client.is_closed
    ):
        _weather_client = (
            _create_weather_client()
        )

    return _weather_client


async def close_weather_client(
) -> None:
    global _weather_client

    if (
        _weather_client is not None
        and not _weather_client.is_closed
    ):
        await _weather_client.aclose()

    _weather_client = None


def _retry_delay_seconds(
    attempt_number: int,
) -> float:
    """
    Small bounded exponential delay.

    attempt 1 -> base
    attempt 2 -> base * 2
    attempt 3 -> base * 4
    """

    return (
        settings
        .weather_retry_base_delay_seconds
        * (
            2
            ** (
                attempt_number
                - 1
            )
        )
    )


def _parse_weather_response(
    response: httpx.Response,
) -> tuple[
    datetime,
    WeatherData,
]:
    payload = response.json()

    current = payload[
        "current"
    ]

    weather = WeatherData(
        temperature_c=(
            current[
                "temperature_2m"
            ]
        ),
        precipitation_mm=(
            current[
                "precipitation"
            ]
        ),
        wind_speed_kmh=(
            current[
                "wind_speed_10m"
            ]
        ),
        weather_code=(
            current[
                "weather_code"
            ]
        ),
    )

    observed_at = datetime.fromisoformat(
        current[
            "time"
        ]
    )

    return (
        observed_at,
        weather,
    )


async def get_current_weather(
    latitude: float,
    longitude: float,
) -> tuple[
    datetime,
    WeatherData,
]:
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

    client = get_weather_client()

    max_attempts = (
        settings
        .weather_max_attempts
    )

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        try:
            logger.info(
                "Fetching weather data "
                "latitude=%s longitude=%s "
                "attempt=%s/%s",
                latitude,
                longitude,
                attempt,
                max_attempts,
            )

            response = await client.get(
                settings.weather_base_url,
                params=params,
            )

            if (
                response.status_code
                in TRANSIENT_STATUS_CODES
                and attempt
                < max_attempts
            ):
                delay = (
                    _retry_delay_seconds(
                        attempt
                    )
                )

                logger.warning(
                    "Transient weather API "
                    "status=%s; retrying in %.2fs",
                    response.status_code,
                    delay,
                )

                await asyncio.sleep(
                    delay
                )

                continue

            response.raise_for_status()

            return _parse_weather_response(
                response
            )

        except httpx.TransportError as error:
            if attempt < max_attempts:
                delay = (
                    _retry_delay_seconds(
                        attempt
                    )
                )

                logger.warning(
                    "Transient weather transport "
                    "failure; retrying in %.2fs",
                    delay,
                )

                await asyncio.sleep(
                    delay
                )

                continue

            logger.exception(
                "Weather API transport failed "
                "after all attempts."
            )

            raise WeatherServiceError(
                "Failed to retrieve "
                "weather data."
            ) from error

        except httpx.HTTPStatusError as error:
            logger.warning(
                "Weather API returned "
                "status=%s.",
                error.response.status_code,
            )

            raise WeatherServiceError(
                "Failed to retrieve "
                "weather data."
            ) from error

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            logger.exception(
                "Weather API returned "
                "invalid response data."
            )

            raise WeatherServiceError(
                "Failed to retrieve "
                "weather data."
            ) from error

    raise WeatherServiceError(
        "Failed to retrieve weather data."
    )