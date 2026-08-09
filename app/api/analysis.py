from fastapi import APIRouter, HTTPException

from app.schemas.analysis import ChargingIssueAnalysis, ChargingIssueRequest
from app.services.llm_service import LLMServiceError, analyze_charging_issue

router = APIRouter()


@router.post("/analyze", response_model=ChargingIssueAnalysis)
async def analyze(request: ChargingIssueRequest) -> ChargingIssueAnalysis:
    try:
        context = (
            f"Station ID: {request.station_id}\n"
            f"Charger model: {request.charger_model or 'Unknown'}\n"
            f"Issue: {request.issue}"
        )

        return await analyze_charging_issue(context)

    except LLMServiceError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error