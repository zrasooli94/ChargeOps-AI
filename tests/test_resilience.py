import asyncio
from unittest.mock import (
    AsyncMock,
    patch,
)
from uuid import uuid4

import pytest
from sqlalchemy.exc import (
    SQLAlchemyError,
)

from app.services.agent_tools import (
    StationContext,
    execute_weather_tool,
)
from app.services.observability_resilience import (
    safe_complete_pending_agent_run,
    safe_record_agent_run,
)
from app.services.weather_service import (
    WeatherServiceError,
)


def make_station(
) -> StationContext:
    return {
        "station_id": "KL-205",
        "name": "Test Station",
        "charger_model": "ABB Terra 54",
        "location": (
            "Kuala Lumpur, Malaysia"
        ),
        "latitude": 3.1390,
        "longitude": 101.6869,
        "status": "active",
    }


def test_weather_failure_degrades_safely(
) -> None:
    async def run_test() -> None:
        with patch(
            "app.services.agent_tools."
            "get_current_weather",
            new=AsyncMock(
                side_effect=(
                    WeatherServiceError(
                        "provider secret failure"
                    )
                )
            ),
        ):
            result, trace = (
                await execute_weather_tool(
                    make_station()
                )
            )

        assert (
            result["available"]
            is False
        )

        assert (
            result["error"]
            == (
                "Current weather data is "
                "temporarily unavailable."
            )
        )

        assert (
            "provider secret failure"
            not in str(
                result
            )
        )

        assert trace.status == "error"

    asyncio.run(
        run_test()
    )


def test_observability_success_is_reported(
) -> None:
    async def run_test() -> None:
        with patch(
            "app.services."
            "observability_resilience."
            "record_agent_run",
            new=AsyncMock(),
        ) as record_mock:
            persisted = (
                await safe_record_agent_run(
                    run_id=uuid4(),
                    thread_id="test-thread",
                    station_id="KL-205",
                    user_message="Hello",
                    answer="Hello.",
                    used_tools=[],
                    trace=[],
                    approval_required=False,
                    latency_ms=100,
                )
            )

        assert persisted is True

        record_mock.assert_awaited_once()

    asyncio.run(
        run_test()
    )


def test_observability_database_failure_does_not_escape(
) -> None:
    async def run_test() -> None:
        with patch(
            "app.services."
            "observability_resilience."
            "record_agent_run",
            new=AsyncMock(
                side_effect=(
                    SQLAlchemyError(
                        "database unavailable"
                    )
                )
            ),
        ):
            persisted = (
                await safe_record_agent_run(
                    run_id=uuid4(),
                    thread_id="test-thread",
                    station_id="KL-205",
                    user_message="Hello",
                    answer="Hello.",
                    used_tools=[],
                    trace=[],
                    approval_required=False,
                    latency_ms=100,
                )
            )

        assert persisted is False

    asyncio.run(
        run_test()
    )


def test_observability_does_not_hide_programming_errors(
) -> None:
    async def run_test() -> None:
        with patch(
            "app.services."
            "observability_resilience."
            "record_agent_run",
            new=AsyncMock(
                side_effect=ValueError(
                    "programming bug"
                )
            ),
        ), pytest.raises(
            ValueError,
            match="programming bug",
        ):
            await safe_record_agent_run(
                run_id=uuid4(),
                thread_id="test-thread",
                station_id="KL-205",
                user_message="Hello",
                answer="Hello.",
                used_tools=[],
                trace=[],
                approval_required=False,
                latency_ms=100,
            )

    asyncio.run(
        run_test()
    )


def test_observability_completion_failure_returns_none(
) -> None:
    async def run_test() -> None:
        with patch(
            "app.services."
            "observability_resilience."
            "complete_pending_agent_run",
            new=AsyncMock(
                side_effect=(
                    SQLAlchemyError(
                        "database unavailable"
                    )
                )
            ),
        ):
            result = (
                await safe_complete_pending_agent_run(
                    thread_id="test-thread",
                    approved=True,
                    answer="Approved.",
                    used_tools=[
                        "change_station_status"
                    ],
                    trace=[],
                )
            )

        assert result is None

    asyncio.run(
        run_test()
    )