import logging

from openai import OpenAIError

from app.core.config import settings
from app.core.openai_client import client

logger = logging.getLogger(__name__)


class EmbeddingServiceError(Exception):
    """Raised when text embeddings cannot be generated."""


async def create_embedding(
    text: str,
) -> list[float]:
    clean_text = text.strip()

    if not clean_text:
        raise EmbeddingServiceError(
            "Cannot create an embedding for empty text."
        )

    try:
        logger.info(
            "Creating embedding with model=%s",
            settings.embedding_model,
        )

        response = await client.embeddings.create(
            model=settings.embedding_model,
            input=clean_text,
            dimensions=settings.embedding_dimensions,
            encoding_format="float",
        )

        return response.data[0].embedding

    except OpenAIError as error:
        logger.exception(
            "Embedding generation failed"
        )

        raise EmbeddingServiceError(
            "Failed to generate text embedding."
        ) from error