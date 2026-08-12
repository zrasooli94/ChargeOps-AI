from fastapi import (
    APIRouter,
    status,
)
from fastapi.responses import (
    JSONResponse,
)

from app.core.config import settings
from app.core.database import (
    check_database_ready,
)

router = APIRouter(
    prefix="/health",
    tags=[
        "Health",
    ],
)


@router.get(
    "/live"
)
async def liveness_check(
) -> dict[str, str]:
    """
    Liveness answers one question:

    Is the ChargeOps process alive?
    """

    return {
        "status": "alive",
        "app": settings.app_name,
    }


@router.get(
    "/ready"
)
async def readiness_check(
) -> JSONResponse:
    """
    Readiness answers:

    Can this ChargeOps instance currently serve
    normal application traffic?
    """

    database_ready, reason = (
        await check_database_ready()
    )

    if database_ready:
        return JSONResponse(
            status_code=(
                status.HTTP_200_OK
            ),
            content={
                "status": "ready",
                "database": "ok",
            },
        )

    return JSONResponse(
        status_code=(
            status
            .HTTP_503_SERVICE_UNAVAILABLE
        ),
        content={
            "status": "not_ready",
            "database": "unavailable",
            "reason": reason,
        },
    )