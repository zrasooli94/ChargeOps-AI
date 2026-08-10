import json
from dataclasses import dataclass
from typing import (
    Any,
    Literal,
    cast,
)

from langgraph.graph import (
    START,
    StateGraph,
)
from langgraph.runtime import Runtime
from openai.types.responses import (
    ResponseInputItemParam,
    ResponseInputParam,
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import TypedDict

from app.core.checkpointing import (
    get_checkpointer,
)
from app.core.config import settings
from app.core.openai_client import client
from app.schemas.agent import ToolTrace
from app.schemas.knowledge import (
    KnowledgeSearchResult,
)
from app.services.agent_tools import (
    AGENT_INSTRUCTIONS,
    TOOLS,
    DiagnosticToolArguments,
    KnowledgeToolArguments,
    StationContext,
    execute_diagnostic_tool,
    execute_incident_history_tool,
    execute_knowledge_tool,
    execute_station_tool,
    execute_weather_tool,
)

MAX_TOOL_ITERATIONS = 12


# =================================================
# Runtime dependencies
# =================================================


@dataclass
class AgentRuntimeContext:
    session: AsyncSession


# =================================================
# Graph state
# =================================================


class ChargeOpsState(TypedDict):
    station_id: str
    message: str

    input_items: list[
        dict[str, Any]
    ]

    pending_calls: list[
        dict[str, Any]
    ]

    station_context: (
        StationContext | None
    )

    knowledge_context: list[
        dict[str, Any]
    ]

    knowledge_retrieved: bool

    used_tools: list[str]

    traces: list[
        dict[str, Any]
    ]

    final_answer: str

    iteration_count: int


# =================================================
# Model node
# =================================================


async def call_model_node(
    state: ChargeOpsState,
) -> dict[str, Any]:
    response = await client.responses.create(
        model=settings.openai_model,
        instructions=AGENT_INSTRUCTIONS,
        tools=TOOLS,
        tool_choice="auto",
        parallel_tool_calls=False,
        input=cast(
            ResponseInputParam,
            state["input_items"],
        ),
    )

    input_items = list(
        state["input_items"]
    )

    pending_calls: list[
        dict[str, Any]
    ] = []

    for item in response.output:
        input_items.append(
            cast(
                dict[str, Any],
                item.to_dict(),
            )
        )

        if item.type == "function_call":
            pending_calls.append(
                {
                    "name": item.name,
                    "arguments": (
                        item.arguments
                    ),
                    "call_id": (
                        item.call_id
                    ),
                }
            )

    final_answer = ""

    if not pending_calls:
        final_answer = (
            response.output_text
            or ""
        )

        if not final_answer:
            raise RuntimeError(
                "Agent returned no final response."
            )

    return {
        "input_items": input_items,
        "pending_calls": pending_calls,
        "final_answer": final_answer,
    }


# =================================================
# Routing
# =================================================


def route_after_model(
    state: ChargeOpsState,
) -> Literal[
    "execute_tools",
    "__end__",
]:
    if state["pending_calls"]:
        return "execute_tools"

    return "__end__"


# =================================================
# Tool execution node
# =================================================


async def execute_tools_node(
    state: ChargeOpsState,
    runtime: Runtime[
        AgentRuntimeContext
    ],
) -> dict[str, Any]:
    if (
        state["iteration_count"]
        >= MAX_TOOL_ITERATIONS
    ):
        raise RuntimeError(
            "Agent exceeded maximum "
            "tool iterations."
        )

    session = runtime.context.session

    station_context = (
        state["station_context"]
    )

    knowledge_context = [
        KnowledgeSearchResult
        .model_validate(item)
        for item
        in state["knowledge_context"]
    ]

    knowledge_retrieved = (
        state["knowledge_retrieved"]
    )

    used_tools = list(
        state["used_tools"]
    )

    traces = list(
        state["traces"]
    )

    input_items = list(
        state["input_items"]
    )

    for tool_call in state[
        "pending_calls"
    ]:
        tool_name = cast(
            str,
            tool_call["name"],
        )

        call_id = cast(
            str,
            tool_call["call_id"],
        )

        arguments_json = cast(
            str,
            tool_call["arguments"],
        )

        # =========================================
        # Station
        # =========================================

        if (
            tool_name
            == "get_station_details"
        ):
            (
                tool_result,
                station_context,
                tool_trace,
            ) = await execute_station_tool(
                session=session,
                station_id=(
                    state["station_id"]
                ),
            )

        # =========================================
        # Incident history
        # =========================================

        elif (
            tool_name
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
                    tool=tool_name,
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

        # =========================================
        # Weather
        # =========================================

        elif (
            tool_name
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
                    tool=tool_name,
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
                    await execute_weather_tool(
                        station_context
                    )
                )

        # =========================================
        # RAG
        # =========================================

        elif (
            tool_name
            == "search_knowledge_base"
        ):
            arguments = (
                KnowledgeToolArguments
                .model_validate_json(
                    arguments_json
                )
            )

            (
                tool_result,
                retrieved_knowledge,
                tool_trace,
            ) = await execute_knowledge_tool(
                session=session,
                query=arguments.query,
                category=(
                    arguments.category
                ),
                document_id=(
                    arguments.document_id
                ),
            )

            knowledge_context = (
                retrieved_knowledge
            )

            knowledge_retrieved = True

        # =========================================
        # Diagnosis
        # =========================================

        elif (
            tool_name
            == "diagnose_charging_issue"
        ):
            if station_context is None:
                tool_result = {
                    "error": (
                        "Station details must "
                        "be loaded before "
                        "diagnosis."
                    )
                }

                tool_trace = ToolTrace(
                    tool=tool_name,
                    status="error",
                    summary=(
                        "Station context is "
                        "not loaded."
                    ),
                )

            elif not knowledge_retrieved:
                tool_result = {
                    "error": (
                        "Technical knowledge "
                        "must be retrieved "
                        "before diagnosis."
                    )
                }

                tool_trace = ToolTrace(
                    tool=tool_name,
                    status="error",
                    summary=(
                        "Knowledge retrieval "
                        "must happen before "
                        "diagnosis."
                    ),
                )

            else:
                arguments = (
                    DiagnosticToolArguments
                    .model_validate_json(
                        arguments_json
                    )
                )

                (
                    tool_result,
                    tool_trace,
                ) = (
                    await execute_diagnostic_tool(
                        session=session,
                        station=station_context,
                        issue=(
                            arguments.issue
                        ),
                        knowledge_context=(
                            knowledge_context
                        ),
                    )
                )

        # =========================================
        # Unknown tool
        # =========================================

        else:
            raise RuntimeError(
                "Unknown tool requested: "
                f"{tool_name}"
            )

        if tool_name not in used_tools:
            used_tools.append(
                tool_name
            )

        traces.append(
            tool_trace.model_dump()
        )

        input_items.append(
            {
                "type": (
                    "function_call_output"
                ),
                "call_id": call_id,
                "output": json.dumps(
                    tool_result,
                    default=str,
                ),
            }
        )

    return {
        "input_items": input_items,
        "pending_calls": [],
        "station_context": (
            station_context
        ),
        "knowledge_context": [
            item.model_dump()
            for item
            in knowledge_context
        ],
        "knowledge_retrieved": (
            knowledge_retrieved
        ),
        "used_tools": used_tools,
        "traces": traces,
        "iteration_count": (
            state["iteration_count"]
            + 1
        ),
    }


# =================================================
# Graph construction
# =================================================


builder = StateGraph(
    ChargeOpsState,
    context_schema=AgentRuntimeContext,
)

builder.add_node(
    "call_model",
    call_model_node,
)

builder.add_node(
    "execute_tools",
    execute_tools_node,
)

builder.add_edge(
    START,
    "call_model",
)

builder.add_conditional_edges(
    "call_model",
    route_after_model,
)

builder.add_edge(
    "execute_tools",
    "call_model",
)


_chargeops_graph: Any | None = None


def build_chargeops_graph(
    checkpointer: Any | None = None,
) -> Any:
    return builder.compile(
        checkpointer=checkpointer,
        name="chargeops-agent",
    )


def get_chargeops_graph() -> Any:
    global _chargeops_graph

    if _chargeops_graph is None:
        _chargeops_graph = (
            build_chargeops_graph(
                checkpointer=(
                    get_checkpointer()
                )
            )
        )

    return _chargeops_graph


# =================================================
# Public graph runner
# =================================================



async def run_chargeops_graph(
    message: str,
    station_id: str,
    session: AsyncSession,
    thread_id: str,
) -> tuple[
    str,
    list[str],
    list[ToolTrace],
]:
    graph = get_chargeops_graph()

    config = {
        "configurable": {
            "thread_id": thread_id,
        },
        "recursion_limit": 30,
    }

    # =============================================
    # Load previous thread memory
    # =============================================

    previous_snapshot = (
        await graph.aget_state(
            config
        )
    )

    previous_values = (
        previous_snapshot.values
        or {}
    )

    previous_station_id = (
        previous_values.get(
            "station_id"
        )
    )

    # A conversation is bound to one station.
    if (
        previous_station_id
        and previous_station_id
        != station_id
    ):
        raise RuntimeError(
            "This conversation thread "
            "belongs to a different "
            "charging station."
        )

    previous_input_items = cast(
        list[dict[str, Any]],
        previous_values.get(
            "input_items",
            [],
        ),
    )

    # =============================================
    # Add new user turn
    # =============================================

    user_item: ResponseInputItemParam = cast(
        ResponseInputItemParam,
        {
            "role": "user",
            "content": (
                "Trusted application context:\n"
                f"Selected station ID: "
                f"{station_id}\n\n"
                "Retrieve trusted operational "
                "and technical information using "
                "tools when required.\n\n"
                "User request:\n"
                f"{message}"
            ),
        },
    )

    conversation_items = [
        *previous_input_items,
        cast(
            dict[str, Any],
            user_item,
        ),
    ]

    # =============================================
    # Per-turn state
    # =============================================

    initial_state: ChargeOpsState = {
        "station_id": station_id,
        "message": message,
        "input_items": (
            conversation_items
        ),
        "pending_calls": [],
        "station_context": None,
        "knowledge_context": [],
        "knowledge_retrieved": False,
        "used_tools": [],
        "traces": [],
        "final_answer": "",
        "iteration_count": 0,
    }

    # =============================================
    # Continue this thread
    # =============================================

    result = await graph.ainvoke(
        initial_state,
        context=AgentRuntimeContext(
            session=session
        ),
        config=config,
    )

    final_answer = cast(
        str,
        result["final_answer"],
    )

    used_tools = cast(
        list[str],
        result["used_tools"],
    )

    traces = [
        ToolTrace.model_validate(
            trace
        )
        for trace
        in result["traces"]
    ]

    return (
        final_answer,
        used_tools,
        traces,
    )