import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeChunk
from app.schemas.knowledge import KnowledgeSearchResult
from app.services.embedding_service import (
    EmbeddingServiceError,
    create_embedding,
)

logger = logging.getLogger(__name__)


class KnowledgeServiceError(Exception):
    """Raised when knowledge retrieval fails."""


async def search_knowledge(
    session: AsyncSession,
    query: str,
    limit: int = 5,
) -> list[KnowledgeSearchResult]:
    try:
        query_embedding = await create_embedding(
            query
        )

        distance = (
            KnowledgeChunk.embedding.cosine_distance(
                query_embedding
            )
        )

        statement = (
            select(
                KnowledgeChunk,
                distance.label(
                    "distance"
                ),
            )
            .order_by(
                distance
            )
            .limit(
                limit
            )
        )

        result = await session.execute(
            statement
        )

        search_results: list[
            KnowledgeSearchResult
        ] = []

        for chunk, distance_value in result.all():
            similarity = (
                1.0
                - float(distance_value)
            )

            search_results.append(
                KnowledgeSearchResult(
                    id=chunk.id,
                    document_key=(
                        chunk.document_key
                    ),
                    title=chunk.title,
                    category=chunk.category,
                    source=chunk.source,
                    content=chunk.content,
                    similarity=round(
                        similarity,
                        4,
                    ),
                )
            )

        return search_results

    except (
        EmbeddingServiceError,
        SQLAlchemyError,
    ) as error:
        logger.exception(
            "Knowledge search failed"
        )

        raise KnowledgeServiceError(
            "Could not search the knowledge base."
        ) from error