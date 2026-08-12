from dataclasses import (
    asdict,
    dataclass,
)
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import (
    ColumnTransformer,
)
from sklearn.ensemble import (
    HistGradientBoostingRegressor,
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
)
from sklearn.pipeline import (
    Pipeline,
)
from sklearn.preprocessing import (
    OneHotEncoder,
)

from app.ml.forecasting.features import (
    CATEGORICAL_FEATURE_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    NUMERIC_FEATURE_COLUMNS,
    TARGET_COLUMN,
    build_forecast_features,
)

MODEL_VERSION = "demand-hgb-v1"


@dataclass
class ForecastMetrics:
    mae_kwh: float
    rmse_kwh: float
    baseline_mae_kwh: float
    baseline_rmse_kwh: float
    mae_improvement_pct: float
    train_rows: int
    test_rows: int
    train_end: str
    test_start: str


@dataclass
class ForecastTrainingResult:
    model_version: str
    metrics: ForecastMetrics
    artifact_path: str


def build_model_pipeline(
) -> Pipeline:
    preprocessor = (
        ColumnTransformer(
            transformers=[
                (
                    "station",
                    OneHotEncoder(
                        handle_unknown=(
                            "ignore"
                        ),
                        sparse_output=False,
                    ),
                    CATEGORICAL_FEATURE_COLUMNS,
                ),
                (
                    "numeric",
                    "passthrough",
                    NUMERIC_FEATURE_COLUMNS,
                ),
            ],
            remainder="drop",
        )
    )

    regressor = (
        HistGradientBoostingRegressor(
            learning_rate=0.05,
            max_iter=250,
            max_leaf_nodes=31,
            min_samples_leaf=20,
            l2_regularization=1.0,
            random_state=42,
        )
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "regressor",
                regressor,
            ),
        ]
    )


def chronological_holdout(
    frame: pd.DataFrame,
    *,
    holdout_days: int = 28,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    if holdout_days < 1:
        raise ValueError(
            "holdout_days must be positive."
        )

    max_timestamp = frame[
        "timestamp"
    ].max()

    cutoff = (
        max_timestamp
        - pd.Timedelta(
            days=holdout_days,
        )
    )

    train = frame[
        frame[
            "timestamp"
        ]
        <= cutoff
    ].copy()

    test = frame[
        frame[
            "timestamp"
        ]
        > cutoff
    ].copy()

    if train.empty or test.empty:
        raise ValueError(
            "Not enough data for chronological holdout."
        )

    return (
        train,
        test,
    )


def _rmse(
    y_true: pd.Series,
    y_pred: np.ndarray,
) -> float:
    mse = mean_squared_error(
        y_true,
        y_pred,
    )

    return float(
        np.sqrt(
            mse
        )
    )


def _safe_baseline(
    test: pd.DataFrame,
) -> pd.Series:
    baseline = (
        test[
            "lag_24h"
        ]
        .fillna(
            test[
                "rolling_mean_24h"
            ]
        )
        .fillna(
            test[
                TARGET_COLUMN
            ].median()
        )
    )

    return baseline.clip(
        lower=0
    )


def train_demand_forecast_model(
    raw_frame: pd.DataFrame,
    *,
    artifact_path: str | Path,
    holdout_days: int = 28,
) -> ForecastTrainingResult:
    frame = (
        build_forecast_features(
            raw_frame
        )
    )

    frame = frame.sort_values(
        "timestamp"
    ).reset_index(
        drop=True
    )

    train, test = (
        chronological_holdout(
            frame,
            holdout_days=(
                holdout_days
            ),
        )
    )

    X_train = train[
        MODEL_FEATURE_COLUMNS
    ]

    y_train = train[
        TARGET_COLUMN
    ]

    X_test = test[
        MODEL_FEATURE_COLUMNS
    ]

    y_test = test[
        TARGET_COLUMN
    ]

    pipeline = (
        build_model_pipeline()
    )

    pipeline.fit(
        X_train,
        y_train,
    )

    predictions = pipeline.predict(
        X_test
    )

    predictions = np.maximum(
        predictions,
        0.0,
    )

    baseline_predictions = (
        _safe_baseline(
            test
        )
        .to_numpy()
    )

    mae = float(
        mean_absolute_error(
            y_test,
            predictions,
        )
    )

    rmse = _rmse(
        y_test,
        predictions,
    )

    baseline_mae = float(
        mean_absolute_error(
            y_test,
            baseline_predictions,
        )
    )

    baseline_rmse = _rmse(
        y_test,
        baseline_predictions,
    )

    if baseline_mae > 0:
        improvement = (
            (
                baseline_mae
                - mae
            )
            / baseline_mae
            * 100.0
        )

    else:
        improvement = 0.0

    metrics = ForecastMetrics(
        mae_kwh=mae,
        rmse_kwh=rmse,
        baseline_mae_kwh=(
            baseline_mae
        ),
        baseline_rmse_kwh=(
            baseline_rmse
        ),
        mae_improvement_pct=(
            float(
                improvement
            )
        ),
        train_rows=len(
            train
        ),
        test_rows=len(
            test
        ),
        train_end=(
            train[
                "timestamp"
            ]
            .max()
            .isoformat()
        ),
        test_start=(
            test[
                "timestamp"
            ]
            .min()
            .isoformat()
        ),
    )

    final_pipeline = (
        build_model_pipeline()
    )

    final_pipeline.fit(
        frame[
            MODEL_FEATURE_COLUMNS
        ],
        frame[
            TARGET_COLUMN
        ],
    )

    output_path = Path(
        artifact_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    artifact: dict[
        str,
        Any,
    ] = {
        "model_version": (
            MODEL_VERSION
        ),
        "trained_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "feature_columns": (
            MODEL_FEATURE_COLUMNS
        ),
        "target_column": (
            TARGET_COLUMN
        ),
        "metrics": (
            asdict(
                metrics
            )
        ),
        "pipeline": (
            final_pipeline
        ),
    }

    joblib.dump(
        artifact,
        output_path,
    )

    return ForecastTrainingResult(
        model_version=(
            MODEL_VERSION
        ),
        metrics=metrics,
        artifact_path=str(
            output_path
        ),
    )