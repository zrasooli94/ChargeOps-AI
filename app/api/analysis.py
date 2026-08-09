from fastapi import APIRouter, HTTPException

from app.schemas.analysis import ChargingIssueAnalysis
from app.schemas.chat import ChatRequest
from app.services.llm_service import LLMServiceError, analyze_charging_issue

router = APIRouter()


@router.post("/analyze", response_model=ChargingIssueAnalysis)
async def analyze(request: ChatRequest) -> ChargingIssueAnalysis:
    try:
        return await analyze_charging_issue(request.message)

    except LLMServiceError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error