import json
import logging
from typing import cast

from openai import OpenAIError
from openai.types.responses import (
    FunctionToolParam,
    ResponseInputItemParam,
    ResponseInputParam,
)

from app.core.config import settings
from app.core.openai_client import client
from app.schemas.agent import ToolTrace
from app.services.llm_service import (
    LLMServiceError,
    analyze_charging_issue,
)
from app.services.weather_service import (
    WeatherServiceError,
    get_current_weather,
)

logger = logging.getLogger(__name__)


class AgentServiceError(Exception):
    """Raised when the ChargeOps agent cannot complete a request."""


WEATHER_TOOL: FunctionToolParam = {
    "type": "function",
    "name": "get_station_weather",
    "description": (
        "Get the current real-world weather for the EV charging station. "
        "Use this tool when current temperature, precipitation, wind, "
        "or weather conditions may affect charging operations."
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
        "Perform a structured technical diagnosis of an EV charging problem. "
        "Use this when the user reports faults, failures, abnormal behavior, "
        "overheating, connectivity issues, power problems, payment problems, "
        "or asks for troubleshooting."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "issue": {
                "type": "string",
                "description": (
                    "A clear description of the EV charging issue "
                    "that requires diagnosis."
                ),
            }
        },
        "required": ["issue"],
        "additionalProperties": False,
    },
    "strict": True,
}


TOOLS: list[FunctionToolParam] = [
    WEATHER_TOOL,
    DIAGNOSTIC_TOOL,
]


AGENT_INSTRUCTIONS = """
You are ChargeOps AI, an intelligent operations agent for EV charging
infrastructure.

You have two tools:

1. get_station_weather
   Retrieves current real-world weather for the station.

2. diagnose_charging_issue
   Performs structured technical diagnosis of charging faults.

TOOL SELECTION RULES:

- Answer general EV charging knowledge questions directly without tools.

- Use diagnose_charging_issue when the user reports a charger fault,
  abnormal behavior, error, failure, overheating, connectivity problem,
  power issue, payment issue, or asks for troubleshooting.

- Use get_station_weather ONLY when the user explicitly asks about:
  current weather, temperature, rain, wind, environmental conditions,
  or whether weather could be contributing to the problem.

- Do NOT call get_station_weather merely because a charger reports
  overheating or an over-temperature fault.

- If the user asks both for technical diagnosis AND whether current
  weather/environment could be contributing, use BOTH tools.

Examples:

Question:
"What is OCPP?"
Action:
Answer directly. Use no tools.

Question:
"My charger stops every two minutes with an over-temperature warning.
Diagnose the problem."
Action:
Use diagnose_charging_issue only.

Question:
"What is the current temperature at this station?"
Action:
Use get_station_weather only.

Question:
"My charger is overheating. Check whether today's weather could be
contributing and diagnose the problem."
Action:
Use both get_station_weather and diagnose_charging_issue.

OTHER RULES:

- Never invent current weather.
- Treat station ID, charger model, latitude, and longitude supplied by
  the application as trusted context.
- Base conclusions on actual tool results.
- Do not claim a tool was used unless it was actually executed.
- Clearly state uncertainty when evidence is insufficient.
- Give practical and technically accurate answers.
"""


async def execute_weather_tool(
    station_id: str,
    latitude: float,
    longitude: float,
) -> tuple[dict, ToolTrace]:
    observed_at, weather = await get_current_weather(
        latitude=latitude,
        longitude=longitude,
    )

    tool_result = {
        "station_id": station_id,
        "observed_at": observed_at.isoformat(),
        "weather": weather.model_dump(),
    }

    tool_trace = ToolTrace(
        tool="get_station_weather",
        status="success",
        summary=(
            f"Temperature {weather.temperature_c}°C, "
            f"precipitation {weather.precipitation_mm} mm, "
            f"wind {weather.wind_speed_kmh} km/h"
        ),
    )

    return tool_result, tool_trace


async def execute_diagnostic_tool(
    station_id: str,
    charger_model: str | None,
    issue: str,
) -> tuple[dict, ToolTrace]:
    context = (
        f"Station ID: {station_id}\n"
        f"Charger model: {charger_model or 'Unknown'}\n"
        f"Issue: {issue}"
    )

    analysis = await analyze_charging_issue(context)

    tool_result = analysis.model_dump()

    tool_trace = ToolTrace(
        tool="diagnose_charging_issue",
        status="success",
        summary=(
            f"{analysis.category} issue | "
            f"severity: {analysis.severity} | "
            f"confidence: {analysis.confidence:.0%}"
        ),
    )

    return tool_result, tool_trace


async def run_agent(
    message: str,
    station_id: str,
    charger_model: str | None,
    latitude: float,
    longitude: float,
) -> tuple[str, list[str], list[ToolTrace]]:
    user_item: ResponseInputItemParam = cast(
        ResponseInputItemParam,
        {
            "role": "user",
            "content": (
                "Trusted station context:\n"
                f"Station ID: {station_id}\n"
                f"Charger model: {charger_model or 'Unknown'}\n"
                f"Latitude: {latitude}\n"
                f"Longitude: {longitude}\n\n"
                "User request:\n"
                f"{message}"
            ),
        },
    )

    input_items: ResponseInputParam = [user_item]

    used_tools: list[str] = []
    traces: list[ToolTrace] = []

    try:
        response = await client.responses.create(
            model=settings.openai_model,
            instructions=AGENT_INSTRUCTIONS,
            tools=TOOLS,
            tool_choice="auto",
            parallel_tool_calls=False,
            input=input_items,
        )

        for _ in range(5):
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

                if tool_call.name == "get_station_weather":
                    tool_result, tool_trace = await execute_weather_tool(
                        station_id=station_id,
                        latitude=latitude,
                        longitude=longitude,
                    )

                elif tool_call.name == "diagnose_charging_issue":
                    arguments = json.loads(tool_call.arguments)

                    issue = arguments["issue"]

                    tool_result, tool_trace = await execute_diagnostic_tool(
                        station_id=station_id,
                        charger_model=charger_model,
                        issue=issue,
                    )

                else:
                    raise AgentServiceError(
                        f"Unknown tool requested: {tool_call.name}"
                    )

                used_tools.append(tool_call.name)
                traces.append(tool_trace)

                tool_output_item: ResponseInputItemParam = cast(
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

                input_items.append(tool_output_item)

            response = await client.responses.create(
                model=settings.openai_model,
                instructions=AGENT_INSTRUCTIONS,
                tools=TOOLS,
                tool_choice="auto",
                parallel_tool_calls=False,
                input=input_items,
            )

        raise AgentServiceError(
            "Agent exceeded the maximum number of tool iterations."
        )

    except AgentServiceError:
        raise

    except (
        OpenAIError,
        WeatherServiceError,
        LLMServiceError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
    ) as error:
        logger.exception("ChargeOps agent failed")

        raise AgentServiceError(
            "ChargeOps agent could not complete the request."
        ) from error