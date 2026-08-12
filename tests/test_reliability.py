import asyncio
from unittest.mock import (
    AsyncMock,
    patch,
)

import httpx

from app.core.database import (
    check_database_ready,
)
from app.services.weather_service import (
    WeatherServiceError,
    get_current_weather,
)


def make_weather_response(
    status_code: int = 200,
) -> httpx.Response:
    request = httpx.Request(
        "GET",
        "https://api.open-meteo.com/"
        "v1/forecast",
    )

    if status_code == 200:
        return httpx.Response(
            status_code=200,
            request=request,
            json={
                "current": {
                    "temperature_2m": 29.5,
                    "precipitation": 0.2,
                    "wind_speed_10m": 11.0,
                    "weather_code": 2,
                    "time": (
                        "2026-08-11T14:00"
                    ),
                }
            },
        )

    return httpx.Response(
        status_code=status_code,
        request=request,
        json={
            "error": True
        },
    )


def test_weather_success(
) -> None:
    async def run_test() -> None:
        client = AsyncMock()

        client.get.return_value = (
            make_weather_response()
        )

        with patch(
            "app.services.weather_service."
            "get_weather_client",
            return_value=client,
        ):
            observed_at, weather = (
                await get_current_weather(
                    latitude=3.1390,
                    longitude=101.6869,
                )
            )

        assert (
            observed_at.year
            == 2026
        )

        assert (
            weather.temperature_c
            == 29.5
        )

        client.get.assert_awaited_once()

    asyncio.run(
        run_test()
    )


def test_weather_retries_transient_status(
) -> None:
    async def run_test() -> None:
        client = AsyncMock()

        client.get.side_effect = [
            make_weather_response(
                503
            ),
            make_weather_response(
                200
            ),
        ]

        with (
            patch(
                "app.services.weather_service."
                "get_weather_client",
                return_value=client,
            ),
            patch(
                "app.services.weather_service."
                "asyncio.sleep",
                new=AsyncMock(),
            ) as sleep_mock,
        ):
            _, weather = (
                await get_current_weather(
                    latitude=3.1390,
                    longitude=101.6869,
                )
            )

        assert (
            weather.temperature_c
            == 29.5
        )

        assert (
            client.get.await_count
            == 2
        )

        sleep_mock.assert_awaited_once()

    asyncio.run(
        run_test()
    )


def test_weather_does_not_retry_permanent_400(
) -> None:
    async def run_test() -> None:
        client = AsyncMock()

        client.get.return_value = (
            make_weather_response(
                400
            )
        )

        with (
            patch(
                "app.services.weather_service."
                "get_weather_client",
                return_value=client,
            ),
            patch(
                "app.services.weather_service."
                "asyncio.sleep",
                new=AsyncMock(),
            ) as sleep_mock,
        ):
            try:
                await get_current_weather(
                    latitude=3.1390,
                    longitude=101.6869,
                )

            except WeatherServiceError:
                pass

            else:
                raise AssertionError(
                    "Expected WeatherServiceError."
                )

        assert (
            client.get.await_count
            == 1
        )

        sleep_mock.assert_not_awaited()

    asyncio.run(
        run_test()
    )


def test_weather_retries_transport_failure(
) -> None:
    async def run_test() -> None:
        client = AsyncMock()

        client.get.side_effect = [
            httpx.ConnectError(
                "temporary connection failure"
            ),
            make_weather_response(
                200
            ),
        ]

        with (
            patch(
                "app.services.weather_service."
                "get_weather_client",
                return_value=client,
            ),
            patch(
                "app.services.weather_service."
                "asyncio.sleep",
                new=AsyncMock(),
            ),
        ):
            _, weather = (
                await get_current_weather(
                    latitude=3.1390,
                    longitude=101.6869,
                )
            )

        assert (
            weather.temperature_c
            == 29.5
        )

        assert (
            client.get.await_count
            == 2
        )

    asyncio.run(
        run_test()
    )


def test_database_readiness_success(
) -> None:
    class FakeConnection:
        async def __aenter__(
            self,
        ):
            return self

        async def __aexit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            return None

        async def execute(
            self,
            statement,
        ):
            return None

    class FakeEngine:
        def connect(
            self,
        ) -> FakeConnection:
            return FakeConnection()

    async def run_test() -> None:
        with patch(
            "app.core.database.engine",
            new=FakeEngine(),
        ):
            ready, reason = (
                await check_database_ready()
            )

        assert ready is True
        assert reason == "ok"

    asyncio.run(
        run_test()
    )


def test_database_readiness_failure_is_safe(
) -> None:
    class FailingConnection:
        async def __aenter__(
            self,
        ):
            raise RuntimeError(
                "database-password-secret"
            )

        async def __aexit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            return None

    class FailingEngine:
        def connect(
            self,
        ) -> FailingConnection:
            return FailingConnection()

    async def run_test() -> None:
        with patch(
            "app.core.database.engine",
            new=FailingEngine(),
        ):
            ready, reason = (
                await check_database_ready()
            )

        assert ready is False

        assert (
            reason
            == "unavailable"
        )

        assert (
            "database-password-secret"
            not in reason
        )

    asyncio.run(
        run_test()
    )
