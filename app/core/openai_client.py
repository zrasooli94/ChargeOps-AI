import httpx
from dotenv import load_dotenv
from langsmith.wrappers import (
    wrap_openai,
)
from openai import AsyncOpenAI

from app.core.config import settings

load_dotenv()


_openai_timeout = httpx.Timeout(
    timeout=(
        settings.openai_timeout_seconds
    ),
    connect=(
        settings
        .openai_connect_timeout_seconds
    ),
)


_base_client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    timeout=_openai_timeout,
    max_retries=(
        settings.openai_max_retries
    ),
)


client = wrap_openai(
    _base_client
)


async def close_openai_client(
) -> None:
    """
    Close the underlying OpenAI HTTP client during
    application shutdown.
    """

    await _base_client.close()