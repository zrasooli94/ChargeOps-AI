import json
from pathlib import Path
from typing import Any

from langsmith import Client

DATASET_NAME = (
    "chargeops-agent-baseline-v1"
)

CASES_PATH = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    / "evals"
    / "agent_cases.json"
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
                    "ChargeOps AI Agent "
                    "Evaluation Baseline v1. "
                    "Covers tool routing, "
                    "RAG, operational memory, "
                    "diagnosis, HITL and "
                    "approval-bypass safety."
                ),
                metadata={
                    "project": (
                        "chargeops-ai"
                    ),
                    "baseline": "v1",
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
                    "required_tools": (
                        case.get(
                            "required_tools",
                            [],
                        )
                    ),
                    "forbidden_tools": (
                        case.get(
                            "forbidden_tools",
                            [],
                        )
                    ),
                    "expected_approval": (
                        case.get(
                            "expected_approval",
                            False,
                        )
                    ),
                    "min_answer_chars": (
                        case.get(
                            "min_answer_chars",
                            0,
                        )
                    ),
                    "answer_contains_any": (
                        case.get(
                            "answer_contains_any",
                            [],
                        )
                    ),
                },
                "metadata": {
                    "case_id": (
                        case["id"]
                    ),
                    "baseline": "v1",
                    "project": (
                        "chargeops-ai"
                    ),
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
        "LangSmith dataset:"
    )

    print(
        DATASET_NAME
    )


if __name__ == "__main__":
    main()