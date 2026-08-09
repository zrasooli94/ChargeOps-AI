import asyncio
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.knowledge import (
    KnowledgeSearchResult,
)
from app.services.agent_tools import (
    execute_knowledge_tool,
)


def test_execute_knowledge_tool() -> None:
    knowledge_result = KnowledgeSearchResult(
        id=1,
        document_key="thermal-management-001",
        title=(
            "Charger Over-Temperature Troubleshooting"
        ),
        category="hardware",
        source="ChargeOps Demo Knowledge Base",
        content=(
            "Repeated over-temperature warnings "
            "may indicate cooling problems."
        ),
        similarity=0.92,
    )

    mocked_session = AsyncMock(
        spec=AsyncSession
    )

    with patch(
        "app.services.agent_tools.search_knowledge",
        new=AsyncMock(
            return_value=[
                knowledge_result
            ]
        ),
    ):
        result, knowledge, trace = asyncio.run(
            execute_knowledge_tool(
                session=mocked_session,
                query=(
                    "charger stops because "
                    "of overheating"
                ),
            )
        )

    assert result["count"] == 1

    assert len(
        knowledge
    ) == 1

    assert (
        knowledge[0].title
        == "Charger Over-Temperature Troubleshooting"
    )

    assert (
        trace.tool
        == "search_knowledge_base"
    )

    assert (
        trace.status
        == "success"
    )

    assert "92%" in trace.summary