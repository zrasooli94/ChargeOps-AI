import json
import logging

from langgraph.errors import (
    GraphRecursionError,
)
from openai import OpenAIError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.chargeops_graph import (
    run_chargeops_graph,
)
from app.schemas.agent import ToolTrace
from app.services.embedding_service import (
    EmbeddingServiceError,
)
from app.services.knowledge_service import (
    KnowledgeServiceError,
)
from app.services.llm_service import (
    LLMServiceError,
)
from app.services.weather_service import (
    WeatherServiceError,
)

logger = logging.getLogger(__name__)


class AgentServiceError(Exception):
    """Raised when ChargeOps cannot complete a request."""


async def run_agent(
    message: str,
    station_id: str,
    session: AsyncSession,
) -> tuple[
    str,
    list[str],
    list[ToolTrace],
]:
    try:
        return await run_chargeops_graph(
            message=message,
            station_id=station_id,
            session=session,
        )

    except (
        OpenAIError,
        WeatherServiceError,
        LLMServiceError,
        EmbeddingServiceError,
        KnowledgeServiceError,
        SQLAlchemyError,
        ValidationError,
        json.JSONDecodeError,
        GraphRecursionError,
        RuntimeError,
        KeyError,
        TypeError,
    ) as error:
        logger.exception(
            "ChargeOps LangGraph execution failed"
        )

        raise AgentServiceError(
            "ChargeOps agent could not complete "
            "the request."
        ) from error