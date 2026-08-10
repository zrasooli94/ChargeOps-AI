from dotenv import load_dotenv
from langsmith.wrappers import (
    wrap_openai,
)
from openai import AsyncOpenAI

from app.core.config import settings

load_dotenv()


_base_client = AsyncOpenAI(
    api_key=settings.openai_api_key,
)


client = wrap_openai(
    _base_client
)