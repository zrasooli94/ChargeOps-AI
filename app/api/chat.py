from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMServiceError, generate_response

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        answer = generate_response(request.message)
        return ChatResponse(answer=answer)

    except LLMServiceError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error