from typing import Any, TypedDict

from openai.types.responses import (
    FunctionToolParam,
)
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.agent import ToolTrace
from app.schemas.knowledge import (
    KnowledgeSearchResult,
)
from app.services.incident_service import (
    create_incident,
    get_recent_incidents,
)
from app.services.knowledge_service import (
    search_knowledge,
)
from app.services.llm_service import (
    analyze_charging_issue,
)
from app.services.station_service import (
    get_station,
)
from app.services.weather_service import (
    get_current_weather,
)

# =================================================
# Serializable station context
# =================================================


class StationContext(TypedDict):
    station_id: str
    name: str
    charger_model: str
    location: str
    latitude: float
    longitude: float
    status: str


# =================================================
# Tool argument schemas
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

    category: str | None = Field(
        default=None,
        max_length=100,
    )

    document_id: int | None = Field(
        default=None,
        ge=1,
    )


# =================================================
# OpenAI tool definitions
# =================================================


STATION_TOOL: FunctionToolParam = {
    "type": "function",
    "name": "get_station_details",
    "description": (
        "Retrieve trusted information about the selected "
        "EV charging station from PostgreSQL."
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
        "Retrieve recent incidents for the selected charging "
        "station. Use for historical faults, recurring problems, "
        "and previous incidents."
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
        "Retrieve current real-world weather for the selected "
        "station. Use only when current environmental conditions "
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


KNOWLEDGE_TOOL: FunctionToolParam = {
    "type": "function",
    "name": "search_knowledge_base",
    "description": (
        "Search the ChargeOps EV charging technical knowledge "
        "base using semantic vector retrieval."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Focused semantic search query describing "
                    "the technical information needed."
                ),
            },
            "category": {
                "type": [
                    "string",
                    "null",
                ],
                "description": (
                    "Optional knowledge category filter, "
                    "or null."
                ),
            },
            "document_id": {
                "type": [
                    "integer",
                    "null",
                ],
                "description": (
                    "Optional uploaded knowledge document ID, "
                    "or null."
                ),
            },
        },
        "required": [
            "query",
            "category",
            "document_id",
        ],
        "additionalProperties": False,
    },
    "strict": True,
}


DIAGNOSTIC_TOOL: FunctionToolParam = {
    "type": "function",
    "name": "diagnose_charging_issue",
    "description": (
        "Perform structured technical diagnosis of an EV "
        "charging fault and record the successful diagnosis "
        "as an operational incident."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "issue": {
                "type": "string",
                "description": (
                    "Charging issue requiring diagnosis."
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
   as an incident.

GENERAL QUESTIONS:

For simple general questions such as:
"What is OCPP?"

Answer directly without tools when specialized evidence is unnecessary.

TECHNICAL KNOWLEDGE QUESTIONS:

When the user requests technical troubleshooting guidance, failure modes,
manual information, operational procedures, or asks what the ChargeOps
knowledge base says, use search_knowledge_base.

STATION-SPECIFIC QUESTIONS:

If the question requires information about the selected station,
call get_station_details first.

INCIDENT HISTORY:

For previous faults, recurring issues, or incident history:

1. Call get_station_details.
2. Call get_recent_incidents.

STATION-SPECIFIC DIAGNOSIS:

For troubleshooting a specific station:

1. Call get_station_details.
2. Call search_knowledge_base.
3. Call diagnose_charging_issue.

WEATHER QUESTIONS:

When current environmental conditions are explicitly relevant:

1. Call get_station_details.
2. Call get_station_weather.

WEATHER + DIAGNOSIS:

1. Call get_station_details.
2. Call get_station_weather.
3. Call search_knowledge_base.
4. Call diagnose_charging_issue.

HISTORY + DIAGNOSIS:

1. Call get_station_details.
2. Call get_recent_incidents.
3. Call search_knowledge_base.
4. Call diagnose_charging_issue if diagnosis is requested.

KNOWLEDGE CITATIONS:

Retrieved evidence has citation identifiers such as KB1 and KB2.

When relying on retrieved evidence:

- Cite supporting claims using [KB1], [KB2], etc.
- Never invent citation identifiers.
- Cite only evidence actually returned by the knowledge tool.
- At the end include a short "Knowledge sources" section.
- Distinguish retrieved evidence from technical inference.

If no knowledge result passes the retrieval threshold, explicitly say
that sufficiently relevant evidence was not retrieved.

IMPORTANT:

- Never invent station information.
- Never invent weather.
- Never invent incident history.
- Never invent retrieved knowledge.
- Separate evidence from inference.
- Clearly state uncertainty.
- Do not call weather merely because an over-temperature fault exists.
"""


# =================================================
# Station tool
# =================================================


async def execute_station_tool(
    session: AsyncSession,
    station_id: str,
) -> tuple[
    dict[str, Any],
    StationContext | None,
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

    station_context: StationContext = {
        "station_id": station.station_id,
        "name": station.name,
        "charger_model": station.charger_model,
        "location": station.location,
        "latitude": station.latitude,
        "longitude": station.longitude,
        "status": station.status,
    }

    result: dict[str, Any] = {
        "found": True,
        **station_context,
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

    return (
        result,
        station_context,
        trace,
    )


# =================================================
# Incident history
# =================================================


async def execute_incident_history_tool(
    session: AsyncSession,
    station: StationContext,
) -> tuple[
    dict[str, Any],
    ToolTrace,
]:
    incidents = await get_recent_incidents(
        session=session,
        station_id=station["station_id"],
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
        "station_id": station["station_id"],
        "count": len(items),
        "incidents": items,
    }

    trace = ToolTrace(
        tool="get_recent_incidents",
        status="success",
        summary=(
            f"Retrieved {len(items)} recent "
            f"incident(s) for "
            f"{station['station_id']}."
        ),
    )

    return result, trace


# =================================================
# Weather
# =================================================


async def execute_weather_tool(
    station: StationContext,
) -> tuple[
    dict[str, Any],
    ToolTrace,
]:
    observed_at, weather = await get_current_weather(
        latitude=station["latitude"],
        longitude=station["longitude"],
    )

    result = {
        "station_id": station["station_id"],
        "location": station["location"],
        "observed_at": observed_at.isoformat(),
        "weather": weather.model_dump(),
    }

    trace = ToolTrace(
        tool="get_station_weather",
        status="success",
        summary=(
            f"Temperature {weather.temperature_c}°C, "
            f"precipitation "
            f"{weather.precipitation_mm} mm, "
            f"wind {weather.wind_speed_kmh} km/h"
        ),
    )

    return result, trace


# =================================================
# Knowledge retrieval
# =================================================


async def execute_knowledge_tool(
    session: AsyncSession,
    query: str,
    category: str | None = None,
    document_id: int | None = None,
) -> tuple[
    dict[str, Any],
    list[KnowledgeSearchResult],
    ToolTrace,
]:
    results = await search_knowledge(
        session=session,
        query=query,
        limit=5,
        min_similarity=(
            settings.knowledge_min_similarity
        ),
        category=category,
        document_id=document_id,
        max_chunks_per_document=(
            settings
            .knowledge_max_chunks_per_document
        ),
    )

    result_items = [
        item.model_dump()
        for item in results
    ]

    result: dict[str, Any] = {
        "query": query,
        "category_filter": category,
        "document_filter": document_id,
        "count": len(results),
        "results": result_items,
    }

    if results:
        sources = ", ".join(
            (
                f"[{item.citation_id}] "
                f"{item.title} "
                f"({item.similarity:.0%})"
            )
            for item in results
        )

        summary = (
            f"Retrieved {len(results)} "
            f"qualified knowledge result(s): "
            f"{sources}"
        )

    else:
        summary = (
            "No knowledge chunks met the "
            "retrieval quality threshold."
        )

    trace = ToolTrace(
        tool="search_knowledge_base",
        status="success",
        summary=summary,
    )

    return (
        result,
        results,
        trace,
    )


# =================================================
# Diagnosis
# =================================================


async def execute_diagnostic_tool(
    session: AsyncSession,
    station: StationContext,
    issue: str,
    knowledge_context: list[
        KnowledgeSearchResult
    ],
) -> tuple[
    dict[str, Any],
    ToolTrace,
]:
    if knowledge_context:
        knowledge_text = "\n\n".join(
            (
                f"[{item.citation_id}]\n"
                f"Title: {item.title}\n"
                f"Category: {item.category}\n"
                f"Source: {item.source}\n"
                f"Page: "
                f"{item.page_number or 'Unknown'}\n"
                f"Similarity: "
                f"{item.similarity:.4f}\n"
                f"Content: {item.content}"
            )
            for item
            in knowledge_context
        )

    else:
        knowledge_text = (
            "No knowledge chunks passed the "
            "retrieval quality threshold."
        )

    context = (
        "TRUSTED STATION DATA\n"
        f"Station ID: "
        f"{station['station_id']}\n"
        f"Station name: "
        f"{station['name']}\n"
        f"Charger model: "
        f"{station['charger_model']}\n"
        f"Location: "
        f"{station['location']}\n"
        f"Station status: "
        f"{station['status']}\n\n"
        "REPORTED ISSUE\n"
        f"{issue}\n\n"
        "RETRIEVED CHARGEOPS KNOWLEDGE\n"
        f"{knowledge_text}\n\n"
        "DIAGNOSTIC INSTRUCTION\n"
        "Use retrieved knowledge as supporting "
        "technical evidence. Do not invent facts. "
        "Express uncertainty where evidence "
        "is insufficient."
    )

    analysis = await analyze_charging_issue(
        context
    )

    incident = await create_incident(
        session=session,
        station_id=station["station_id"],
        issue=issue,
        analysis=analysis,
    )

    result: dict[str, Any] = (
        analysis.model_dump()
    )

    result["incident_id"] = (
        incident.id
    )

    result["incident_status"] = (
        incident.status
    )

    result["knowledge_sources"] = [
        {
            "citation_id": (
                item.citation_id
            ),
            "title": item.title,
            "source": item.source,
            "page_number": (
                item.page_number
            ),
            "similarity": (
                item.similarity
            ),
        }
        for item
        in knowledge_context
    ]

    trace = ToolTrace(
        tool="diagnose_charging_issue",
        status="success",
        summary=(
            f"Incident #{incident.id} recorded | "
            f"{analysis.category} | "
            f"severity: {analysis.severity} | "
            f"confidence: "
            f"{analysis.confidence:.0%} | "
            f"{len(knowledge_context)} "
            f"knowledge source(s)"
        ),
    )

    return result, trace