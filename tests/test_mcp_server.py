import asyncio
from unittest.mock import (
    AsyncMock,
    patch,
)

from app.mcp.server import (
    get_station_details,
    get_station_incidents,
    get_station_weather,
    mcp,
    normalize_station_id,
    search_chargeops_knowledge,
)


class FakeSessionContext:
    async def __aenter__(
        self,
    ) -> object:
        return object()

    async def __aexit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> bool:
        return False


def test_station_id_is_normalized(
) -> None:
    assert (
        normalize_station_id(
            "  kl-205  "
        )
        == "KL-205"
    )


def test_mcp_registers_expected_tools(
) -> None:
    async def run_test() -> None:
        tools = await mcp.list_tools()

        tool_names = {
            tool.name
            for tool in tools
        }

        assert {
            "get_station_details",
            "get_station_incidents",
            "get_station_weather",
            "search_chargeops_knowledge",
        }.issubset(
            tool_names
        )

    asyncio.run(
        run_test()
    )


def test_station_tool_returns_existing_station(
) -> None:
    async def run_test() -> None:
        station = {
            "station_id": "KL-205",
            "name": "Test Station",
            "charger_model": "ABB Terra 54",
            "location": "Kuala Lumpur",
            "latitude": 3.139,
            "longitude": 101.6869,
            "status": "active",
        }

        with (
            patch(
                "app.mcp.server."
                "AsyncSessionLocal",
                return_value=(
                    FakeSessionContext()
                ),
            ),
            patch(
                "app.mcp.server."
                "execute_station_tool",
                new=AsyncMock(
                    return_value=(
                        {
                            "found": True,
                            **station,
                        },
                        station,
                        None,
                    )
                ),
            ),
        ):
            result = (
                await get_station_details(
                    "kl-205"
                )
            )

        assert result["found"] is True

        assert (
            result["station_id"]
            == "KL-205"
        )

    asyncio.run(
        run_test()
    )


def test_incident_tool_handles_missing_station(
) -> None:
    async def run_test() -> None:
        with (
            patch(
                "app.mcp.server."
                "AsyncSessionLocal",
                return_value=(
                    FakeSessionContext()
                ),
            ),
            patch(
                "app.mcp.server."
                "execute_station_tool",
                new=AsyncMock(
                    return_value=(
                        {
                            "found": False,
                            "station_id": (
                                "UNKNOWN"
                            ),
                        },
                        None,
                        None,
                    )
                ),
            ),
        ):
            result = (
                await get_station_incidents(
                    "unknown"
                )
            )

        assert result["found"] is False
        assert result["incidents"] == []

    asyncio.run(
        run_test()
    )


def test_weather_tool_preserves_degraded_result(
) -> None:
    async def run_test() -> None:
        station = {
            "station_id": "KL-205",
            "name": "Test Station",
            "charger_model": "ABB Terra 54",
            "location": "Kuala Lumpur",
            "latitude": 3.139,
            "longitude": 101.6869,
            "status": "active",
        }

        with (
            patch(
                "app.mcp.server."
                "AsyncSessionLocal",
                return_value=(
                    FakeSessionContext()
                ),
            ),
            patch(
                "app.mcp.server."
                "execute_station_tool",
                new=AsyncMock(
                    return_value=(
                        {
                            "found": True,
                            **station,
                        },
                        station,
                        None,
                    )
                ),
            ),
            patch(
                "app.mcp.server."
                "execute_weather_tool",
                new=AsyncMock(
                    return_value=(
                        {
                            "station_id": "KL-205",
                            "available": False,
                            "error": (
                                "Current weather data "
                                "is temporarily unavailable."
                            ),
                        },
                        None,
                    )
                ),
            ),
        ):
            result = (
                await get_station_weather(
                    "KL-205"
                )
            )

        assert result["found"] is True

        assert (
            result["available"]
            is False
        )

    asyncio.run(
        run_test()
    )


def test_knowledge_tool_forwards_search(
) -> None:
    async def run_test() -> None:
        search_mock = AsyncMock(
            return_value=(
                {
                    "query": "OCPP timeout",
                    "count": 1,
                    "results": [
                        {
                            "citation_id": "KB1",
                            "title": (
                                "OCPP Guide"
                            ),
                        }
                    ],
                },
                [],
                None,
            )
        )

        with (
            patch(
                "app.mcp.server."
                "AsyncSessionLocal",
                return_value=(
                    FakeSessionContext()
                ),
            ),
            patch(
                "app.mcp.server."
                "execute_knowledge_tool",
                new=search_mock,
            ),
        ):
            result = (
                await search_chargeops_knowledge(
                    "OCPP timeout"
                )
            )

        assert result["count"] == 1

        search_mock.assert_awaited_once()

    asyncio.run(
        run_test()
    )