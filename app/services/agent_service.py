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
from app.schemas.knowledge import KnowledgeSearchResult
from app.services.embedding_service import EmbeddingServiceError
from app.services.incident_service import (
    create_incident,
    get_recent_incidents,
)
from app.services.knowledge_service import (
    KnowledgeServiceError,
    search_knowledge,
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


# =================================================
# Tool argument models
# =================================================


class DiagnosticToolArguments(BaseModel):
    issue: str = Field(
        min_length=3,
        max_length=3000,
    )


class KnowledgeToolArguments(BaseModel):
    query: str = Field(
        min_length=3,
        max_length=3000,
    )


# =================================================
# Tool definitions
# =================================================


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
        "station. Use when the user asks about previous faults, "
        "recurring problems, past incidents, or similar failures."
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
        "Use only when current temperature, rain, wind, weather, "
        "or environmental conditions are relevant."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
    "strict": True,
}


KNOWLEDGE_TOOL: FunctionToolParam = {
    "type": "function",
    "name": "search_knowledge_base",
    "description": (
        "Search the ChargeOps technical EV charging knowledge base using "
        "semantic vector search. Use this for technical troubleshooting "
        "guidance, charger failure modes, operational procedures, "
        "network issues, power faults, thermal faults, payment faults, "
        "environmental effects, and related EV charging knowledge."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "A concise technical search query describing the "
                    "information or charging problem to retrieve."
                ),
            }
        },
        "required": [
            "query",
        ],
        "additionalProperties": False,
    },
    "strict": True,
}


DIAGNOSTIC_TOOL: FunctionToolParam = {
    "type": "function",
    "name": "diagnose_charging_issue",
    "description": (
        "Perform structured technical diagnosis of an EV charging fault. "
        "For station-specific troubleshooting, technical knowledge should "
        "normally be retrieved with search_knowledge_base first. "
        "Successful diagnoses are recorded as incidents."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "issue": {
                "type": "string",
                "description": (
                    "The charging issue requiring technical diagnosis."
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
    KNOWLEDGE_TOOL,
    DIAGNOSTIC_TOOL,
]


# =================================================
# Agent instructions
# =================================================


AGENT_INSTRUCTIONS = """
You are ChargeOps AI, an intelligent operations agent for EV charging
infrastructure.

AVAILABLE TOOLS:

1. get_station_details
   Retrieves trusted station information from PostgreSQL.

2. get_recent_incidents
   Retrieves historical incidents for the selected station.

3. get_station_weather
   Retrieves current real-world weather for the station.

4. search_knowledge_base
   Performs semantic search over the ChargeOps technical knowledge base.

5. diagnose_charging_issue
   Performs structured fault diagnosis and records the diagnosis
   as an operational incident.

GENERAL QUESTIONS:

For simple general questions such as:
"What is OCPP?"

Answer directly without tools when specialized evidence is unnecessary.

TECHNICAL KNOWLEDGE QUESTIONS:

When the user asks for technical troubleshooting guidance, failure modes,
operational procedures, or asks what the ChargeOps knowledge base says,
use search_knowledge_base.

STATION-SPECIFIC QUESTIONS:

If the question requires information about the selected station,
call get_station_details first.

INCIDENT HISTORY:

For questions about previous faults, recurring issues, or incident history:

1. Call get_station_details.
2. Call get_recent_incidents.

STATION-SPECIFIC DIAGNOSIS:

For troubleshooting a specific station:

1. Call get_station_details.
2. Call search_knowledge_base using the reported fault as the query.
3. Call diagnose_charging_issue.

The diagnosis should be grounded in the retrieved technical evidence.

WEATHER QUESTIONS:

If the user explicitly asks about current weather or environmental
conditions:

1. Call get_station_details.
2. Call get_station_weather.

WEATHER + DIAGNOSIS:

If the user asks whether current weather may contribute to a fault
and also requests diagnosis:

1. Call get_station_details.
2. Call get_station_weather.
3. Call search_knowledge_base.
4. Call diagnose_charging_issue.

HISTORY + DIAGNOSIS:

If the user asks whether a current fault resembles previous problems:

1. Call get_station_details.
2. Call get_recent_incidents.
3. Call search_knowledge_base.
4. Call diagnose_charging_issue if diagnosis is requested.

IMPORTANT:

- Never invent station information.
- Never invent current weather.
- Never invent incident history.
- Never invent retrieved knowledge.
- Treat PostgreSQL station and incident information as trusted.
- Treat retrieved knowledge as supporting technical evidence.
- Do not claim that a knowledge source says something unless it was
  actually returned by search_knowledge_base.
- When knowledge is used, mention the relevant knowledge title or titles
  in the final response.
- Separate evidence from inference.
- Clearly state uncertainty.
- Do not call the weather tool merely because an over-temperature
  fault exists.
- Give practical and technically accurate responses.
"""


# =================================================
# Station tool
# =================================================


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
                f"Station {station_id} was not found."
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


# =================================================
# Incident history tool
# =================================================


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


# =================================================
# Weather tool
# =================================================


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


# =================================================
# Knowledge / RAG retrieval tool
# =================================================


async def execute_knowledge_tool(
    session: AsyncSession,
    query: str,
) -> tuple[
    dict,
    list[KnowledgeSearchResult],
    ToolTrace,
]:
    results = await search_knowledge(
        session=session,
        query=query,
        limit=4,
    )

    result_items = [
        item.model_dump()
        for item in results
    ]

    result = {
        "query": query,
        "count": len(results),
        "results": result_items,
    }

    if results:
        titles = ", ".join(
            (
                f"{item.title} "
                f"({item.similarity:.0%})"
            )
            for item in results
        )

        summary = (
            f"Retrieved {len(results)} knowledge "
            f"result(s): {titles}"
        )

    else:
        summary = (
            "No relevant knowledge results were found."
        )

    trace = ToolTrace(
        tool="search_knowledge_base",
        status="success",
        summary=summary,
    )

    return result, results, trace


# =================================================
# Diagnostic tool
# =================================================


async def execute_diagnostic_tool(
    session: AsyncSession,
    station: Station,
    issue: str,
    knowledge_context: list[
        KnowledgeSearchResult
    ],
) -> tuple[
    dict,
    ToolTrace,
]:
    if knowledge_context:
        knowledge_text = "\n\n".join(
            (
                f"[Knowledge {index}]\n"
                f"Title: {item.title}\n"
                f"Category: {item.category}\n"
                f"Source: {item.source}\n"
                f"Similarity: {item.similarity:.4f}\n"
                f"Content: {item.content}"
            )
            for index, item
            in enumerate(
                knowledge_context,
                start=1,
            )
        )

    else:
        knowledge_text = (
            "No relevant ChargeOps knowledge "
            "was retrieved."
        )

    context = (
        "TRUSTED STATION DATA\n"
        f"Station ID: {station.station_id}\n"
        f"Station name: {station.name}\n"
        f"Charger model: {station.charger_model}\n"
        f"Location: {station.location}\n"
        f"Station status: {station.status}\n\n"
        "REPORTED ISSUE\n"
        f"{issue}\n\n"
        "RETRIEVED CHARGEOPS KNOWLEDGE\n"
        f"{knowledge_text}\n\n"
        "DIAGNOSTIC INSTRUCTION\n"
        "Use the retrieved knowledge as supporting technical evidence. "
        "Do not invent facts that are not supported by the station data, "
        "reported issue, or retrieved evidence. "
        "Where evidence is insufficient, express uncertainty."
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

    result["knowledge_sources"] = [
        {
            "title": item.title,
            "source": item.source,
            "similarity": item.similarity,
        }
        for item in knowledge_context
    ]

    trace = ToolTrace(
        tool="diagnose_charging_issue",
        status="success",
        summary=(
            f"Incident #{incident.id} recorded | "
            f"{analysis.category} | "
            f"severity: {analysis.severity} | "
            f"confidence: {analysis.confidence:.0%} | "
            f"{len(knowledge_context)} knowledge source(s)"
        ),
    )

    return result, trace


# =================================================
# Main agent loop
# =================================================


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
                "Retrieve trusted operational and technical "
                "information using tools when required.\n\n"
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

    knowledge_context: (
        list[KnowledgeSearchResult] | None
    ) = None

    try:
        response = await client.responses.create(
            model=settings.openai_model,
            instructions=AGENT_INSTRUCTIONS,
            tools=TOOLS,
            tool_choice="auto",
            parallel_tool_calls=False,
            input=input_items,
        )

        for _ in range(12):
            # Preserve model output for the next turn.
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

            # -----------------------------------------
            # No more tool calls = final answer
            # -----------------------------------------

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

                # =====================================
                # Station
                # =====================================

                if (
                    tool_call.name
                    == "get_station_details"
                ):
                    (
                        tool_result,
                        station_context,
                        tool_trace,
                    ) = await execute_station_tool(
                        session=session,
                        station_id=station_id,
                    )

                # =====================================
                # Incident history
                # =====================================

                elif (
                    tool_call.name
                    == "get_recent_incidents"
                ):
                    if station_context is None:
                        tool_result = {
                            "error": (
                                "Station details must "
                                "be loaded first."
                            )
                        }

                        tool_trace = ToolTrace(
                            tool="get_recent_incidents",
                            status="error",
                            summary=(
                                "Station context is "
                                "not loaded."
                            ),
                        )

                    else:
                        (
                            tool_result,
                            tool_trace,
                        ) = (
                            await execute_incident_history_tool(
                                session=session,
                                station=station_context,
                            )
                        )

                # =====================================
                # Weather
                # =====================================

                elif (
                    tool_call.name
                    == "get_station_weather"
                ):
                    if station_context is None:
                        tool_result = {
                            "error": (
                                "Station details must "
                                "be loaded first."
                            )
                        }

                        tool_trace = ToolTrace(
                            tool="get_station_weather",
                            status="error",
                            summary=(
                                "Station context is "
                                "not loaded."
                            ),
                        )

                    else:
                        (
                            tool_result,
                            tool_trace,
                        ) = await execute_weather_tool(
                            station_context
                        )

                # =====================================
                # Knowledge retrieval / RAG
                # =====================================

                elif (
                    tool_call.name
                    == "search_knowledge_base"
                ):
                    arguments = (
                        KnowledgeToolArguments
                        .model_validate_json(
                            tool_call.arguments
                        )
                    )

                    (
                        tool_result,
                        knowledge_context,
                        tool_trace,
                    ) = await execute_knowledge_tool(
                        session=session,
                        query=arguments.query,
                    )

                # =====================================
                # Diagnosis
                # =====================================

                elif (
                    tool_call.name
                    == "diagnose_charging_issue"
                ):
                    if station_context is None:
                        tool_result = {
                            "error": (
                                "Station details must "
                                "be loaded before diagnosis."
                            )
                        }

                        tool_trace = ToolTrace(
                            tool=(
                                "diagnose_charging_issue"
                            ),
                            status="error",
                            summary=(
                                "Station context is "
                                "not loaded."
                            ),
                        )

                    elif knowledge_context is None:
                        tool_result = {
                            "error": (
                                "Technical knowledge must "
                                "be retrieved before diagnosis. "
                                "Call search_knowledge_base first."
                            )
                        }

                        tool_trace = ToolTrace(
                            tool=(
                                "diagnose_charging_issue"
                            ),
                            status="error",
                            summary=(
                                "Knowledge retrieval must "
                                "happen before diagnosis."
                            ),
                        )

                    else:
                        arguments = (
                            DiagnosticToolArguments
                            .model_validate_json(
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
                            knowledge_context=(
                                knowledge_context
                            ),
                        )

                # =====================================
                # Unknown tool
                # =====================================

                else:
                    raise AgentServiceError(
                        f"Unknown tool requested: "
                        f"{tool_call.name}"
                    )

                if (
                    tool_call.name
                    not in used_tools
                ):
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
                            "type": (
                                "function_call_output"
                            ),
                            "call_id": (
                                tool_call.call_id
                            ),
                            "output": json.dumps(
                                tool_result,
                                default=str,
                            ),
                        },
                    )
                )

            # -----------------------------------------
            # Send tool outputs back to model
            # -----------------------------------------

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
        EmbeddingServiceError,
        KnowledgeServiceError,
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