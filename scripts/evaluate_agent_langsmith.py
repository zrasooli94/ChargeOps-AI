from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

import httpx
from langsmith import Client
from langsmith.evaluation import run_evaluator
from langsmith.schemas import Example, Run

API_BASE_URL = os.getenv(
    "CHARGEOPS_API_URL",
    "http://127.0.0.1:8000",
)

DATASET_NAME = (
    "chargeops-agent-baseline-v1"
)


# =========================================================
# ChargeOps evaluation target
# =========================================================


async def chargeops_target(
    inputs: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute one ChargeOps agent evaluation case.

    Every evaluation example gets a fresh conversation
    thread so cases cannot influence each other.
    """

    thread_id = str(
        uuid4()
    )

    async with httpx.AsyncClient(
        timeout=120.0,
    ) as client:
        response = await client.post(
            (
                f"{API_BASE_URL}"
                "/agent/run"
            ),
            json={
                "station_id": (
                    inputs[
                        "station_id"
                    ]
                ),
                "message": (
                    inputs[
                        "message"
                    ]
                ),
                "thread_id": (
                    thread_id
                ),
            },
        )

        response.raise_for_status()

        return response.json()


# =========================================================
# Evaluator helpers
# =========================================================


def get_outputs(
    run: Run,
) -> dict[str, Any]:
    """
    Safely extract application outputs from
    the LangSmith Run object.
    """

    if run.outputs is None:
        return {}

    return dict(
        run.outputs
    )


def get_reference_outputs(
    example: Example | None,
) -> dict[str, Any]:
    """
    Safely extract expected outputs from
    the LangSmith dataset example.
    """

    if (
        example is None
        or example.outputs is None
    ):
        return {}

    return dict(
        example.outputs
    )


# =========================================================
# Evaluator 1
# Required tools
# =========================================================


@run_evaluator
def required_tools(
    run: Run,
    example: Example | None,
) -> dict[str, Any]:
    outputs = get_outputs(
        run
    )

    reference = (
        get_reference_outputs(
            example
        )
    )

    actual_tools = set(
        outputs.get(
            "used_tools",
            [],
        )
    )

    required = set(
        reference.get(
            "required_tools",
            [],
        )
    )

    passed = (
        required.issubset(
            actual_tools
        )
    )

    return {
        "key": "required_tools",
        "score": passed,
    }


# =========================================================
# Evaluator 2
# Forbidden tools
# =========================================================


@run_evaluator
def forbidden_tools(
    run: Run,
    example: Example | None,
) -> dict[str, Any]:
    outputs = get_outputs(
        run
    )

    reference = (
        get_reference_outputs(
            example
        )
    )

    actual_tools = set(
        outputs.get(
            "used_tools",
            [],
        )
    )

    forbidden = set(
        reference.get(
            "forbidden_tools",
            [],
        )
    )

    passed = not bool(
        actual_tools
        & forbidden
    )

    return {
        "key": "forbidden_tools",
        "score": passed,
    }


# =========================================================
# Evaluator 3
# Human approval correctness
# =========================================================


@run_evaluator
def approval_correct(
    run: Run,
    example: Example | None,
) -> dict[str, Any]:
    outputs = get_outputs(
        run
    )

    reference = (
        get_reference_outputs(
            example
        )
    )

    expected = (
        reference.get(
            "expected_approval",
            False,
        )
    )

    actual = outputs.get(
        "approval_required",
        False,
    )

    return {
        "key": "approval_correct",
        "score": (
            actual == expected
        ),
    }


# =========================================================
# Evaluator 4
# Minimum answer length
# =========================================================


@run_evaluator
def answer_length(
    run: Run,
    example: Example | None,
) -> dict[str, Any]:
    outputs = get_outputs(
        run
    )

    reference = (
        get_reference_outputs(
            example
        )
    )

    answer = (
        outputs.get(
            "answer"
        )
        or ""
    )

    minimum = int(
        reference.get(
            "min_answer_chars",
            0,
        )
    )

    passed = (
        len(
            answer.strip()
        )
        >= minimum
    )

    return {
        "key": "answer_length",
        "score": passed,
    }


# =========================================================
# Evaluator 5
# Safety language
# =========================================================


@run_evaluator
def safety_language(
    run: Run,
    example: Example | None,
) -> dict[str, Any]:
    outputs = get_outputs(
        run
    )

    reference = (
        get_reference_outputs(
            example
        )
    )

    expected_terms = [
        str(
            term
        ).lower()
        for term
        in reference.get(
            "answer_contains_any",
            [],
        )
    ]

    if not expected_terms:
        return {
            "key": (
                "safety_language"
            ),
            "score": True,
        }

    answer = (
        outputs.get(
            "answer"
        )
        or ""
    ).lower()

    passed = any(
        term in answer
        for term
        in expected_terms
    )

    return {
        "key": (
            "safety_language"
        ),
        "score": passed,
    }


# =========================================================
# Evaluator 6
# Persistent conversation thread
# =========================================================


@run_evaluator
def has_thread_id(
    run: Run,
    example: Example | None,
) -> dict[str, Any]:
    del example

    outputs = get_outputs(
        run
    )

    return {
        "key": "has_thread_id",
        "score": bool(
            outputs.get(
                "thread_id"
            )
        ),
    }


# =========================================================
# Evaluator 7
# Observability run ID
# =========================================================


@run_evaluator
def has_run_id(
    run: Run,
    example: Example | None,
) -> dict[str, Any]:
    del example

    outputs = get_outputs(
        run
    )

    return {
        "key": "has_run_id",
        "score": bool(
            outputs.get(
                "run_id"
            )
        ),
    }


# =========================================================
# LangSmith experiment
# =========================================================


async def main() -> None:
    client = Client()

    print()
    print(
        "ChargeOps LangSmith "
        "Experiment"
    )

    print(
        "=" * 72
    )

    print(
        "Dataset:",
        DATASET_NAME,
    )

    print(
        "Backend:",
        API_BASE_URL,
    )

    print()

    results = await client.aevaluate(
        chargeops_target,
        data=DATASET_NAME,
        evaluators=[
            required_tools,
            forbidden_tools,
            approval_correct,
            answer_length,
            safety_language,
            has_thread_id,
            has_run_id,
        ],
        experiment_prefix=(
            "chargeops-agent-v1"
        ),
        description=(
            "ChargeOps AI baseline "
            "agent evaluation. "
            "Measures deterministic "
            "routing, RAG, HITL and "
            "safety behavior."
        ),
        metadata={
            "project": (
                "chargeops-ai"
            ),
            "baseline": "v1",
            "evaluation_type": (
                "deterministic"
            ),
        },
        max_concurrency=1,
    )

    print()
    print(
        results
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(
        main()
    )