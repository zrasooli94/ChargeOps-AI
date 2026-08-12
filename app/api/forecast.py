from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)

from app.ml.forecasting.runtime import (
    ForecastRuntimeError,
    ForecastStationNotFoundError,
    forecast_station_demand,
)
from app.schemas.forecast import (
    StationDemandForecast,
)

router = APIRouter(
    prefix="/forecast",
    tags=[
        "forecasting",
    ],
)


@router.get(
    "/stations/{station_id}",
    response_model=(
        StationDemandForecast
    ),
)
async def get_station_forecast(
    station_id: str,
    hours: int = Query(
        default=24,
        ge=1,
        le=48,
    ),
) -> StationDemandForecast:
    try:
        result = (
            await forecast_station_demand(
                station_id,
                hours,
            )
        )

        return (
            StationDemandForecast
            .model_validate(
                result
            )
        )

    except (
        ForecastStationNotFoundError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(
                error
            ),
        ) from error

    except ForecastRuntimeError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "EV demand forecasting "
                "is temporarily unavailable."
            ),
        ) from error