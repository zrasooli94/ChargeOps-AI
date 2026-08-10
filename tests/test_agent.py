from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.agent import ToolTrace
from app.services.agent_service import AgentServiceError

client = TestClient(app)


def test_agent_success() -> None:
    test_thread_id = (
        "550e8400-e29b-41d4-a716-446655440000"
    )

    with patch(
        "app.api.agent.run_agent",
        new=AsyncMock(
            return_value=(
                "Station KL-205 is currently active.",
                [
                    "get_station_details",
                ],
                [
                    ToolTrace(
                        tool="get_station_details",
                        status="success",
                        summary=(
                            "KL-205 | ABB Terra 54 | "
                            "Kuala Lumpur, Malaysia | "
                            "status: active"
                        ),
                    )
                ],
                None,
                [],
            )
        ),
    ) as mocked_agent:
        response = client.post(
            "/agent/run",
            json={
                "station_id": "kl-205",
                "message": (
                    "Tell me about this charging station."
                ),
                "thread_id": test_thread_id,
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["thread_id"]
        == test_thread_id
    )

    assert (
        data["answer"]
        == "Station KL-205 is currently active."
    )

    assert data["used_tools"] == [
        "get_station_details"
    ]

    assert len(data["trace"]) == 1

    assert (
        data["trace"][0]["tool"]
        == "get_station_details"
    )

    assert (
        data["trace"][0]["status"]
        == "success"
    )

    call = mocked_agent.await_args

    assert call is not None

    assert (
        call.kwargs["station_id"]
        == "KL-205"
    )

    assert (
        call.kwargs["message"]
        == "Tell me about this charging station."
    )

    assert (
        call.kwargs["thread_id"]
        == test_thread_id
    )

    assert (
        call.kwargs["session"]
        is not None
    )

def test_agent_failure() -> None:
    with patch(
        "app.api.agent.run_agent",
        new=AsyncMock(
            side_effect=AgentServiceError(
                "ChargeOps agent could not complete the request."
            )
        ),
    ):
        response = client.post(
            "/agent/run",
            json={
                "station_id": "KL-205",
                "message": "Analyze this station.",
            },
        )

    assert response.status_code == 503


def test_agent_normalizes_station_id() -> None:
    with patch(
        "app.api.agent.run_agent",
        new=AsyncMock(
            return_value=(
                "Station loaded.",
                [],
                [],
                None,
                [],
            )
        ),
    ) as mocked_agent:
        response = client.post(
            "/agent/run",
            json={
                "station_id": "  kl-205  ",
                "message": (
                    "Tell me about this station."
                ),
            },
        )

    assert response.status_code == 200

    mocked_agent.assert_awaited_once()

    call = mocked_agent.await_args

    assert call is not None

    assert call.kwargs["station_id"] == "KL-205"
    assert (
        call.kwargs["message"]
        == "Tell me about this station."
    )
    assert "session" in call.kwargs


def test_agent_rejects_client_station_metadata() -> None:
    response = client.post(
        "/agent/run",
        json={
            "station_id": "KL-205",
            "message": "Tell me about this station.",
            "charger_model": "Fake Charger",
            "latitude": 99.0,
            "longitude": 99.0,
        },
    )

    assert response.status_code == 422