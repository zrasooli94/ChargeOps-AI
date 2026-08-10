from typing import Annotated
from uuid import uuid4

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
async def run_chargeops_agent(
    request: AgentRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> AgentResponse:
    """
    Run the ChargeOps LangGraph agent.

    If the client supplies a thread_id,
    the existing conversation is continued.

    If no thread_id is supplied,
    a new conversation thread is created.
    """

    thread_id = (
        request.thread_id
        or uuid4()
    )

    try:
        (
            answer,
            used_tools,
            trace,
        ) = await run_agent(
            message=request.message,
            station_id=request.station_id,
            session=session,
            thread_id=str(
                thread_id
            ),
        )

        return AgentResponse(
            thread_id=thread_id,
            answer=answer,
            used_tools=used_tools,
            trace=trace,
        )

    except AgentServiceError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error