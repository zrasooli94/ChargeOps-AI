from time import perf_counter
from typing import (
    Annotated,
    cast,
)
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_dependencies import (
    OperatorUser,
    ViewerUser,
)
from app.core.database import get_db
from app.schemas.agent import (
    AgentApprovalRequest,
    AgentRequest,
    AgentResponse,
    AgentResumeRequest,
)
from app.schemas.auth import UserRole
from app.services.agent_service import (
    AgentServiceError,
    resume_agent,
    run_agent,
)
from app.services.observability_service import (
    complete_pending_agent_run,
    record_agent_run,
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
    current_user: ViewerUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> AgentResponse:
    run_id = uuid4()

    thread_id = (
        request.thread_id
        or uuid4()
    )

    started = perf_counter()

    try:
        (
            answer,
            used_tools,
            trace,
            approval_request,
            retrieved_evidence,
        ) = await run_agent(
            message=request.message,
            station_id=request.station_id,
            session=session,
            thread_id=str(
                thread_id
            ),
            user_id=str(
                current_user.id
            ),
            user_role=cast(
                UserRole,
                current_user.role,
            ),
        )

        latency_ms = int(
            (
                perf_counter()
                - started
            )
            * 1000
        )

        approval_required = (
            approval_request
            is not None
        )

        await record_agent_run(
            session=session,
            run_id=run_id,
            thread_id=str(
                thread_id
            ),
            station_id=(
                request.station_id
            ),
            user_message=(
                request.message
            ),
            answer=answer,
            used_tools=used_tools,
            trace=trace,
            approval_required=(
                approval_required
            ),
            latency_ms=latency_ms,
        )

        return AgentResponse(
            run_id=run_id,
            thread_id=thread_id,
            answer=answer,
            used_tools=used_tools,
            trace=trace,
            approval_required=(
                approval_required
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
            retrieved_evidence=(
                retrieved_evidence
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
    current_user: OperatorUser,
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
            retrieved_evidence,
        ) = await resume_agent(
            thread_id=str(
                request.thread_id
            ),
            approved=(
                request.approved
            ),
            session=session,
            user_id=str(
                current_user.id
            ),
            user_role=cast(
                UserRole,
                current_user.role,
            ),
        )

        completed_run = (
            await complete_pending_agent_run(
                session=session,
                thread_id=str(
                    request.thread_id
                ),
                approved=(
                    request.approved
                ),
                answer=answer,
                used_tools=used_tools,
                trace=trace,
            )
        )

        run_id = (
            completed_run.id
            if completed_run
            is not None
            else uuid4()
        )

        return AgentResponse(
            run_id=run_id,
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
            retrieved_evidence=(
                retrieved_evidence
            ),
        )

    except AgentServiceError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error