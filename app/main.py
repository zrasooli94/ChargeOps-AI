import logging

from fastapi import FastAPI

from app.api.analysis import router as analysis_router
from app.api.chat import router as chat_router
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

app.include_router(analysis_router)
app.include_router(chat_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
    }
