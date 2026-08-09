import json
import logging
from typing import cast

from openai import OpenAIError
from openai.types.responses import (
    FunctionToolParam,
    ResponseInputItemParam,
    ResponseInputParam,
)
from pydantic import (
    BaseModel,
    Field,
    ValidationError,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.openai_client import client
from app.models.station import Station
from app.schemas.agent import ToolTrace
from app.services.incident_service import (
    create_incident,
    get_recent_incidents,
)
from app.services.llm_service import (
    LLMServiceError,
    analyze_charging_issue,
)
from app.services.station_service import get_station
from app.services.weather_service import (
    WeatherServiceError,
    get_current_weather,
)

logger = logging.getLogger(__name__)


class AgentServiceError(Exception):
    """Raised when the ChargeOps agent cannot complete a request."""


class DiagnosticToolArguments(BaseModel):
    issue: str = Field(
        min_length=3,
        max_length=3000,
    )


STATION_TOOL: FunctionToolParam = {
    "type": "function",
    "name": "get_station_details",
    "description": (
        "Retrieve trusted information about the selected EV charging "
        "station from the ChargeOps PostgreSQL database."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
    "strict": True,
}


INCIDENT_HISTORY_TOOL: FunctionToolParam = {
    "type": "function",
    "name": "get_recent_incidents",
    "description": (
        "Retrieve recent recorded incidents for the selected charging "
        "station. Use this when the user asks about previous faults, "
        "incident history, repeated problems, recurring issues, "
        "or similar past failures."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
    "strict": True,
}


WEATHER_TOOL: FunctionToolParam = {
    "type": "function",
    "name": "get_station_weather",
    "description": (
        "Retrieve current real-world weather for the selected station. "
        "Use only when current weather or environmental conditions "
        "are relevant."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
    "strict": True,
}


DIAGNOSTIC_TOOL: FunctionToolParam = {
    "type": "function",
    "name": "diagnose_charging_issue",
    "description": (
        "Perform structured technical diagnosis of an EV charging "
        "fault. A successful diagnosis is automatically recorded "
        "as an incident by the ChargeOps application."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "issue": {
                "type": "string",
                "description": (
                    "The charging issue requiring diagnosis."
                ),
            }
        },
        "required": [
            "issue",
        ],
        "additionalProperties": False,
    },
    "strict": True,
}


TOOLS: list[FunctionToolParam] = [
    STATION_TOOL,
    INCIDENT_HISTORY_TOOL,
    WEATHER_TOOL,
    DIAGNOSTIC_TOOL,
]


AGENT_INSTRUCTIONS = """
You are ChargeOps AI, an intelligent operations agent for EV charging
infrastructure.

AVAILABLE TOOLS:

1. get_station_details
   Retrieves trusted station data from PostgreSQL.

2. get_recent_incidents
   Retrieves recent stored incidents for the station.

3. get_station_weather
   Retrieves current real-world weather.

4. diagnose_charging_issue
   Performs structured technical fault diagnosis. Successful diagnoses
   are automatically saved by the application as incidents.

TOOL ROUTING:

GENERAL KNOWLEDGE
For questions like "What is OCPP?", answer directly with no tools.

STATION INFORMATION
For questions specifically about the selected station:
- Call get_station_details first.

INCIDENT HISTORY
For questions about previous faults, recurring problems, past incidents,
or whether the station has experienced similar issues:
1. Call get_station_details.
2. Call get_recent_incidents.

DIAGNOSIS
For station-specific troubleshooting:
1. Call get_station_details.
2. Call diagnose_charging_issue.

WEATHER
If the user explicitly asks about current weather or whether current
weather could contribute:
1. Call get_station_details.
2. Call get_station_weather.

WEATHER + DIAGNOSIS
If troubleshooting AND current weather are requested:
1. Call get_station_details.
2. Call get_station_weather.
3. Call diagnose_charging_issue.

Do not call the weather tool merely because an over-temperature fault
exists.

IMPORTANT:
- Never invent station information.
- Never invent current weather.
- Never invent incident history.
- Treat PostgreSQL results as trusted application data.
- Base conclusions on real tool results.
- Clearly state uncertainty.
- Give practical and technically accurate responses.
"""


async def execute_station_tool(
    session: AsyncSession,
    station_id: str,
) -> tuple[
    dict,
    Station | None,
    ToolTrace,
]:
    station = await get_station(
        session,
        station_id,
    )

    if station is None:
        result = {
            "found": False,
            "station_id": station_id,
        }

        trace = ToolTrace(
            tool="get_station_details",
            status="error",
            summary=(
                f"Station {station_id} not found."
            ),
        )

        return result, None, trace

    result = {
        "found": True,
        "station_id": station.station_id,
        "name": station.name,
        "charger_model": station.charger_model,
        "location": station.location,
        "latitude": station.latitude,
        "longitude": station.longitude,
        "status": station.status,
    }

    trace = ToolTrace(
        tool="get_station_details",
        status="success",
        summary=(
            f"{station.station_id} | "
            f"{station.charger_model} | "
            f"{station.location} | "
            f"status: {station.status}"
        ),
    )

    return result, station, trace


async def execute_incident_history_tool(
    session: AsyncSession,
    station: Station,
) -> tuple[
    dict,
    ToolTrace,
]:
    incidents = await get_recent_incidents(
        session=session,
        station_id=station.station_id,
        limit=10,
    )

    items = [
        {
            "id": incident.id,
            "issue": incident.issue,
            "category": incident.category,
            "severity": incident.severity,
            "confidence": incident.confidence,
            "summary": incident.summary,
            "status": incident.status,
            "created_at": (
                incident.created_at.isoformat()
            ),
        }
        for incident in incidents
    ]

    result = {
        "station_id": station.station_id,
        "count": len(items),
        "incidents": items,
    }

    trace = ToolTrace(
        tool="get_recent_incidents",
        status="success",
        summary=(
            f"Retrieved {len(items)} recent "
            f"incident(s) for {station.station_id}."
        ),
    )

    return result, trace


async def execute_weather_tool(
    station: Station,
) -> tuple[
    dict,
    ToolTrace,
]:
    observed_at, weather = await get_current_weather(
        latitude=station.latitude,
        longitude=station.longitude,
    )

    result = {
        "station_id": station.station_id,
        "observed_at": observed_at.isoformat(),
        "weather": weather.model_dump(),
    }

    trace = ToolTrace(
        tool="get_station_weather",
        status="success",
        summary=(
            f"Temperature {weather.temperature_c}°C, "
            f"precipitation {weather.precipitation_mm} mm, "
            f"wind {weather.wind_speed_kmh} km/h"
        ),
    )

    return result, trace


async def execute_diagnostic_tool(
    session: AsyncSession,
    station: Station,
    issue: str,
) -> tuple[
    dict,
    ToolTrace,
]:
    context = (
        f"Station ID: {station.station_id}\n"
        f"Station name: {station.name}\n"
        f"Charger model: {station.charger_model}\n"
        f"Location: {station.location}\n"
        f"Station status: {station.status}\n"
        f"Issue: {issue}"
    )

    analysis = await analyze_charging_issue(
        context
    )

    incident = await create_incident(
        session=session,
        station_id=station.station_id,
        issue=issue,
        analysis=analysis,
    )

    result = analysis.model_dump()

    result["incident_id"] = incident.id
    result["incident_status"] = incident.status

    trace = ToolTrace(
        tool="diagnose_charging_issue",
        status="success",
        summary=(
            f"Incident #{incident.id} recorded | "
            f"{analysis.category} | "
            f"severity: {analysis.severity} | "
            f"confidence: {analysis.confidence:.0%}"
        ),
    )

    return result, trace


async def run_agent(
    message: str,
    station_id: str,
    session: AsyncSession,
) -> tuple[
    str,
    list[str],
    list[ToolTrace],
]:
    user_item: ResponseInputItemParam = cast(
        ResponseInputItemParam,
        {
            "role": "user",
            "content": (
                "Trusted application context:\n"
                f"Selected station ID: {station_id}\n\n"
                "Only the station ID is supplied directly. "
                "Retrieve trusted station information using tools "
                "when required.\n\n"
                "User request:\n"
                f"{message}"
            ),
        },
    )

    input_items: ResponseInputParam = [
        user_item
    ]

    used_tools: list[str] = []
    traces: list[ToolTrace] = []

    station_context: Station | None = None

    try:
        response = await client.responses.create(
            model=settings.openai_model,
            instructions=AGENT_INSTRUCTIONS,
            tools=TOOLS,
            tool_choice="auto",
            parallel_tool_calls=False,
            input=input_items,
        )

        for _ in range(10):
            for item in response.output:
                input_items.append(
                    cast(
                        ResponseInputItemParam,
                        item.to_dict(),
                    )
                )

            function_calls = [
                item
                for item in response.output
                if item.type == "function_call"
            ]

            if not function_calls:
                if not response.output_text:
                    raise AgentServiceError(
                        "Agent returned no final response."
                    )

                return (
                    response.output_text,
                    used_tools,
                    traces,
                )

            for tool_call in function_calls:
                logger.info(
                    "Agent requested tool=%s station=%s",
                    tool_call.name,
                    station_id,
                )

                if tool_call.name == "get_station_details":
                    (
                        tool_result,
                        station_context,
                        tool_trace,
                    ) = await execute_station_tool(
                        session=session,
                        station_id=station_id,
                    )

                elif tool_call.name == "get_recent_incidents":
                    if station_context is None:
                        tool_result = {
                            "error": (
                                "Station details must be loaded first."
                            )
                        }

                        tool_trace = ToolTrace(
                            tool="get_recent_incidents",
                            status="error",
                            summary=(
                                "Station context is not loaded."
                            ),
                        )

                    else:
                        (
                            tool_result,
                            tool_trace,
                        ) = await execute_incident_history_tool(
                            session=session,
                            station=station_context,
                        )

                elif tool_call.name == "get_station_weather":
                    if station_context is None:
                        tool_result = {
                            "error": (
                                "Station details must be loaded first."
                            )
                        }

                        tool_trace = ToolTrace(
                            tool="get_station_weather",
                            status="error",
                            summary=(
                                "Station context is not loaded."
                            ),
                        )

                    else:
                        (
                            tool_result,
                            tool_trace,
                        ) = await execute_weather_tool(
                            station_context
                        )

                elif tool_call.name == "diagnose_charging_issue":
                    if station_context is None:
                        tool_result = {
                            "error": (
                                "Station details must be loaded first."
                            )
                        }

                        tool_trace = ToolTrace(
                            tool="diagnose_charging_issue",
                            status="error",
                            summary=(
                                "Station context is not loaded."
                            ),
                        )

                    else:
                        arguments = (
                            DiagnosticToolArguments.model_validate_json(
                                tool_call.arguments
                            )
                        )

                        (
                            tool_result,
                            tool_trace,
                        ) = await execute_diagnostic_tool(
                            session=session,
                            station=station_context,
                            issue=arguments.issue,
                        )

                else:
                    raise AgentServiceError(
                        f"Unknown tool requested: "
                        f"{tool_call.name}"
                    )

                if tool_call.name not in used_tools:
                    used_tools.append(
                        tool_call.name
                    )

                traces.append(
                    tool_trace
                )

                input_items.append(
                    cast(
                        ResponseInputItemParam,
                        {
                            "type": "function_call_output",
                            "call_id": tool_call.call_id,
                            "output": json.dumps(
                                tool_result,
                                default=str,
                            ),
                        },
                    )
                )

            response = await client.responses.create(
                model=settings.openai_model,
                instructions=AGENT_INSTRUCTIONS,
                tools=TOOLS,
                tool_choice="auto",
                parallel_tool_calls=False,
                input=input_items,
            )

        raise AgentServiceError(
            "Agent exceeded maximum tool iterations."
        )

    except AgentServiceError:
        raise

    except (
        OpenAIError,
        WeatherServiceError,
        LLMServiceError,
        SQLAlchemyError,
        ValidationError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
    ) as error:
        logger.exception(
            "ChargeOps agent failed"
        )

        raise AgentServiceError(
            "ChargeOps agent could not complete the request."
        ) from error