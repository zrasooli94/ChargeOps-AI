from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
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