import json
from pathlib import Path
from typing import Any

from langsmith import Client

DATASET_NAME = (
    "chargeops-rag-grounding-v1"
)

CASES_PATH = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    / "evals"
    / "rag_grounding_cases.json"
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

    existing = list(
        client.list_datasets(
            dataset_name=(
                DATASET_NAME
            )
        )
    )

    if existing:
        dataset = existing[0]

        print(
            "Dataset already exists:"
        )

        print(
            dataset.name
        )

    else:
        dataset = client.create_dataset(
            dataset_name=(
                DATASET_NAME
            ),
            description=(
                "ChargeOps RAG grounding "
                "and citation-faithfulness "
                "evaluation baseline v1."
            ),
            metadata={
                "project": (
                    "chargeops-ai"
                ),
                "evaluation_type": (
                    "rag-grounding"
                ),
                "version": "v1",
                "case_count": len(
                    cases
                ),
            },
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
                    "require_citations": (
                        case.get(
                            "require_citations",
                            True,
                        )
                    ),
                },
                "metadata": {
                    "case_id": (
                        case["id"]
                    ),
                    "project": (
                        "chargeops-ai"
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
        "Published examples:",
        len(
            examples
        ),
    )


if __name__ == "__main__":
    main()