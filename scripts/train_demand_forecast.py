import argparse
from dataclasses import (
    asdict,
)
from pathlib import Path

import pandas as pd

from app.ml.forecasting.demo_data import (
    save_demo_demand_data,
)
from app.ml.forecasting.modeling import (
    train_demand_forecast_model,
)

DEFAULT_DATA_PATH = Path(
    "data/forecasting/"
    "demand_history.csv"
)

DEFAULT_ARTIFACT_PATH = Path(
    "artifacts/"
    "demand_forecast.joblib"
)


def parse_args(
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Train the ChargeOps EV charging "
            "demand forecasting model."
        )
    )

    parser.add_argument(
        "--data",
        type=Path,
        default=(
            DEFAULT_DATA_PATH
        ),
    )

    parser.add_argument(
        "--artifact",
        type=Path,
        default=(
            DEFAULT_ARTIFACT_PATH
        ),
    )

    parser.add_argument(
        "--generate-demo",
        action="store_true",
    )

    parser.add_argument(
        "--demo-days",
        type=int,
        default=240,
    )

    parser.add_argument(
        "--holdout-days",
        type=int,
        default=28,
    )

    return parser.parse_args()


def main(
) -> None:
    args = parse_args()

    if args.generate_demo:
        frame = (
            save_demo_demand_data(
                args.data,
                days=args.demo_days,
            )
        )

        print(
            "Generated demo observations:",
            len(
                frame
            ),
        )

        print(
            "Demo data:",
            args.data,
        )

    if not args.data.exists():
        raise SystemExit(
            "Demand dataset does not exist. "
            "Use --generate-demo or provide --data."
        )

    raw_frame = pd.read_csv(
        args.data
    )

    result = (
        train_demand_forecast_model(
            raw_frame,
            artifact_path=(
                args.artifact
            ),
            holdout_days=(
                args.holdout_days
            ),
        )
    )

    print()
    print(
        "Model:",
        result.model_version,
    )

    print(
        "Artifact:",
        result.artifact_path,
    )

    print()

    for key, value in asdict(
        result.metrics
    ).items():
        print(
            f"{key}: {value}"
        )


if __name__ == "__main__":
    main()