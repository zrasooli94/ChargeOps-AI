from typing import Any, Literal

from pydantic import (
    BaseModel,
    Field,
)


class ForecastPoint(
    BaseModel
):
    timestamp: str

    predicted_energy_kwh: float = Field(
        ge=0
    )

    temperature_c: float

    precipitation_mm: float = Field(
        ge=0
    )

    wind_speed_kmh: float = Field(
        ge=0
    )

    mobility_index: float = Field(
        ge=0
    )

    risk_level: Literal[
        "low",
        "medium",
        "high",
    ]


class ForecastSummary(
    BaseModel
):
    total_predicted_energy_kwh: float = Field(
        ge=0
    )

    average_hourly_energy_kwh: float = Field(
        ge=0
    )

    peak_energy_kwh: float = Field(
        ge=0
    )

    peak_timestamp: str

    historical_p75_kwh: float = Field(
        ge=0
    )

    historical_p90_kwh: float = Field(
        ge=0
    )


class StationDemandForecast(
    BaseModel
):
    available: bool

    station_id: str

    generated_at: str

    forecast_start: str

    horizon_hours: int = Field(
        ge=1,
        le=72,
    )

    model_version: str

    history_source: str

    weather_source: str

    peak_risk: Literal[
        "low",
        "medium",
        "high",
    ]

    summary: ForecastSummary

    training_metrics: dict[
        str,
        Any,
    ]

    points: list[
        ForecastPoint
    ]