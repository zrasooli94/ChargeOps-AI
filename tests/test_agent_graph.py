from app.agents.chargeops_graph import (
    route_after_model,
)


def base_state() -> dict:
    return {
        "station_id": "KL-205",
        "message": "Test message",
        "input_items": [],
        "pending_calls": [],
        "station_context": None,
        "knowledge_context": [],
        "knowledge_retrieved": False,
        "used_tools": [],
        "traces": [],
        "final_answer": "",
        "iteration_count": 0,
    }


def test_graph_routes_to_tools() -> None:
    state = base_state()

    state["pending_calls"] = [
        {
            "name": (
                "get_station_details"
            ),
            "arguments": "{}",
            "call_id": "call-1",
        }
    ]

    route = route_after_model(
        state  # type: ignore[arg-type]
    )

    assert route == "execute_tools"


def test_graph_routes_to_end() -> None:
    state = base_state()

    route = route_after_model(
        state  # type: ignore[arg-type]
    )

    assert route == "__end__"