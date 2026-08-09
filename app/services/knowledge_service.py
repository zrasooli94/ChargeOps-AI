import hashlib
import logging
from collections import defaultdict

from sqlalchemy import (
    delete,
    func,
    select,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
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


def content_identity(
    content: str,
    stored_hash: str | None,
) -> str:
    if stored_hash:
        return stored_hash

    normalized = " ".join(
        content.lower().split()
    )

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


async def search_knowledge(
    session: AsyncSession,
    query: str,
    limit: int = 5,
    min_similarity: float | None = None,
    category: str | None = None,
    document_id: int | None = None,
    max_chunks_per_document: int | None = None,
) -> list[KnowledgeSearchResult]:
    try:
        threshold = (
            min_similarity
            if min_similarity is not None
            else settings.knowledge_min_similarity
        )

        max_per_document = (
            max_chunks_per_document
            if max_chunks_per_document is not None
            else settings.knowledge_max_chunks_per_document
        )

        query_embedding = await create_embedding(
            query
        )

        distance = (
            KnowledgeChunk.embedding
            .cosine_distance(
                query_embedding
            )
        )

        candidate_limit = min(
            max(
                limit
                * settings.knowledge_candidate_multiplier,
                20,
            ),
            100,
        )

        statement = select(
            KnowledgeChunk,
            distance.label(
                "distance"
            ),
        )

        # -----------------------------------------
        # Metadata filtering
        # -----------------------------------------

        if category:
            statement = statement.where(
                func.lower(
                    KnowledgeChunk.category
                )
                == category.strip().lower()
            )

        if document_id is not None:
            statement = statement.where(
                KnowledgeChunk.knowledge_document_id
                == document_id
            )

        statement = (
            statement
            .order_by(
                distance
            )
            .limit(
                candidate_limit
            )
        )

        result = await session.execute(
            statement
        )

        search_results: list[
            KnowledgeSearchResult
        ] = []

        seen_content: set[str] = set()

        document_counts: dict[
            str,
            int,
        ] = defaultdict(int)

        # -----------------------------------------
        # Retrieval quality controls
        # -----------------------------------------

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

            # Reject weak semantic matches.
            if similarity < threshold:
                continue

            identity = content_identity(
                content=chunk.content,
                stored_hash=(
                    chunk.content_hash
                ),
            )

            # Reject duplicate content.
            if identity in seen_content:
                continue

            # Group uploaded chunks by document.
            if (
                chunk.knowledge_document_id
                is not None
            ):
                document_group = (
                    f"document:"
                    f"{chunk.knowledge_document_id}"
                )

            else:
                # Legacy seeded chunks don't have
                # a parent KnowledgeDocument.
                document_group = (
                    f"legacy:"
                    f"{chunk.document_key}"
                )

            if (
                document_counts[
                    document_group
                ]
                >= max_per_document
            ):
                continue

            seen_content.add(
                identity
            )

            document_counts[
                document_group
            ] += 1

            citation_id = (
                f"KB{len(search_results) + 1}"
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
                    citation_id=(
                        citation_id
                    ),
                    knowledge_document_id=(
                        chunk
                        .knowledge_document_id
                    ),
                    chunk_index=(
                        chunk.chunk_index
                    ),
                    page_number=(
                        chunk.page_number
                    ),
                )
            )

            if (
                len(search_results)
                >= limit
            ):
                break

        logger.info(
            (
                "Knowledge search query=%r "
                "candidates=%s returned=%s "
                "threshold=%s category=%s "
                "document_id=%s"
            ),
            query,
            candidate_limit,
            len(search_results),
            threshold,
            category,
            document_id,
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