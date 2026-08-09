import logging

from openai import OpenAI, OpenAIError

from app.core.config import settings

logger = logging.getLogger(__name__)



client = OpenAI(api_key=settings.openai_api_key)


class LLMServiceError(Exception):
    """Raised when the LLM service fails."""


def generate_response(message: str) -> str:
    try:
        logger.info("Sending request to OpenAI")

        response = client.responses.create(
            model=settings.openai_model,
            instructions=(
                "You are ChargeOps AI, an assistant for EV charging operations. "
                "Give clear, concise, technically accurate answers. "
                "If information is uncertain, say so rather than inventing details."
            ),
            input=message,
        )

        logger.info("OpenAI response received successfully")

        return response.output_text

    except OpenAIError as error:
        logger.exception("OpenAI request failed")
        raise LLMServiceError("Failed to generate an AI response.") from error