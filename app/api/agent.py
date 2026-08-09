from fastapi import APIRouter, HTTPException

from app.schemas.agent import AgentRequest, AgentResponse
from app.services.agent_service import AgentServiceError, run_agent

router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)


@router.post(
    "/run",
    response_model=AgentResponse,
)
async def agent_run(
    request: AgentRequest,
) -> AgentResponse:
    try:
        answer, used_tools = await run_agent(
            message=request.message,
            station_id=request.station_id,
            latitude=request.latitude,
            longitude=request.longitude,
        )

        return AgentResponse(
            station_id=request.station_id,
            answer=answer,
            used_tools=used_tools,
        )

    except AgentServiceError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error