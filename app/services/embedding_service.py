import logging

from openai import OpenAIError

from app.core.config import settings
from app.core.openai_client import client

logger = logging.getLogger(__name__)


class EmbeddingServiceError(Exception):
    """Raised when embeddings cannot be generated."""


async def create_embeddings(
    texts: list[str],
) -> list[list[float]]:
    cleaned_texts = [
        text.strip()
        for text in texts
        if text.strip()
    ]

    if not cleaned_texts:
        raise EmbeddingServiceError(
            "Cannot create embeddings for empty text."
        )

    try:
        logger.info(
            "Creating %s embeddings with model=%s",
            len(cleaned_texts),
            settings.embedding_model,
        )

        response = await client.embeddings.create(
            model=settings.embedding_model,
            input=cleaned_texts,
            dimensions=(
                settings.embedding_dimensions
            ),
            encoding_format="float",
        )

        ordered_data = sorted(
            response.data,
            key=lambda item: item.index,
        )

        return [
            item.embedding
            for item in ordered_data
        ]

    except OpenAIError as error:
        logger.exception(
            "Embedding generation failed"
        )

        raise EmbeddingServiceError(
            "Failed to generate embeddings."
        ) from error


async def create_embedding(
    text: str,
) -> list[float]:
    embeddings = await create_embeddings(
        [text]
    )

    return embeddings[0]