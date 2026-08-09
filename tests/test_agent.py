from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.agent import ToolTrace
from app.services.agent_service import AgentServiceError

client = TestClient(app)


def test_agent_success() -> None:
    with patch(
        "app.api.agent.run_agent",
        new=AsyncMock(
            return_value=(
                "Current hot weather may contribute to thermal stress.",
                ["get_station_weather"],
                [
                    ToolTrace(
                        tool="get_station_weather",
                        status="success",
                        summary="31.5°C, precipitation 0 mm, wind 8 km/h",
                    ),
                ],
            )
        ),
    ):
        response = client.post(
            "/agent/run",
            json={
                "station_id": "kl-205",
                "latitude": 3.139,
                "longitude": 101.6869,
                "message": (
                    "Could today's weather be contributing "
                    "to overheating?"
                ),
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["station_id"] == "KL-205"
    assert data["used_tools"] == ["get_station_weather"]
    assert data["trace"][0]["tool"] == "get_station_weather"
    assert data["trace"][0]["status"] == "success"


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
                "latitude": 3.139,
                "longitude": 101.6869,
                "message": "Check current weather.",
                "charger_model": "ABB Terra 54",
            },
        )

    assert response.status_code == 503


def test_agent_rejects_invalid_coordinates() -> None:
    response = client.post(
        "/agent/run",
        json={
            "station_id": "KL-205",
            "latitude": 500,
            "longitude": 101.6869,
            "message": "Check the weather.",
            "charger_model": "ABB Terra 54",
        },
    )

    assert response.status_code == 422