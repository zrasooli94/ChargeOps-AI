from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.ml.forecasting.features import (
    MODEL_FEATURE_COLUMNS,
)


class ForecastModelError(
    RuntimeError
):
    """Raised when the forecasting model cannot be used."""


def load_forecast_artifact(
    path: str | Path,
) -> dict[str, Any]:
    artifact_path = Path(
        path
    )

    if not artifact_path.exists():
        raise ForecastModelError(
            "Forecast model artifact does not exist."
        )

    artifact = joblib.load(
        artifact_path
    )

    if not isinstance(
        artifact,
        dict,
    ):
        raise ForecastModelError(
            "Invalid forecast model artifact."
        )

    if "pipeline" not in artifact:
        raise ForecastModelError(
            "Forecast pipeline missing from artifact."
        )

    return artifact


def predict_demand(
    artifact: dict[str, Any],
    feature_frame: pd.DataFrame,
) -> np.ndarray:
    missing = [
        column
        for column in MODEL_FEATURE_COLUMNS
        if column
        not in feature_frame.columns
    ]

    if missing:
        raise ForecastModelError(
            "Forecast features missing: "
            + ", ".join(
                missing
            )
        )

    pipeline = artifact[
        "pipeline"
    ]

    predictions = pipeline.predict(
        feature_frame[
            MODEL_FEATURE_COLUMNS
        ]
    )

    return np.maximum(
        predictions,
        0.0,
    )