import asyncio
import logging
from uuid import UUID

from sqlalchemy.exc import (
    SQLAlchemyError,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.config import settings
from app.core.database import (
    AsyncSessionLocal,
)
from app.models.agent_run import AgentRun
from app.schemas.agent import ToolTrace
from app.services.observability_service import (
    complete_pending_agent_run,
    record_agent_run,
)

logger = logging.getLogger(
    __name__
)


async def _safe_rollback(
    session: AsyncSession,
) -> None:
    try:
        await session.rollback()

    except SQLAlchemyError:
        logger.exception(
            "Observability session rollback failed."
        )


async def safe_record_agent_run(
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
) -> bool:
    """
    Persist agent telemetry without allowing an
    observability outage to destroy a successful
    user-facing agent response.

    Observability intentionally uses its own
    database session so telemetry failures cannot
    poison the main request transaction.
    """

    try:
        async with (
            AsyncSessionLocal()
            as session
        ):
            try:
                async with asyncio.timeout(
                    settings
                    .observability_write_timeout_seconds
                ):
                    await record_agent_run(
                        session=session,
                        run_id=run_id,
                        thread_id=thread_id,
                        station_id=station_id,
                        user_message=(
                            user_message
                        ),
                        answer=answer,
                        used_tools=used_tools,
                        trace=trace,
                        approval_required=(
                            approval_required
                        ),
                        latency_ms=(
                            latency_ms
                        ),
                    )

                return True

            except TimeoutError:
                await _safe_rollback(
                    session
                )

                logger.warning(
                    "Agent observability write "
                    "timed out; agent response "
                    "will continue."
                )

                return False

            except SQLAlchemyError:
                await _safe_rollback(
                    session
                )

                logger.exception(
                    "Agent observability write "
                    "failed; agent response "
                    "will continue."
                )

                return False

    except SQLAlchemyError:
        logger.exception(
            "Could not create or close "
            "observability database session; "
            "agent response will continue."
        )

        return False


async def safe_complete_pending_agent_run(
    *,
    thread_id: str,
    approved: bool,
    answer: str,
    used_tools: list[str],
    trace: list[ToolTrace],
) -> AgentRun | None:
    """
    Best-effort completion of persisted HITL
    observability information.
    """

    try:
        async with (
            AsyncSessionLocal()
            as session
        ):
            try:
                async with asyncio.timeout(
                    settings
                    .observability_write_timeout_seconds
                ):
                    return (
                        await complete_pending_agent_run(
                            session=session,
                            thread_id=thread_id,
                            approved=approved,
                            answer=answer,
                            used_tools=used_tools,
                            trace=trace,
                        )
                    )

            except TimeoutError:
                await _safe_rollback(
                    session
                )

                logger.warning(
                    "Agent observability completion "
                    "timed out; response will continue."
                )

                return None

            except SQLAlchemyError:
                await _safe_rollback(
                    session
                )

                logger.exception(
                    "Agent observability completion "
                    "failed; response will continue."
                )

                return None

    except SQLAlchemyError:
        logger.exception(
            "Could not create or close "
            "observability database session; "
            "response will continue."
        )

        return None