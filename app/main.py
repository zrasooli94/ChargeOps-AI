from fastapi import FastAPI, HTTPException

from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMServiceError, generate_response

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
    try:
        answer = generate_response(request.message)
        return ChatResponse(answer=answer)

    except LLMServiceError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error