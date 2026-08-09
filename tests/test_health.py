from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.analysis import ChargingIssueAnalysis
from app.services.llm_service import LLMServiceError

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["app"] == "ChargeOps AI"


def test_chat_success() -> None:
    with patch(
        "app.api.chat.generate_response",
        return_value="Charging demand forecasting predicts future EV charging usage.",
    ):
        response = client.post(
            "/chat",
            json={"message": "What is EV charging demand forecasting?"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Charging demand forecasting predicts future EV charging usage."
    }

def test_chat_rejects_empty_message() -> None:
    response = client.post(
        "/chat",
        json={"message": ""},
    )

    assert response.status_code == 422


def test_chat_rejects_missing_message() -> None:
    response = client.post(
        "/chat",
        json={},
    )

    assert response.status_code == 422

def test_chat_llm_error() -> None:
    with patch(
        "app.api.chat.generate_response",
        side_effect=LLMServiceError("Failed to generate an AI response."),
    ):
        response = client.post(
            "/chat",
            json={"message": "Hello"},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "Failed to generate an AI response."

def test_analyze_success() -> None:
    mock_result = ChargingIssueAnalysis(
        category="network",
        severity="high",
        confidence=0.95,
        summary="The charger cannot connect to the OCPP backend.",
        likely_causes=[
            "Backend connectivity failure",
            "Incorrect OCPP configuration",
        ],
        diagnostic_steps=[
            {
                "step": 1,
                "action": "Verify the OCPP endpoint.",
            },
            {
                "step": 2,
                "action": "Test backend connectivity.",
            },
        ],
        needs_human_escalation=False,
    )

    with patch(
        "app.api.analysis.analyze_charging_issue",
        new=AsyncMock(return_value=mock_result),
    ):
        response = client.post(
            "/analyze",
            json={
                "message": "The charger cannot connect to the backend."
            },
        )

    assert response.status_code == 200
    assert response.json()["category"] == "network"
    assert response.json()["severity"] == "high"
    assert response.json()["confidence"] == 0.95
    assert response.json()["needs_human_escalation"] is False


def test_analyze_rejects_empty_message() -> None:
    response = client.post(
        "/analyze",
        json={"message": ""},
    )

    assert response.status_code == 422