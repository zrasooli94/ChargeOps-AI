from __future__ import annotations

import json
import os
import re
from typing import Any
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import run_evaluator
from langsmith.schemas import Example, Run
from openevals.llm import (
    create_async_llm_as_judge,
)
from openevals.prompts import (
    RAG_GROUNDEDNESS_PROMPT,
    RAG_RETRIEVAL_RELEVANCE_PROMPT,
)

load_dotenv()


API_BASE_URL = os.getenv(
    "CHARGEOPS_API_URL",
    "http://127.0.0.1:8000",
)

DATASET_NAME = (
    "chargeops-rag-grounding-v1"
)

_raw_judge_model = os.getenv(
    "EVAL_JUDGE_MODEL",
    "gpt-5-mini",
)

JUDGE_MODEL = (
    _raw_judge_model
    if ":" in _raw_judge_model
    else (
        f"openai:"
        f"{_raw_judge_model}"
    )
)


groundedness_judge = (
    create_async_llm_as_judge(
        prompt=(
            RAG_GROUNDEDNESS_PROMPT
        ),
        feedback_key=(
            "rag_groundedness"
        ),
        model=JUDGE_MODEL,
    )
)


retrieval_relevance_judge = (
    create_async_llm_as_judge(
        prompt=(
            RAG_RETRIEVAL_RELEVANCE_PROMPT
        ),
        feedback_key=(
            "retrieval_relevance"
        ),
        model=JUDGE_MODEL,
    )
)


CITATION_FAITHFULNESS_PROMPT = """
You are evaluating citation faithfulness in a
retrieval-augmented EV charging assistant.

You are given:

1. the assistant answer,
2. the exact retrieved evidence available to the
   assistant.

Retrieved evidence items contain citation identifiers
such as KB1, KB2, and KB3.

Score citation faithfulness using:

0.0
One or more citations are fabricated, refer to evidence
that does not exist, or materially misrepresent what
their cited evidence supports.

0.5
The citations are mostly reasonable, but some claims are
only partially supported or attribution is ambiguous.

1.0
Every cited technical claim is supported by the evidence
identified by that citation. No citation is fabricated or
materially misleading.

Do not require every generic sentence to have a citation.
Evaluate whether citations that ARE used faithfully
represent their associated evidence.

<context>
{context}
</context>

<outputs>
{outputs}
</outputs>
"""


citation_faithfulness_judge = (
    create_async_llm_as_judge(
        prompt=(
            CITATION_FAITHFULNESS_PROMPT
        ),
        feedback_key=(
            "citation_faithfulness"
        ),
        choices=[
            0.0,
            0.5,
            1.0,
        ],
        model=JUDGE_MODEL,
    )
)


async def chargeops_target(
    inputs: dict[str, Any],
) -> dict[str, Any]:
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

        result = response.json()

        if not isinstance(
            result,
            dict,
        ):
            raise TypeError(
                "ChargeOps API returned "
                "an unexpected response."
            )

        return result


def get_outputs(
    run: Run,
) -> dict[str, Any]:
    if run.outputs is None:
        return {}

    return dict(
        run.outputs
    )


def get_inputs(
    example: Example | None,
) -> dict[str, Any]:
    if (
        example is None
        or example.inputs is None
    ):
        return {}

    return dict(
        example.inputs
    )


def get_reference(
    example: Example | None,
) -> dict[str, Any]:
    if (
        example is None
        or example.outputs is None
    ):
        return {}

    return dict(
        example.outputs
    )


def build_context(
    outputs: dict[str, Any],
) -> dict[str, list[str]]:
    evidence = outputs.get(
        "retrieved_evidence",
        [],
    )

    if not isinstance(
        evidence,
        list,
    ):
        return {
            "documents": [],
        }

    documents = [
        json.dumps(
            item,
            ensure_ascii=False,
            default=str,
        )
        for item in evidence
    ]

    return {
        "documents": documents,
    }


def normalize_judge_result(
    result: Any,
    key: str,
) -> dict[str, Any]:
    if not isinstance(
        result,
        dict,
    ):
        raise TypeError(
            f"{key} evaluator returned "
            "an unexpected result."
        )

    score = result.get(
        "score"
    )

    comment = result.get(
        "comment"
    )

    if (
        comment is not None
        and not isinstance(
            comment,
            str,
        )
    ):
        comment = str(
            comment
        )

    return {
        "key": key,
        "score": score,
        "comment": comment,
    }


@run_evaluator
async def rag_groundedness(
    run: Run,
    example: Example | None,
) -> dict[str, Any]:
    del example

    outputs = get_outputs(
        run
    )

    context = build_context(
        outputs
    )

    result = await groundedness_judge(
        context=context,
        outputs={
            "answer": (
                outputs.get(
                    "answer"
                )
                or ""
            ),
        },
    )

    return normalize_judge_result(
        result,
        "rag_groundedness",
    )


@run_evaluator
async def retrieval_relevance(
    run: Run,
    example: Example | None,
) -> dict[str, Any]:
    outputs = get_outputs(
        run
    )

    inputs = get_inputs(
        example
    )

    context = build_context(
        outputs
    )

    result = (
        await retrieval_relevance_judge(
            inputs={
                "question": (
                    inputs.get(
                        "message"
                    )
                    or ""
                ),
            },
            context=context,
        )
    )

    return normalize_judge_result(
        result,
        "retrieval_relevance",
    )


@run_evaluator
def citation_validity(
    run: Run,
    example: Example | None,
) -> dict[str, Any]:
    outputs = get_outputs(
        run
    )

    reference = get_reference(
        example
    )

    require_citations = bool(
        reference.get(
            "require_citations",
            False,
        )
    )

    answer = str(
        outputs.get(
            "answer"
        )
        or ""
    )

    citations = {
        citation.upper()
        for citation in re.findall(
            r"\bKB\d+\b",
            answer,
            flags=re.IGNORECASE,
        )
    }

    evidence = outputs.get(
        "retrieved_evidence",
        [],
    )

    evidence_ids: set[str] = set()

    if isinstance(
        evidence,
        list,
    ):
        for item in evidence:
            if not isinstance(
                item,
                dict,
            ):
                continue

            citation_id = item.get(
                "citation_id"
            )

            if citation_id:
                evidence_ids.add(
                    str(
                        citation_id
                    ).upper()
                )

    valid = (
        (
            not require_citations
            or bool(
                citations
            )
        )
        and citations.issubset(
            evidence_ids
        )
    )

    return {
        "key": "citation_validity",
        "score": valid,
        "comment": (
            "Answer citations: "
            f"{sorted(citations)}; "
            "retrieved evidence IDs: "
            f"{sorted(evidence_ids)}"
        ),
    }


@run_evaluator
async def citation_faithfulness(
    run: Run,
    example: Example | None,
) -> dict[str, Any]:
    del example

    outputs = get_outputs(
        run
    )

    context = build_context(
        outputs
    )

    result = (
        await citation_faithfulness_judge(
            context=context,
            outputs={
                "answer": (
                    outputs.get(
                        "answer"
                    )
                    or ""
                ),
            },
        )
    )

    return normalize_judge_result(
        result,
        "citation_faithfulness",
    )


async def main() -> None:
    client = Client()

    print()
    print(
        "ChargeOps RAG Grounding "
        "Evaluation"
    )

    print(
        "=" * 72
    )

    print(
        "Dataset:",
        DATASET_NAME,
    )

    print(
        "Judge:",
        JUDGE_MODEL,
    )

    print()

    results = await client.aevaluate(
        chargeops_target,
        data=DATASET_NAME,
        evaluators=[
            rag_groundedness,
            retrieval_relevance,
            citation_validity,
            citation_faithfulness,
        ],
        experiment_prefix=(
            "chargeops-rag-v1"
        ),
        description=(
            "ChargeOps RAG groundedness, "
            "retrieval relevance and "
            "citation-faithfulness baseline."
        ),
        metadata={
            "project": (
                "chargeops-ai"
            ),
            "evaluation_type": (
                "rag-groundedness"
            ),
            "version": "v1",
            "judge_model": (
                JUDGE_MODEL
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