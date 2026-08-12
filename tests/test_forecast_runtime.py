import asyncio
from pathlib import Path
from unittest.mock import (
    AsyncMock,
    patch,
)

import pandas as pd
import pytest

from app.ml.forecasting.demo_data import (
    generate_demo_demand_data,
)
from app.ml.forecasting.modeling import (
    train_demand_forecast_model,
)
from app.ml.forecasting.runtime import (
    ForecastStationNotFoundError,
    ForecastWeatherError,
    forecast_station_demand,
)


def _make_weather(
    start: pd.Timestamp,
    hours: int,
) -> pd.DataFrame:
    timestamps = (
        pd.date_range(
            start=start,
            periods=hours,
            freq="h",
        )
    )

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "temperature_c": [
                30.0
            ]
            * hours,
            "precipitation_mm": [
                0.0
            ]
            * hours,
            "wind_speed_kmh": [
                8.0
            ]
            * hours,
        }
    )


def test_runtime_produces_recursive_forecast(
    tmp_path: Path,
) -> None:
    async def run_test() -> None:
        raw = (
            generate_demo_demand_data(
                days=60
            )
        )

        history_path = (
            tmp_path
            / "history.csv"
        )

        artifact_path = (
            tmp_path
            / "forecast.joblib"
        )

        raw.to_csv(
            history_path,
            index=False,
        )

        train_demand_forecast_model(
            raw,
            artifact_path=(
                artifact_path
            ),
            holdout_days=7,
        )

        latest = pd.to_datetime(
            raw[
                "timestamp"
            ],
            utc=True,
        ).max()

        weather = _make_weather(
            latest
            + pd.Timedelta(
                hours=1
            ),
            24,
        )

        with patch(
            "app.ml.forecasting."
            "runtime."
            "get_hourly_weather_forecast",
            new=AsyncMock(
                return_value=(
                    weather
                )
            ),
        ):
            result = (
                await forecast_station_demand(
                    "KL-205",
                    24,
                    artifact_path=(
                        artifact_path
                    ),
                    history_path=(
                        history_path
                    ),
                )
            )

        assert (
            result[
                "available"
            ]
            is True
        )

        assert (
            result[
                "station_id"
            ]
            == "KL-205"
        )

        assert len(
            result[
                "points"
            ]
        ) == 24

        assert (
            result[
                "weather_source"
            ]
            == (
                "open_meteo_hourly_forecast"
            )
        )

        assert all(
            point[
                "predicted_energy_kwh"
            ]
            >= 0
            for point
            in result[
                "points"
            ]
        )

    asyncio.run(
        run_test()
    )


def test_weather_failure_uses_historical_fallback(
    tmp_path: Path,
) -> None:
    async def run_test() -> None:
        raw = (
            generate_demo_demand_data(
                days=60
            )
        )

        history_path = (
            tmp_path
            / "history.csv"
        )

        artifact_path = (
            tmp_path
            / "forecast.joblib"
        )

        raw.to_csv(
            history_path,
            index=False,
        )

        train_demand_forecast_model(
            raw,
            artifact_path=(
                artifact_path
            ),
            holdout_days=7,
        )

        with patch(
            "app.ml.forecasting."
            "runtime."
            "get_hourly_weather_forecast",
            new=AsyncMock(
                side_effect=(
                    ForecastWeatherError(
                        "provider unavailable"
                    )
                )
            ),
        ):
            result = (
                await forecast_station_demand(
                    "KL-101",
                    12,
                    artifact_path=(
                        artifact_path
                    ),
                    history_path=(
                        history_path
                    ),
                )
            )

        assert (
            result[
                "available"
            ]
            is True
        )

        assert (
            result[
                "weather_source"
            ]
            == (
                "historical_weather_profile_fallback"
            )
        )

    asyncio.run(
        run_test()
    )


def test_unknown_forecast_station_is_rejected(
    tmp_path: Path,
) -> None:
    async def run_test() -> None:
        raw = (
            generate_demo_demand_data(
                days=30
            )
        )

        history_path = (
            tmp_path
            / "history.csv"
        )

        raw.to_csv(
            history_path,
            index=False,
        )

        with pytest.raises(
            ForecastStationNotFoundError
        ):
            await forecast_station_demand(
                "KL-999",
                24,
                artifact_path=(
                    tmp_path
                    / "missing.joblib"
                ),
                history_path=(
                    history_path
                ),
            )

    asyncio.run(
        run_test()
    )