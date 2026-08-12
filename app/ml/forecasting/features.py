import numpy as np
import pandas as pd

TARGET_COLUMN = "energy_kwh"


NUMERIC_FEATURE_COLUMNS = [
    "latitude",
    "longitude",
    "charger_count",
    "max_power_kw",
    "temperature_c",
    "precipitation_mm",
    "wind_speed_kmh",
    "mobility_index",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
    "month_sin",
    "month_cos",
    "is_weekend",
    "lag_1h",
    "lag_24h",
    "lag_168h",
    "rolling_mean_24h",
    "rolling_mean_168h",
]


CATEGORICAL_FEATURE_COLUMNS = [
    "station_id",
]


MODEL_FEATURE_COLUMNS = (
    CATEGORICAL_FEATURE_COLUMNS
    + NUMERIC_FEATURE_COLUMNS
)


REQUIRED_RAW_COLUMNS = {
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
    TARGET_COLUMN,
}


class ForecastFeatureError(
    ValueError
):
    """Raised when forecast training data is invalid."""


def validate_raw_demand_frame(
    frame: pd.DataFrame,
) -> None:
    missing = (
        REQUIRED_RAW_COLUMNS
        - set(
            frame.columns
        )
    )

    if missing:
        raise ForecastFeatureError(
            "Missing required demand columns: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )

    if frame.empty:
        raise ForecastFeatureError(
            "Demand dataset is empty."
        )


def build_forecast_features(
    raw_frame: pd.DataFrame,
) -> pd.DataFrame:
    validate_raw_demand_frame(
        raw_frame
    )

    frame = raw_frame.copy()

    frame[
        "timestamp"
    ] = pd.to_datetime(
        frame[
            "timestamp"
        ],
        utc=True,
        errors="raise",
    )

    frame = frame.sort_values(
        [
            "station_id",
            "timestamp",
        ]
    ).reset_index(
        drop=True
    )

    timestamp = frame[
        "timestamp"
    ]

    hour = (
        timestamp
        .dt.hour
        .astype(
            float
        )
    )

    weekday = (
        timestamp
        .dt.dayofweek
        .astype(
            float
        )
    )

    month = (
        timestamp
        .dt.month
        .astype(
            float
        )
    )

    frame[
        "hour_sin"
    ] = np.sin(
        2
        * np.pi
        * hour
        / 24
    )

    frame[
        "hour_cos"
    ] = np.cos(
        2
        * np.pi
        * hour
        / 24
    )

    frame[
        "weekday_sin"
    ] = np.sin(
        2
        * np.pi
        * weekday
        / 7
    )

    frame[
        "weekday_cos"
    ] = np.cos(
        2
        * np.pi
        * weekday
        / 7
    )

    frame[
        "month_sin"
    ] = np.sin(
        2
        * np.pi
        * (
            month
            - 1
        )
        / 12
    )

    frame[
        "month_cos"
    ] = np.cos(
        2
        * np.pi
        * (
            month
            - 1
        )
        / 12
    )

    frame[
        "is_weekend"
    ] = (
        timestamp
        .dt.dayofweek
        .ge(5)
        .astype(
            int
        )
    )

    grouped = frame.groupby(
        "station_id",
        sort=False,
    )[
        TARGET_COLUMN
    ]

    frame[
        "lag_1h"
    ] = grouped.shift(
        1
    )

    frame[
        "lag_24h"
    ] = grouped.shift(
        24
    )

    frame[
        "lag_168h"
    ] = grouped.shift(
        168
    )

    frame[
        "rolling_mean_24h"
    ] = (
        grouped
        .transform(
            lambda values: (
                values
                .shift(1)
                .rolling(
                    window=24,
                    min_periods=6,
                )
                .mean()
            )
        )
    )

    frame[
        "rolling_mean_168h"
    ] = (
        grouped
        .transform(
            lambda values: (
                values
                .shift(1)
                .rolling(
                    window=168,
                    min_periods=24,
                )
                .mean()
            )
        )
    )

    return frame