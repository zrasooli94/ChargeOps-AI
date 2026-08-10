from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.database import get_db
from app.schemas.observability import (
    AgentRunRead,
)
from app.services.observability_service import (
    list_agent_runs,
)

router = APIRouter(
    prefix="/observability",
    tags=["Observability"],
)


@router.get(
    "/runs",
    response_model=list[
        AgentRunRead
    ],
)
async def get_agent_runs(
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
    station_id: str | None = None,
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
) -> list[AgentRunRead]:
    runs = await list_agent_runs(
        session=session,
        station_id=station_id,
        limit=limit,
    )

    return [
        AgentRunRead.model_validate(
            run
        )
        for run in runs
    ]