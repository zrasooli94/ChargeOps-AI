import json
from typing import Any

from mcp.server import MCPServer

from app.core.config import settings
from app.core.database import (
    AsyncSessionLocal,
)
from app.services.agent_tools import (
    StationContext,
    execute_incident_history_tool,
    execute_knowledge_tool,
    execute_station_tool,
    execute_weather_tool,
)

mcp = MCPServer(
    "ChargeOps AI",
    instructions=(
        "Read-only operational intelligence for "
        "EV charging infrastructure. Provides trusted "
        "station data, incident history, current weather, "
        "and ChargeOps technical knowledge. Operational "
        "write actions are intentionally not exposed."
    ),
)


def normalize_station_id(
    station_id: str,
) -> str:
    normalized = (
        station_id
        .strip()
        .upper()
    )

    if not normalized:
        raise ValueError(
            "Station ID must not be empty."
        )

    if len(normalized) > 50:
        raise ValueError(
            "Station ID is too long."
        )

    return normalized


async def _load_station(
    station_id: str,
) -> tuple[
    dict[str, Any],
    StationContext | None,
]:
    normalized_station_id = (
        normalize_station_id(
            station_id
        )
    )

    async with (
        AsyncSessionLocal()
        as session
    ):
        (
            result,
            station,
            _,
        ) = await execute_station_tool(
            session=session,
            station_id=(
                normalized_station_id
            ),
        )

    return (
        result,
        station,
    )


@mcp.tool()
async def get_station_details(
    station_id: str,
) -> dict[str, Any]:
    """
    Retrieve trusted operational information for
    an EV charging station from ChargeOps.
    """

    result, _ = await _load_station(
        station_id
    )

    return result


@mcp.tool()
async def get_station_incidents(
    station_id: str,
) -> dict[str, Any]:
    """
    Retrieve recent operational incidents for a
    ChargeOps EV charging station.
    """

    normalized_station_id = (
        normalize_station_id(
            station_id
        )
    )

    async with (
        AsyncSessionLocal()
        as session
    ):
        (
            station_result,
            station,
            _,
        ) = await execute_station_tool(
            session=session,
            station_id=(
                normalized_station_id
            ),
        )

        if station is None:
            return {
                "found": False,
                "station_id": (
                    normalized_station_id
                ),
                "station": (
                    station_result
                ),
                "incidents": [],
            }

        result, _ = (
            await execute_incident_history_tool(
                session=session,
                station=station,
            )
        )

    return {
        "found": True,
        **result,
    }


@mcp.tool()
async def get_station_weather(
    station_id: str,
) -> dict[str, Any]:
    """
    Retrieve current real-world weather for the
    location of a ChargeOps EV charging station.

    If the external weather provider is temporarily
    unavailable, ChargeOps returns a safe degraded
    response rather than inventing weather.
    """

    normalized_station_id = (
        normalize_station_id(
            station_id
        )
    )

    async with (
        AsyncSessionLocal()
        as session
    ):
        (
            station_result,
            station,
            _,
        ) = await execute_station_tool(
            session=session,
            station_id=(
                normalized_station_id
            ),
        )

        if station is None:
            return {
                "found": False,
                "station_id": (
                    normalized_station_id
                ),
                "station": (
                    station_result
                ),
                "available": False,
            }

        result, _ = (
            await execute_weather_tool(
                station
            )
        )

    return {
        "found": True,
        **result,
    }


@mcp.tool()
async def search_chargeops_knowledge(
    query: str,
    category: str | None = None,
    document_id: int | None = None,
) -> dict[str, Any]:
    """
    Search the ChargeOps vector knowledge base for
    technical EV charging information.

    Results are retrieved from the same pgvector-backed
    knowledge system used by the ChargeOps agent.
    """

    normalized_query = query.strip()

    if len(normalized_query) < 3:
        raise ValueError(
            "Knowledge query must contain "
            "at least 3 characters."
        )

    if len(normalized_query) > 3000:
        raise ValueError(
            "Knowledge query is too long."
        )

    normalized_category = (
        category.strip()
        if category is not None
        and category.strip()
        else None
    )

    async with (
        AsyncSessionLocal()
        as session
    ):
        (
            result,
            _,
            _,
        ) = await execute_knowledge_tool(
            session=session,
            query=normalized_query,
            category=(
                normalized_category
            ),
            document_id=document_id,
        )

    return result


@mcp.resource(
    "chargeops://station/{station_id}"
)
async def station_resource(
    station_id: str,
) -> str:
    """
    Expose a ChargeOps station as an MCP resource.
    """

    result, _ = await _load_station(
        station_id
    )

    return json.dumps(
        result,
        ensure_ascii=False,
        default=str,
    )


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=settings.mcp_host,
        port=settings.mcp_port,
        streamable_http_path=(
            settings
            .mcp_streamable_http_path
        ),
        stateless_http=True,
        json_response=True,
    )