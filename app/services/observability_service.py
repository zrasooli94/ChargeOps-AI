from datetime import (
    datetime,
    timezone,
)
from uuid import UUID

from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.config import settings
from app.models.agent_run import AgentRun
from app.schemas.agent import ToolTrace


async def record_agent_run(
    session: AsyncSession,
    *,
    run_id: UUID,
    thread_id: str,
    station_id: str,
    user_message: str,
    answer: str,
    used_tools: list[str],
    trace: list[ToolTrace],
    approval_required: bool,
    latency_ms: int,
) -> AgentRun:
    status = (
        "awaiting_approval"
        if approval_required
        else "completed"
    )

    completed_at = (
        None
        if approval_required
        else datetime.now(
            timezone.utc
        )
    )

    agent_run = AgentRun(
        id=run_id,
        thread_id=thread_id,
        station_id=station_id,
        user_message=user_message,
        status=status,
        answer=(
            answer
            or None
        ),
        used_tools=used_tools,
        trace=[
            item.model_dump()
            for item in trace
        ],
        approval_required=(
            approval_required
        ),
        model=settings.openai_model,
        latency_ms=latency_ms,
        completed_at=completed_at,
    )

    session.add(
        agent_run
    )

    await session.commit()

    await session.refresh(
        agent_run
    )

    return agent_run


async def complete_pending_agent_run(
    session: AsyncSession,
    *,
    thread_id: str,
    approved: bool,
    answer: str,
    used_tools: list[str],
    trace: list[ToolTrace],
) -> AgentRun | None:
    result = await session.execute(
        select(
            AgentRun
        )
        .where(
            AgentRun.thread_id
            == thread_id,
            AgentRun.status
            == "awaiting_approval",
        )
        .order_by(
            AgentRun.started_at.desc()
        )
        .limit(1)
    )

    agent_run = (
        result.scalar_one_or_none()
    )

    if agent_run is None:
        return None

    agent_run.status = (
        "completed"
    )

    agent_run.approval_decision = (
        approved
    )

    agent_run.answer = (
        answer
        or None
    )

    agent_run.used_tools = (
        used_tools
    )

    agent_run.trace = [
        item.model_dump()
        for item in trace
    ]

    agent_run.completed_at = (
        datetime.now(
            timezone.utc
        )
    )

    await session.commit()

    await session.refresh(
        agent_run
    )

    return agent_run


async def list_agent_runs(
    session: AsyncSession,
    *,
    station_id: str | None = None,
    limit: int = 100,
) -> list[AgentRun]:
    statement = (
        select(
            AgentRun
        )
        .order_by(
            AgentRun.started_at.desc()
        )
        .limit(limit)
    )

    if station_id:
        statement = statement.where(
            AgentRun.station_id
            == station_id
        )

    result = await session.execute(
        statement
    )

    return list(
        result.scalars().all()
    )