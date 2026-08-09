from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.knowledge import (
    KnowledgeSearchResult,
)
from app.services.knowledge_service import (
    KnowledgeServiceError,
)

client = TestClient(app)


def test_knowledge_search() -> None:
    result = KnowledgeSearchResult(
        id=1,
        document_key=(
            "ocpp-connectivity-001"
        ),
        title=(
            "OCPP Connectivity Troubleshooting"
        ),
        category="network",
        source=(
            "ChargeOps Demo Knowledge Base"
        ),
        content=(
            "Check network and WebSocket "
            "connectivity."
        ),
        similarity=0.91,
    )

    with patch(
        "app.api.knowledge.search_knowledge",
        new=AsyncMock(
            return_value=[result]
        ),
    ):
        response = client.post(
            "/knowledge/search",
            json={
                "query": (
                    "Why does my charger "
                    "keep losing OCPP?"
                ),
                "limit": 5,
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert len(data["results"]) == 1

    assert (
        data["results"][0]["category"]
        == "network"
    )


def test_knowledge_search_validation() -> None:
    response = client.post(
        "/knowledge/search",
        json={
            "query": "x",
        },
    )

    assert response.status_code == 422


def test_knowledge_search_failure() -> None:
    with patch(
        "app.api.knowledge.search_knowledge",
        new=AsyncMock(
            side_effect=KnowledgeServiceError(
                "Could not search the knowledge base."
            )
        ),
    ):
        response = client.post(
            "/knowledge/search",
            json={
                "query": (
                    "How do I troubleshoot "
                    "a charger?"
                )
            },
        )

    assert response.status_code == 503