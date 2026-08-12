from pathlib import Path

import numpy as np
import pandas as pd

DEMO_STATIONS = [
    {
        "station_id": "KL-101",
        "latitude": 3.1073,
        "longitude": 101.6067,
        "charger_count": 12,
        "max_power_kw": 60.0,
        "station_scale": 1.15,
    },
    {
        "station_id": "KL-205",
        "latitude": 3.1390,
        "longitude": 101.6869,
        "charger_count": 8,
        "max_power_kw": 50.0,
        "station_scale": 0.95,
    },
    {
        "station_id": "KL-330",
        "latitude": 3.1579,
        "longitude": 101.7123,
        "charger_count": 16,
        "max_power_kw": 120.0,
        "station_scale": 1.35,
    },
]


def _gaussian_peak(
    hour: np.ndarray,
    center: float,
    width: float,
) -> np.ndarray:
    return np.exp(
        -0.5
        * (
            (
                hour
                - center
            )
            / width
        )
        ** 2
    )


def generate_demo_demand_data(
    *,
    days: int = 240,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate deterministic hourly EV charging
    demand observations.

    This is simulation data for engineering and
    demonstration only. It must not be presented
    as real operational charging history.
    """

    if days < 30:
        raise ValueError(
            "At least 30 days are required."
        )


    end = (
        pd.Timestamp.now(
            tz="UTC"
        )
        .floor("h")
        - pd.Timedelta(
            hours=1
        )
    )

    timestamps = pd.date_range(
        end=end,
        periods=(
            days
            * 24
        ),
        freq="h",
    )

    frames: list[
        pd.DataFrame
    ] = []

    for station_index, station in enumerate(
        DEMO_STATIONS
    ):
        station_rng = (
            np.random.default_rng(
                seed
                + station_index
                + 1
            )
        )

        frame = pd.DataFrame(
            {
                "timestamp": (
                    timestamps
                )
            }
        )

        hour = (
            frame[
                "timestamp"
            ]
            .dt.hour
            .to_numpy()
        )

        weekday = (
            frame[
                "timestamp"
            ]
            .dt.dayofweek
            .to_numpy()
        )

        day_number = (
            np.arange(
                len(frame)
            )
            / 24.0
        )

        weekend = (
            weekday >= 5
        ).astype(
            float
        )

        morning_peak = (
            _gaussian_peak(
                hour,
                center=8.5,
                width=2.0,
            )
        )

        evening_peak = (
            _gaussian_peak(
                hour,
                center=18.0,
                width=2.8,
            )
        )

        midday_peak = (
            _gaussian_peak(
                hour,
                center=13.0,
                width=3.5,
            )
        )

        temperature = (
            28.0
            + 2.5
            * np.sin(
                2
                * np.pi
                * (
                    hour
                    - 14
                )
                / 24
            )
            + 1.2
            * np.sin(
                2
                * np.pi
                * day_number
                / 90
            )
            + station_rng.normal(
                0,
                0.8,
                len(frame),
            )
        )

        rain_event = (
            station_rng.random(
                len(frame)
            )
            < 0.12
        )

        precipitation = np.where(
            rain_event,
            station_rng.gamma(
                shape=1.6,
                scale=2.0,
                size=len(frame),
            ),
            0.0,
        )

        wind_speed = np.maximum(
            0.5,
            (
                8.0
                + station_rng.normal(
                    0,
                    2.5,
                    len(frame),
                )
            ),
        )

        workday_mobility = (
            25
            + 48
            * morning_peak
            + 55
            * evening_peak
            + 18
            * midday_peak
        )

        weekend_mobility = (
            25
            + 38
            * midday_peak
            + 35
            * evening_peak
        )

        mobility_index = np.where(
            weekend
            > 0,
            weekend_mobility,
            workday_mobility,
        )

        mobility_index = (
            mobility_index
            + station_rng.normal(
                0,
                5.0,
                len(frame),
            )
        )

        mobility_index = np.clip(
            mobility_index,
            0,
            100,
        )

        station_scale = float(
            station[
                "station_scale"
            ]
        )

        demand = (
            3.0
            + 0.22
            * mobility_index
            + 7.0
            * evening_peak
            + 3.0
            * morning_peak
            + 0.22
            * np.maximum(
                temperature
                - 29.0,
                0,
            )
            - 0.45
            * precipitation
        )

        demand = (
            demand
            * station_scale
        )

        demand += (
            station_rng.normal(
                0,
                1.8,
                len(frame),
            )
        )

        demand = np.maximum(
            demand,
            0.0,
        )

        sessions = np.maximum(
            0,
            np.round(
                demand
                / station_rng.uniform(
                    4.5,
                    7.5,
                    len(frame),
                )
            ),
        ).astype(
            int
        )

        frame[
            "station_id"
        ] = station[
            "station_id"
        ]

        frame[
            "latitude"
        ] = station[
            "latitude"
        ]

        frame[
            "longitude"
        ] = station[
            "longitude"
        ]

        frame[
            "charger_count"
        ] = station[
            "charger_count"
        ]

        frame[
            "max_power_kw"
        ] = station[
            "max_power_kw"
        ]

        frame[
            "temperature_c"
        ] = temperature

        frame[
            "precipitation_mm"
        ] = precipitation

        frame[
            "wind_speed_kmh"
        ] = wind_speed

        frame[
            "mobility_index"
        ] = mobility_index

        frame[
            "session_count"
        ] = sessions

        frame[
            "energy_kwh"
        ] = demand

        frames.append(
            frame
        )

    result = pd.concat(
        frames,
        ignore_index=True,
    )

    result = result.sort_values(
        [
            "timestamp",
            "station_id",
        ]
    ).reset_index(
        drop=True
    )

    return result


def save_demo_demand_data(
    path: str | Path,
    *,
    days: int = 240,
    seed: int = 42,
) -> pd.DataFrame:
    output_path = Path(
        path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame = (
        generate_demo_demand_data(
            days=days,
            seed=seed,
        )
    )

    frame.to_csv(
        output_path,
        index=False,
    )

    return frame