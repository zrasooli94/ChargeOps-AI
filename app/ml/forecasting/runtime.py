import asyncio
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import pandas as pd

from app.core.config import settings
from app.ml.forecasting.service import (
    load_forecast_artifact,
    predict_demand,
)


class ForecastRuntimeError(
    RuntimeError
):
    """Raised when a demand forecast cannot be produced."""


class ForecastStationNotFoundError(
    ForecastRuntimeError
):
    """Raised when forecast history has no requested station."""


class ForecastWeatherError(
    ForecastRuntimeError
):
    """Raised when future weather cannot be retrieved."""


# =================================================
# Scalar helpers
# =================================================


def _as_float(
    value: Any,
) -> float:
    """
    Convert a known numeric runtime value to float.

    This helper also keeps strict static type checkers
    from inheriting Pandas' broad Scalar union.
    """

    return float(
        value
    )


def _as_timestamp(
    value: Any,
) -> pd.Timestamp:
    """
    Normalize a runtime datetime-like value to
    a Pandas Timestamp.
    """

    return pd.Timestamp(
        value
    )


# =================================================
# Historical demand loading
# =================================================


def _load_history(
    history_path: str | Path,
) -> pd.DataFrame:
    path = Path(
        history_path
    )

    if not path.exists():
        raise ForecastRuntimeError(
            "Forecast history dataset does not exist."
        )

    frame = pd.read_csv(
        path
    )

    if frame.empty:
        raise ForecastRuntimeError(
            "Forecast history dataset is empty."
        )

    required_columns = {
        "timestamp",
        "station_id",
        "latitude",
        "longitude",
        "charger_count",
        "max_power_kw",
        "temperature_c",
        "precipitation_mm",
        "wind_speed_kmh",
        "mobility_index",
        "energy_kwh",
    }

    missing_columns = (
        required_columns
        - set(
            frame.columns
        )
    )

    if missing_columns:
        raise ForecastRuntimeError(
            "Forecast history is missing "
            "required columns: "
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )

    frame[
        "timestamp"
    ] = pd.to_datetime(
        frame[
            "timestamp"
        ],
        utc=True,
        errors="raise",
    )

    return (
        frame
        .sort_values(
            [
                "station_id",
                "timestamp",
            ]
        )
        .reset_index(
            drop=True
        )
    )


# =================================================
# External hourly weather forecast
# =================================================


async def get_hourly_weather_forecast(
    *,
    latitude: float,
    longitude: float,
    hours: int,
) -> pd.DataFrame:
    """
    Retrieve hourly weather forecast data from
    Open-Meteo.

    This is a read-only external dependency.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": (
            "temperature_2m,"
            "precipitation,"
            "wind_speed_10m"
        ),
        "timezone": "UTC",
        "forecast_days": 3,
    }

    timeout = httpx.Timeout(
        timeout=(
            settings
            .forecast_weather_timeout_seconds
        ),
        connect=5.0,
    )

    last_error: Exception | None = None

    for attempt in range(
        3
    ):
        try:
            async with httpx.AsyncClient(
                timeout=timeout
            ) as client:
                response = await client.get(
                    settings.weather_base_url,
                    params=params,
                )

                response.raise_for_status()

            payload = response.json()

            hourly = payload[
                "hourly"
            ]

            frame = pd.DataFrame(
                {
                    "timestamp": (
                        pd.to_datetime(
                            hourly[
                                "time"
                            ],
                            utc=True,
                        )
                    ),
                    "temperature_c": (
                        hourly[
                            "temperature_2m"
                        ]
                    ),
                    "precipitation_mm": (
                        hourly[
                            "precipitation"
                        ]
                    ),
                    "wind_speed_kmh": (
                        hourly[
                            "wind_speed_10m"
                        ]
                    ),
                }
            )

            return frame.head(
                max(
                    hours + 24,
                    48,
                )
            )

        except (
            httpx.HTTPError,
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            last_error = error

            if attempt < 2:
                await asyncio.sleep(
                    0.25
                    * (
                        2**attempt
                    )
                )

    raise ForecastWeatherError(
        "Hourly forecast weather is unavailable."
    ) from last_error


# =================================================
# Historical temporal profile helpers
# =================================================


def _profile_value(
    frame: pd.DataFrame,
    column: str,
    timestamp: pd.Timestamp,
) -> float:
    weekday = (
        timestamp.dayofweek
    )

    hour = (
        timestamp.hour
    )

    timestamps = pd.to_datetime(
        frame[
            "timestamp"
        ],
        utc=True,
    )

    exact = frame[
        (
            timestamps.dt.dayofweek
            == weekday
        )
        & (
            timestamps.dt.hour
            == hour
        )
    ]

    if not exact.empty:
        return _as_float(
            exact[
                column
            ].mean()
        )

    hourly = frame[
        timestamps.dt.hour
        == hour
    ]

    if not hourly.empty:
        return _as_float(
            hourly[
                column
            ].mean()
        )

    return _as_float(
        frame[
            column
        ].mean()
    )


def _build_weather_fallback(
    station_history: pd.DataFrame,
    timestamps: pd.DatetimeIndex,
) -> pd.DataFrame:
    rows: list[
        dict[str, Any]
    ] = []

    for timestamp in timestamps:
        rows.append(
            {
                "timestamp": timestamp,
                "temperature_c": (
                    _profile_value(
                        station_history,
                        "temperature_c",
                        timestamp,
                    )
                ),
                "precipitation_mm": (
                    _profile_value(
                        station_history,
                        "precipitation_mm",
                        timestamp,
                    )
                ),
                "wind_speed_kmh": (
                    _profile_value(
                        station_history,
                        "wind_speed_kmh",
                        timestamp,
                    )
                ),
            }
        )

    return pd.DataFrame(
        rows
    )


# =================================================
# Feature helpers
# =================================================


def _temporal_features(
    timestamp: pd.Timestamp,
) -> dict[
    str,
    float | int,
]:
    hour = float(
        timestamp.hour
    )

    weekday = float(
        timestamp.dayofweek
    )

    month = float(
        timestamp.month
    )

    return {
        "hour_sin": float(
            np.sin(
                2
                * np.pi
                * hour
                / 24
            )
        ),
        "hour_cos": float(
            np.cos(
                2
                * np.pi
                * hour
                / 24
            )
        ),
        "weekday_sin": float(
            np.sin(
                2
                * np.pi
                * weekday
                / 7
            )
        ),
        "weekday_cos": float(
            np.cos(
                2
                * np.pi
                * weekday
                / 7
            )
        ),
        "month_sin": float(
            np.sin(
                2
                * np.pi
                * (
                    month
                    - 1
                )
                / 12
            )
        ),
        "month_cos": float(
            np.cos(
                2
                * np.pi
                * (
                    month
                    - 1
                )
                / 12
            )
        ),
        "is_weekend": int(
            timestamp.dayofweek
            >= 5
        ),
    }


def _risk_level(
    predicted_energy_kwh: float,
    *,
    medium_threshold: float,
    high_threshold: float,
) -> str:
    if (
        predicted_energy_kwh
        >= high_threshold
    ):
        return "high"

    if (
        predicted_energy_kwh
        >= medium_threshold
    ):
        return "medium"

    return "low"


# =================================================
# Weather lookup
# =================================================


def _build_weather_lookup(
    weather: pd.DataFrame,
) -> dict[
    pd.Timestamp,
    tuple[
        float,
        float,
        float,
    ],
]:
    """
    Convert the Pandas weather frame into a typed
    Python dictionary.

    This avoids ambiguous Pandas .loc return types.
    """

    lookup: dict[
        pd.Timestamp,
        tuple[
            float,
            float,
            float,
        ],
    ] = {}

    records = weather.to_dict(
        orient="records"
    )

    for record in records:
        timestamp = _as_timestamp(
            record[
                "timestamp"
            ]
        )

        lookup[
            timestamp
        ] = (
            _as_float(
                record[
                    "temperature_c"
                ]
            ),
            _as_float(
                record[
                    "precipitation_mm"
                ]
            ),
            _as_float(
                record[
                    "wind_speed_kmh"
                ]
            ),
        )

    return lookup


# =================================================
# Demand history lookup
# =================================================


def _build_demand_lookup(
    station_history: pd.DataFrame,
) -> dict[
    pd.Timestamp,
    float,
]:
    """
    Convert historical demand into a normal Python
    mapping so recursive predictions can be appended
    without Pandas Series assignment.
    """

    lookup: dict[
        pd.Timestamp,
        float,
    ] = {}

    records = (
        station_history[
            [
                "timestamp",
                "energy_kwh",
            ]
        ]
        .to_dict(
            orient="records"
        )
    )

    for record in records:
        timestamp = _as_timestamp(
            record[
                "timestamp"
            ]
        )

        lookup[
            timestamp
        ] = _as_float(
            record[
                "energy_kwh"
            ]
        )

    return lookup


def _rolling_demand_mean(
    demand_lookup: dict[
        pd.Timestamp,
        float,
    ],
    *,
    timestamp: pd.Timestamp,
    hours: int,
) -> float:
    cutoff = (
        timestamp
        - pd.Timedelta(
            hours=hours
        )
    )

    values = [
        value
        for demand_timestamp, value
        in demand_lookup.items()
        if (
            cutoff
            <= demand_timestamp
            < timestamp
        )
    ]

    if not values:
        return float(
            "nan"
        )

    return float(
        np.mean(
            np.asarray(
                values,
                dtype=float,
            )
        )
    )


# =================================================
# Forecast runtime
# =================================================


async def forecast_station_demand(
    station_id: str,
    hours: int | None = None,
    *,
    artifact_path: str | Path | None = None,
    history_path: str | Path | None = None,
) -> dict[
    str,
    Any,
]:
    normalized_station_id = (
        station_id
        .strip()
        .upper()
    )

    if not normalized_station_id:
        raise ForecastRuntimeError(
            "Station ID must not be empty."
        )

    horizon = (
        hours
        if hours is not None
        else (
            settings
            .forecast_default_horizon_hours
        )
    )

    if not (
        1
        <= horizon
        <= settings.forecast_max_horizon_hours
    ):
        raise ForecastRuntimeError(
            "Forecast horizon is outside "
            "the allowed range."
        )

    resolved_history_path = (
        history_path
        or settings.forecast_history_path
    )

    resolved_artifact_path = (
        artifact_path
        or settings.forecast_model_artifact_path
    )

    # =============================================
    # Load history
    # =============================================

    history = _load_history(
        resolved_history_path
    )

    station_ids = (
        history[
            "station_id"
        ]
        .astype(
            str
        )
        .str.upper()
    )

    station_history = history[
        station_ids
        == normalized_station_id
    ].copy()

    if station_history.empty:
        raise (
            ForecastStationNotFoundError(
                "No forecasting history exists "
                f"for station "
                f"{normalized_station_id}."
            )
        )

    station_history = (
        station_history
        .sort_values(
            "timestamp"
        )
        .reset_index(
            drop=True
        )
    )

    latest_timestamp = (
        _as_timestamp(
            station_history[
                "timestamp"
            ].max()
        )
    )

    now = pd.Timestamp.now(
        tz="UTC"
    )

    age_hours = (
        now
        - latest_timestamp
    ).total_seconds() / 3600

    if (
        age_hours
        > settings
        .forecast_max_history_age_hours
    ):
        raise ForecastRuntimeError(
            "Forecast history is stale. "
            "Refresh or retrain the "
            "forecasting dataset."
        )

    # =============================================
    # Load trusted model artifact
    # =============================================

    artifact = (
        load_forecast_artifact(
            resolved_artifact_path
        )
    )

    # =============================================
    # Build future forecast horizon
    # =============================================

    future_timestamps = (
        pd.date_range(
            start=(
                latest_timestamp
                + pd.Timedelta(
                    hours=1
                )
            ),
            periods=horizon,
            freq="h",
        )
    )

    metadata = (
        station_history.iloc[
            -1
        ]
    )

    latitude = _as_float(
        metadata[
            "latitude"
        ]
    )

    longitude = _as_float(
        metadata[
            "longitude"
        ]
    )

    charger_count = _as_float(
        metadata[
            "charger_count"
        ]
    )

    max_power_kw = _as_float(
        metadata[
            "max_power_kw"
        ]
    )

    # =============================================
    # Weather enrichment
    # =============================================

    weather_source = (
        "open_meteo_hourly_forecast"
    )

    try:
        weather = (
            await get_hourly_weather_forecast(
                latitude=latitude,
                longitude=longitude,
                hours=horizon,
            )
        )

        weather[
            "timestamp"
        ] = pd.to_datetime(
            weather[
                "timestamp"
            ],
            utc=True,
        )

        weather = (
            weather
            .set_index(
                "timestamp"
            )
            .reindex(
                future_timestamps
            )
        )

        required_weather_columns = [
            "temperature_c",
            "precipitation_mm",
            "wind_speed_kmh",
        ]

        missing_weather = bool(
            weather[
                required_weather_columns
            ]
            .isna()
            .to_numpy()
            .any()
        )

        if missing_weather:
            raise ForecastWeatherError(
                "Hourly weather forecast "
                "contains missing values."
            )

        weather = (
            weather
            .reset_index()
        )

        if (
            "index"
            in weather.columns
            and "timestamp"
            not in weather.columns
        ):
            weather = (
                weather.rename(
                    columns={
                        "index": (
                            "timestamp"
                        )
                    }
                )
            )

    except ForecastWeatherError:
        weather_source = (
            "historical_weather_profile_fallback"
        )

        weather = (
            _build_weather_fallback(
                station_history,
                future_timestamps,
            )
        )

    weather_lookup = (
        _build_weather_lookup(
            weather
        )
    )

    # =============================================
    # Recursive demand state
    # =============================================

    demand_lookup = (
        _build_demand_lookup(
            station_history
        )
    )

    medium_threshold = (
        _as_float(
            station_history[
                "energy_kwh"
            ].quantile(
                0.75
            )
        )
    )

    high_threshold = (
        _as_float(
            station_history[
                "energy_kwh"
            ].quantile(
                0.90
            )
        )
    )

    points: list[
        dict[
            str,
            Any,
        ]
    ] = []

    # =============================================
    # Recursive hourly forecast
    # =============================================

    for timestamp in future_timestamps:
        weather_values = (
            weather_lookup.get(
                timestamp
            )
        )

        if weather_values is None:
            raise ForecastRuntimeError(
                "Required hourly weather "
                "features are unavailable."
            )

        (
            temperature_c,
            precipitation_mm,
            wind_speed_kmh,
        ) = weather_values

        mobility_index = (
            _profile_value(
                station_history,
                "mobility_index",
                timestamp,
            )
        )

        lag_1h = demand_lookup.get(
            (
                timestamp
                - pd.Timedelta(
                    hours=1
                )
            ),
            float(
                "nan"
            ),
        )

        lag_24h = demand_lookup.get(
            (
                timestamp
                - pd.Timedelta(
                    hours=24
                )
            ),
            float(
                "nan"
            ),
        )

        lag_168h = demand_lookup.get(
            (
                timestamp
                - pd.Timedelta(
                    hours=168
                )
            ),
            float(
                "nan"
            ),
        )

        rolling_24 = (
            _rolling_demand_mean(
                demand_lookup,
                timestamp=timestamp,
                hours=24,
            )
        )

        rolling_168 = (
            _rolling_demand_mean(
                demand_lookup,
                timestamp=timestamp,
                hours=168,
            )
        )

        row: dict[
            str,
            Any,
        ] = {
            "station_id": (
                normalized_station_id
            ),
            "latitude": latitude,
            "longitude": longitude,
            "charger_count": (
                charger_count
            ),
            "max_power_kw": (
                max_power_kw
            ),
            "temperature_c": (
                temperature_c
            ),
            "precipitation_mm": (
                precipitation_mm
            ),
            "wind_speed_kmh": (
                wind_speed_kmh
            ),
            "mobility_index": (
                mobility_index
            ),
            "lag_1h": (
                lag_1h
            ),
            "lag_24h": (
                lag_24h
            ),
            "lag_168h": (
                lag_168h
            ),
            "rolling_mean_24h": (
                rolling_24
            ),
            "rolling_mean_168h": (
                rolling_168
            ),
            **_temporal_features(
                timestamp
            ),
        }

        feature_frame = (
            pd.DataFrame(
                [
                    row
                ]
            )
        )

        prediction_array = (
            predict_demand(
                artifact,
                feature_frame,
            )
        )

        predicted = _as_float(
            prediction_array[
                0
            ]
        )

        # -----------------------------------------
        # Recursive update:
        # prediction for t becomes historical lag
        # input for t+1.
        # -----------------------------------------

        demand_lookup[
            timestamp
        ] = predicted

        risk = _risk_level(
            predicted,
            medium_threshold=(
                medium_threshold
            ),
            high_threshold=(
                high_threshold
            ),
        )

        points.append(
            {
                "timestamp": (
                    timestamp.isoformat()
                ),
                "predicted_energy_kwh": (
                    round(
                        predicted,
                        3,
                    )
                ),
                "temperature_c": (
                    round(
                        temperature_c,
                        2,
                    )
                ),
                "precipitation_mm": (
                    round(
                        precipitation_mm,
                        2,
                    )
                ),
                "wind_speed_kmh": (
                    round(
                        wind_speed_kmh,
                        2,
                    )
                ),
                "mobility_index": (
                    round(
                        mobility_index,
                        2,
                    )
                ),
                "risk_level": risk,
            }
        )

    if not points:
        raise ForecastRuntimeError(
            "Forecast returned no prediction points."
        )

    # =============================================
    # Forecast summary
    # =============================================

    predicted_values: list[
        float
    ] = [
        _as_float(
            point[
                "predicted_energy_kwh"
            ]
        )
        for point in points
    ]

    peak_index = int(
        np.argmax(
            np.asarray(
                predicted_values,
                dtype=float,
            )
        )
    )

    peak_point = (
        points[
            peak_index
        ]
    )

    risk_rank: dict[
        str,
        int,
    ] = {
        "low": 0,
        "medium": 1,
        "high": 2,
    }

    risk_levels: list[
        str
    ] = [
        str(
            point[
                "risk_level"
            ]
        )
        for point in points
    ]

    overall_risk = max(
        risk_levels,
        key=lambda value: (
            risk_rank[
                value
            ]
        ),
    )

    total_predicted_energy = float(
        np.sum(
            np.asarray(
                predicted_values,
                dtype=float,
            )
        )
    )

    average_hourly_energy = float(
        np.mean(
            np.asarray(
                predicted_values,
                dtype=float,
            )
        )
    )

    return {
        "available": True,
        "station_id": (
            normalized_station_id
        ),
        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "forecast_start": (
            future_timestamps[
                0
            ].isoformat()
        ),
        "horizon_hours": (
            horizon
        ),
        "model_version": (
            artifact.get(
                "model_version",
                "unknown",
            )
        ),
        "history_source": (
            settings
            .forecast_history_label
        ),
        "weather_source": (
            weather_source
        ),
        "peak_risk": (
            overall_risk
        ),
        "summary": {
            "total_predicted_energy_kwh": (
                round(
                    total_predicted_energy,
                    3,
                )
            ),
            "average_hourly_energy_kwh": (
                round(
                    average_hourly_energy,
                    3,
                )
            ),
            "peak_energy_kwh": (
                peak_point[
                    "predicted_energy_kwh"
                ]
            ),
            "peak_timestamp": (
                peak_point[
                    "timestamp"
                ]
            ),
            "historical_p75_kwh": (
                round(
                    medium_threshold,
                    3,
                )
            ),
            "historical_p90_kwh": (
                round(
                    high_threshold,
                    3,
                )
            ),
        },
        "training_metrics": (
            artifact.get(
                "metrics",
                {}
            )
        ),
        "points": points,
    }