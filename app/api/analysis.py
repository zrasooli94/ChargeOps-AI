from fastapi import APIRouter, HTTPException

from app.schemas.analysis import (
    ChargingIssueRequest,
    ChargingIssueResponse,
)
from app.services.llm_service import LLMServiceError, analyze_charging_issue

router = APIRouter()


@router.post("/analyze", response_model=ChargingIssueResponse)
async def analyze(request: ChargingIssueRequest) -> ChargingIssueResponse:
    try:
        context = (
            f"Station ID: {request.station_id}\n"
            f"Charger model: {request.charger_model or 'Unknown'}\n"
            f"Issue: {request.issue}"
        )

        analysis = await analyze_charging_issue(context)

        return ChargingIssueResponse(
            station_id=request.station_id,
            charger_model=request.charger_model,
            analysis=analysis,
        )

    except LLMServiceError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error