import logging

from openai import AsyncOpenAI, OpenAIError

from app.core.config import settings
from app.schemas.analysis import ChargingIssueAnalysis

logger = logging.getLogger(__name__)



client = AsyncOpenAI(api_key=settings.openai_api_key)


class LLMServiceError(Exception):
    """Raised when the LLM service fails."""


async def generate_response(message: str) -> str:
    try:
        logger.info("Sending request to OpenAI")

        response = await client.responses.create(
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


async def analyze_charging_issue(
    message: str,
) -> ChargingIssueAnalysis:
    try:
        logger.info("Analyzing EV charging issue")

        response = await client.responses.parse(
            model=settings.openai_model,
            instructions=(
                "You analyze EV charging station problems. "
                "Classify the issue accurately based only on the information provided. "
                "If the category cannot be determined, use 'unknown'."
            ),
            input=message,
            text_format=ChargingIssueAnalysis,
        )

        result = response.output_parsed

        if result is None:
            raise LLMServiceError(
                "The AI did not return a valid structured analysis."
            )

        return result

    except OpenAIError as error:
        logger.exception("OpenAI structured analysis failed")
        raise LLMServiceError(
            "Failed to analyze the charging issue."
        ) from error