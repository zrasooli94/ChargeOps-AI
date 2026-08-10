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
    AgentApprovalRequest,
    AgentRequest,
    AgentResponse,
    AgentResumeRequest,
)
from app.services.agent_service import (
    AgentServiceError,
    resume_agent,
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
    thread_id = (
        request.thread_id
        or uuid4()
    )

    try:
        (
            answer,
            used_tools,
            trace,
            approval_request,
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
            approval_required=(
                approval_request
                is not None
            ),
            approval_request=(
                AgentApprovalRequest
                .model_validate(
                    approval_request
                )
                if approval_request
                is not None
                else None
            ),
        )

    except AgentServiceError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error


@router.post(
    "/resume",
    response_model=AgentResponse,
)
async def resume_chargeops_agent(
    request: AgentResumeRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> AgentResponse:
    try:
        (
            answer,
            used_tools,
            trace,
            approval_request,
        ) = await resume_agent(
            thread_id=str(
                request.thread_id
            ),
            approved=(
                request.approved
            ),
            session=session,
        )

        return AgentResponse(
            thread_id=(
                request.thread_id
            ),
            answer=answer,
            used_tools=used_tools,
            trace=trace,
            approval_required=(
                approval_request
                is not None
            ),
            approval_request=(
                AgentApprovalRequest
                .model_validate(
                    approval_request
                )
                if approval_request
                is not None
                else None
            ),
        )

    except AgentServiceError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error