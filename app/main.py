from fastapi import FastAPI

from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import generate_response

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    answer = generate_response(request.message)

    return ChatResponse(answer=answer)