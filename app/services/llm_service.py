from openai import OpenAI

from app.core.config import settings

client = OpenAI(api_key=settings.openai_api_key)


def generate_response(message: str) -> str:
    response = client.responses.create(
        model="gpt-5-mini",
        input=message,
    )

    return response.output_text