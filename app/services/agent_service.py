import json
import logging

from openai import OpenAIError

from app.core.config import settings
from app.core.openai_client import client
from app.services.weather_service import (
    WeatherServiceError,
    get_current_weather,
)

logger = logging.getLogger(__name__)


class AgentServiceError(Exception):
    """Raised when the ChargeOps agent cannot complete a request."""


WEATHER_TOOL = {
    "type": "function",
    "name": "get_station_weather",
    "description": (
        "Get the current real-world weather for the EV charging station. "
        "Use this tool when the user asks about current temperature, "
        "precipitation, wind, weather conditions, or whether current weather "
        "could be affecting EV charging operations. "
        "The application supplies trusted station coordinates."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
    "strict": True,
}


AGENT_INSTRUCTIONS = """
You are ChargeOps AI, an operations agent for EV charging infrastructure.

You can answer general EV charging questions directly.

You have access to a weather tool that retrieves real current weather
for the station supplied by the application.

Rules:
- Use the weather tool whenever current weather information is necessary.
- Never invent or estimate current weather.
- Treat station ID and coordinates supplied by the application as trusted.
- Explain how tool results relate to the user's operational question.
- If available information is insufficient, clearly say so.
- Keep responses practical and technically accurate.
"""


async def run_agent(
    message: str,
    station_id: str,
    latitude: float,
    longitude: float,
) -> tuple[str, list[str]]:
    input_items = [
        {
            "role": "user",
            "content": (
                f"Trusted station context:\n"
                f"Station ID: {station_id}\n"
                f"Latitude: {latitude}\n"
                f"Longitude: {longitude}\n\n"
                f"User request:\n{message}"
            ),
        }
    ]

    used_tools: list[str] = []

    try:
        response = await client.responses.create(
            model=settings.openai_model,
            instructions=AGENT_INSTRUCTIONS,
            tools=[WEATHER_TOOL],
            tool_choice="auto",
            parallel_tool_calls=False,
            input=input_items,
        )

        for _ in range(3):
            input_items += response.output

            function_calls = [
                item
                for item in response.output
                if item.type == "function_call"
            ]

            if not function_calls:
                return response.output_text, used_tools

            for tool_call in function_calls:
                if tool_call.name != "get_station_weather":
                    raise AgentServiceError(
                        f"Unknown tool requested: {tool_call.name}"
                    )

                logger.info(
                    "Agent calling weather tool for station=%s",
                    station_id,
                )

                observed_at, weather = await get_current_weather(
                    latitude=latitude,
                    longitude=longitude,
                )

                tool_result = {
                    "station_id": station_id,
                    "observed_at": observed_at.isoformat(),
                    "weather": weather.model_dump(),
                }

                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": json.dumps(tool_result),
                    }
                )

                used_tools.append(tool_call.name)

            response = await client.responses.create(
                model=settings.openai_model,
                instructions=AGENT_INSTRUCTIONS,
                tools=[WEATHER_TOOL],
                tool_choice="auto",
                parallel_tool_calls=False,
                input=input_items,
            )

        raise AgentServiceError(
            "Agent exceeded the maximum number of tool iterations."
        )

    except (OpenAIError, WeatherServiceError) as error:
        logger.exception("ChargeOps agent failed")

        raise AgentServiceError(
            "ChargeOps agent could not complete the request."
        ) from error