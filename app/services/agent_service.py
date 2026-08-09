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


# -------------------------------------------------
# Tool definitions
# -------------------------------------------------


STATION_TOOL: FunctionToolParam = {
    "type": "function",
    "name": "get_station_details",
    "description": (
        "Retrieve trusted information about the selected EV charging "
        "station from the ChargeOps PostgreSQL database. "
        "Use this before performing station-specific operational analysis."
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
        "Use only when current temperature, precipitation, wind, "
        "weather, or environmental conditions are relevant."
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
        "Perform structured technical diagnosis of an EV charging fault. "
        "Use when the user reports charger failures, errors, overheating, "
        "network problems, power problems, payment problems, "
        "or requests troubleshooting."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "issue": {
                "type": "string",
                "description": (
                    "A concise description of the charging issue "
                    "requiring diagnosis."
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
    WEATHER_TOOL,
    DIAGNOSTIC_TOOL,
]


# -------------------------------------------------
# Agent instructions
# -------------------------------------------------


AGENT_INSTRUCTIONS = """
You are ChargeOps AI, an intelligent operations agent for EV charging
infrastructure.

You have three tools:

1. get_station_details
   Retrieves trusted station information from the PostgreSQL database.

2. get_station_weather
   Retrieves current weather for the station.

3. diagnose_charging_issue
   Performs structured EV charger fault diagnosis.

TOOL SELECTION RULES:

GENERAL QUESTIONS

If the user asks a general EV charging knowledge question such as:
"What is OCPP?"

Answer directly without using tools.

STATION-SPECIFIC QUESTIONS

If the user asks anything specifically about the selected station,
first call get_station_details.

Do not assume the charger model, location, coordinates, or station status.

Those values must come from get_station_details.

DIAGNOSTIC QUESTIONS

For a station-specific charger fault:

1. Call get_station_details first.
2. Then call diagnose_charging_issue.

WEATHER QUESTIONS

If the user explicitly asks about current weather, temperature,
rain, wind, environmental conditions, or whether weather could be
contributing to a charging problem:

1. Call get_station_details first.
2. Then call get_station_weather.

WEATHER + DIAGNOSTIC QUESTIONS

If the user asks both for troubleshooting and whether current
weather could be contributing:

1. Call get_station_details.
2. Call get_station_weather.
3. Call diagnose_charging_issue.

Do not use the weather tool merely because a charger reports
an overheating or over-temperature fault.

IMPORTANT:

- Never invent station information.
- Never invent current weather.
- PostgreSQL station data is trusted application data.
- Base conclusions on actual tool results.
- Do not claim a tool was used unless it was executed.
- Clearly state uncertainty when evidence is insufficient.
- Give practical and technically accurate answers.
"""


# -------------------------------------------------
# Tool executors
# -------------------------------------------------


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
            "message": "Station not found in ChargeOps database.",
        }

        trace = ToolTrace(
            tool="get_station_details",
            status="error",
            summary=(
                f"Station {station_id} was not found "
                "in PostgreSQL."
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
        "location": station.location,
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

    result = analysis.model_dump()

    trace = ToolTrace(
        tool="diagnose_charging_issue",
        status="success",
        summary=(
            f"{analysis.category} issue | "
            f"severity: {analysis.severity} | "
            f"confidence: {analysis.confidence:.0%}"
        ),
    )

    return result, trace


# -------------------------------------------------
# Agent
# -------------------------------------------------


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
                "Important: Only the station ID is provided here. "
                "Use get_station_details whenever station metadata "
                "is required.\n\n"
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

        for _ in range(8):
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

                # -----------------------------------------
                # PostgreSQL station tool
                # -----------------------------------------

                if tool_call.name == "get_station_details":
                    (
                        tool_result,
                        station_context,
                        tool_trace,
                    ) = await execute_station_tool(
                        session=session,
                        station_id=station_id,
                    )

                # -----------------------------------------
                # Weather tool
                # -----------------------------------------

                elif tool_call.name == "get_station_weather":
                    if station_context is None:
                        tool_result = {
                            "error": (
                                "Station details are not loaded. "
                                "Call get_station_details first."
                            )
                        }

                        tool_trace = ToolTrace(
                            tool="get_station_weather",
                            status="error",
                            summary=(
                                "Station context must be loaded "
                                "before weather can be retrieved."
                            ),
                        )

                    else:
                        (
                            tool_result,
                            tool_trace,
                        ) = await execute_weather_tool(
                            station=station_context,
                        )

                # -----------------------------------------
                # Diagnostic tool
                # -----------------------------------------

                elif tool_call.name == "diagnose_charging_issue":
                    if station_context is None:
                        tool_result = {
                            "error": (
                                "Station details are not loaded. "
                                "Call get_station_details first."
                            )
                        }

                        tool_trace = ToolTrace(
                            tool="diagnose_charging_issue",
                            status="error",
                            summary=(
                                "Station context must be loaded "
                                "before diagnosis."
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

                tool_output: ResponseInputItemParam = cast(
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

                input_items.append(
                    tool_output
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
            "Agent exceeded the maximum number "
            "of tool iterations."
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