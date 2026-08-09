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