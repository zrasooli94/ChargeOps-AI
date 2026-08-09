import logging

from sqlalchemy import (
    delete,
    select,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import (
    KnowledgeChunk,
    KnowledgeDocument,
)
from app.schemas.knowledge import (
    KnowledgeSearchResult,
)
from app.services.embedding_service import (
    EmbeddingServiceError,
    create_embedding,
)

logger = logging.getLogger(__name__)


class KnowledgeServiceError(Exception):
    """Raised when knowledge operations fail."""


async def search_knowledge(
    session: AsyncSession,
    query: str,
    limit: int = 5,
) -> list[KnowledgeSearchResult]:
    try:
        query_embedding = (
            await create_embedding(
                query
            )
        )

        distance = (
            KnowledgeChunk.embedding
            .cosine_distance(
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

        for (
            chunk,
            distance_value,
        ) in result.all():
            similarity = (
                1.0
                - float(
                    distance_value
                )
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


async def list_knowledge_documents(
    session: AsyncSession,
) -> list[KnowledgeDocument]:
    result = await session.execute(
        select(
            KnowledgeDocument
        ).order_by(
            KnowledgeDocument
            .created_at
            .desc()
        )
    )

    return list(
        result.scalars().all()
    )


async def delete_knowledge_document(
    session: AsyncSession,
    document_id: int,
) -> bool:
    result = await session.execute(
        select(
            KnowledgeDocument
        ).where(
            KnowledgeDocument.id
            == document_id
        )
    )

    document = (
        result.scalar_one_or_none()
    )

    if document is None:
        return False

    await session.execute(
        delete(
            KnowledgeDocument
        ).where(
            KnowledgeDocument.id
            == document_id
        )
    )

    await session.commit()

    return True