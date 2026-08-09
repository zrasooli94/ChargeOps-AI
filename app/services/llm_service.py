from openai import OpenAI, OpenAIError

from app.core.config import settings

client = OpenAI(api_key=settings.openai_api_key)


class LLMServiceError(Exception):
    """Raised when the LLM service fails."""


def generate_response(message: str) -> str:
    try:
        response = client.responses.create(
            model="gpt-5-mini",
            input=message,
        )

        return response.output_text

    except OpenAIError as error:
        raise LLMServiceError("Failed to generate an AI response.") from error