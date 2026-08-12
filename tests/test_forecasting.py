from pathlib import Path
from typing import cast

import numpy as np

from app.ml.forecasting.demo_data import (
    generate_demo_demand_data,
)
from app.ml.forecasting.features import (
    MODEL_FEATURE_COLUMNS,
    build_forecast_features,
)
from app.ml.forecasting.modeling import (
    chronological_holdout,
    train_demand_forecast_model,
)
from app.ml.forecasting.service import (
    load_forecast_artifact,
    predict_demand,
)
from app.services.agent_tools import (
    TOOLS,
)


def test_demo_forecasting_data_has_expected_sources(
) -> None:
    frame = (
        generate_demo_demand_data(
            days=30
        )
    )

    expected_columns = {
        "timestamp",
        "station_id",
        "temperature_c",
        "precipitation_mm",
        "wind_speed_kmh",
        "mobility_index",
        "latitude",
        "longitude",
        "energy_kwh",
    }

    assert expected_columns.issubset(
        frame.columns
    )

    assert len(
        frame
    ) == (
        30
        * 24
        * 3
    )

def test_demand_forecast_tool_is_registered(
) -> None:
    names = {
        tool[
            "name"
        ]
        for tool
        in TOOLS
    }

    assert (
        "forecast_station_demand"
        in names
    )


def test_feature_engineering_uses_previous_demand_for_lag(
) -> None:
    raw = (
        generate_demo_demand_data(
            days=30
        )
    )

    features = (
        build_forecast_features(
            raw
        )
    )

    station = (
        features[
            features[
                "station_id"
            ]
            == "KL-101"
        ]
        .reset_index(
            drop=True
        )
    )

    lag_1h = cast(
        float,
        station.loc[
            1,
            "lag_1h",
        ],
    )

    previous_energy = cast(
        float,
        station.loc[
            0,
            "energy_kwh",
        ],
    )

    assert np.isclose(
        lag_1h,
        previous_energy,
    )



def test_forecast_feature_columns_exist(
) -> None:
    frame = (
        build_forecast_features(
            generate_demo_demand_data(
                days=30
            )
        )
    )

    assert all(
        column
        in frame.columns
        for column
        in MODEL_FEATURE_COLUMNS
    )


def test_chronological_holdout_does_not_mix_future_into_training(
) -> None:
    frame = (
        build_forecast_features(
            generate_demo_demand_data(
                days=60
            )
        )
    )

    train, test = (
        chronological_holdout(
            frame,
            holdout_days=7,
        )
    )

    assert (
        train[
            "timestamp"
        ].max()
        <
        test[
            "timestamp"
        ].min()
    )


def test_training_creates_model_artifact(
    tmp_path: Path,
) -> None:
    raw = (
        generate_demo_demand_data(
            days=60
        )
    )

    artifact_path = (
        tmp_path
        / "forecast.joblib"
    )

    result = (
        train_demand_forecast_model(
            raw,
            artifact_path=(
                artifact_path
            ),
            holdout_days=7,
        )
    )

    assert artifact_path.exists()

    assert (
        result.metrics.mae_kwh
        >= 0
    )

    assert (
        result.metrics.rmse_kwh
        >= 0
    )


def test_loaded_model_predicts_non_negative_demand(
    tmp_path: Path,
) -> None:
    raw = (
        generate_demo_demand_data(
            days=60
        )
    )

    artifact_path = (
        tmp_path
        / "forecast.joblib"
    )

    train_demand_forecast_model(
        raw,
        artifact_path=(
            artifact_path
        ),
        holdout_days=7,
    )

    artifact = (
        load_forecast_artifact(
            artifact_path
        )
    )

    features = (
        build_forecast_features(
            raw
        )
    )

    predictions = (
        predict_demand(
            artifact,
            features.tail(
                12
            ),
        )
    )

    assert len(
        predictions
    ) == 12

    assert np.all(
        predictions
        >= 0
    )