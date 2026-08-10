import json
from pathlib import Path
from typing import Any

from langsmith import Client

DATASET_NAME = (
    "chargeops-agent-quality-v1"
)

CASES_PATH = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    / "evals"
    / "quality_cases.json"
)


def load_cases() -> list[
    dict[str, Any]
]:
    with CASES_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(
            file
        )


def main() -> None:
    client = Client()

    cases = load_cases()

    existing_datasets = list(
        client.list_datasets(
            dataset_name=(
                DATASET_NAME
            )
        )
    )

    if existing_datasets:
        dataset = (
            existing_datasets[0]
        )

        print(
            "Dataset already exists:"
        )

        print(
            dataset.name
        )

    else:
        dataset = (
            client.create_dataset(
                dataset_name=(
                    DATASET_NAME
                ),
                description=(
                    "ChargeOps AI semantic "
                    "quality evaluation v1. "
                    "Measures technical usefulness, "
                    "evidence discipline, diagnosis "
                    "quality and HITL safety."
                ),
                metadata={
                    "project": (
                        "chargeops-ai"
                    ),
                    "evaluation_type": (
                        "llm-as-judge"
                    ),
                    "version": "v1",
                    "case_count": len(
                        cases
                    ),
                },
            )
        )

        print(
            "Created dataset:"
        )

        print(
            dataset.name
        )

    existing_examples = list(
        client.list_examples(
            dataset_id=(
                dataset.id
            )
        )
    )

    if existing_examples:
        print(
            "Dataset already contains "
            f"{len(existing_examples)} "
            "examples."
        )

        print(
            "No examples were duplicated."
        )

        return

    examples = []

    for case in cases:
        examples.append(
            {
                "inputs": {
                    "case_id": (
                        case["id"]
                    ),
                    "station_id": (
                        case[
                            "station_id"
                        ]
                    ),
                    "message": (
                        case[
                            "message"
                        ]
                    ),
                },
                "outputs": {
                    "quality_rubric": (
                        case[
                            "quality_rubric"
                        ]
                    ),
                },
                "metadata": {
                    "case_id": (
                        case["id"]
                    ),
                    "project": (
                        "chargeops-ai"
                    ),
                    "evaluation": (
                        "semantic-quality"
                    ),
                    "version": "v1",
                },
            }
        )

    client.create_examples(
        dataset_id=dataset.id,
        examples=examples,
    )

    print()
    print(
        "Published examples:"
    )

    print(
        len(
            examples
        )
    )

    print()
    print(
        "Dataset:"
    )

    print(
        DATASET_NAME
    )


if __name__ == "__main__":
    main()