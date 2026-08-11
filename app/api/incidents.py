from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_dependencies import (
    OperatorUser,
    ViewerUser,
)
from app.core.database import get_db
from app.schemas.incident import (
    IncidentResponse,
    IncidentStatusUpdate,
)
from app.services.incident_service import (
    get_incident,
    get_recent_incidents,
    update_incident_status,
)

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)


# =================================================
# List incidents
#
# Permission:
# viewer+
#
# Incident history is read-only information.
# =================================================


@router.get(
    "",
    response_model=list[
        IncidentResponse
    ],
)
async def list_incidents(
    _current_user: ViewerUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
    station_id: str,
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
) -> list[IncidentResponse]:
    incidents = await get_recent_incidents(
        session=session,
        station_id=station_id,
        limit=limit,
    )

    return [
        IncidentResponse.model_validate(
            incident
        )
        for incident in incidents
    ]


# =================================================
# Get incident details
#
# Permission:
# viewer+
# =================================================


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
)
async def incident_details(
    incident_id: int,
    _current_user: ViewerUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> IncidentResponse:
    incident = await get_incident(
        session,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    return IncidentResponse.model_validate(
        incident
    )


# =================================================
# Change incident status
#
# Permission:
# operator+
#
# This performs an operational database write,
# so viewers are not permitted.
# =================================================


@router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
)
async def change_incident_status(
    incident_id: int,
    request: IncidentStatusUpdate,
    _current_user: OperatorUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> IncidentResponse:
    incident = await update_incident_status(
        session=session,
        incident_id=incident_id,
        status=request.status,
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    return IncidentResponse.model_validate(
        incident
    )