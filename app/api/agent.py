from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.agent import (
    AgentRequest,
    AgentResponse,
)
from app.services.agent_service import (
    AgentServiceError,
    run_agent,
)

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
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> AgentResponse:
    try:
        answer, used_tools, trace = await run_agent(
            message=request.message,
            station_id=request.station_id,
            session=session,
        )

        return AgentResponse(
            station_id=request.station_id,
            answer=answer,
            used_tools=used_tools,
            trace=trace,
        )

    except AgentServiceError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error