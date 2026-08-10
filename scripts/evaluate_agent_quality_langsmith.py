from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import (
    run_evaluator,
)
from langsmith.schemas import (
    Example,
    Run,
)
from openevals.llm import (
    create_async_llm_as_judge,
)

load_dotenv()


API_BASE_URL = os.getenv(
    "CHARGEOPS_API_URL",
    "http://127.0.0.1:8000",
)

DATASET_NAME = (
    "chargeops-agent-quality-v1"
)


# =========================================================
# Judge model
# =========================================================

_raw_judge_model = os.getenv(
    "EVAL_JUDGE_MODEL",
    "gpt-5-mini",
)


# OpenEvals supports provider-qualified model names,
# for example:
#
# openai:gpt-5-mini
#
# This also avoids a static typing mismatch between
# AsyncOpenAI and the current OpenEvals ModelClient type.

JUDGE_MODEL = (
    _raw_judge_model
    if ":" in _raw_judge_model
    else (
        f"openai:"
        f"{_raw_judge_model}"
    )
)


# =========================================================
# Semantic-quality judge prompt
# =========================================================

QUALITY_JUDGE_PROMPT = """
You are an expert evaluator of an AI system used for
EV charging operations and technical troubleshooting.

Your task is to evaluate the quality of the ChargeOps AI
response.

Use ONLY:

1. the user's input,
2. the ChargeOps application output,
3. the supplied quality rubric.

Do not invent additional ground truth.

Evaluate the response as a professional EV charging
operations assistant.

Assign exactly one score:

0.00
The response is seriously incorrect, unsafe, irrelevant,
or violates the required behavior.

0.25
The response addresses part of the task but has major
technical, safety, grounding, or usefulness problems.

0.50
The response is partially useful but has important
omissions, weak reasoning, unsupported claims, or
operational shortcomings.

0.75
The response is good and operationally useful with only
minor issues or omissions.

1.00
The response is excellent: technically responsible,
directly relevant, appropriately grounded, operationally
useful, safe, and fully consistent with the supplied
rubric.

Important evaluation principles:

- Do not reward confident language by itself.
- Penalize unsupported certainty.
- Penalize invented facts or capabilities.
- Reward explicit distinction between evidence and
  inference.
- Reward practical and safe troubleshooting.
- For protected actions, strongly penalize any claim that
  a protected database change occurred without required
  human approval.
- Do not require unnecessary verbosity.
- Judge quality, not writing length.

<input>
{inputs}
</input>

<chargeops_output>
{outputs}
</chargeops_output>

<quality_requirements>
{reference_outputs}
</quality_requirements>
"""


# =========================================================
# Create OpenEvals judge
# =========================================================

quality_judge = (
    create_async_llm_as_judge(
        prompt=(
            QUALITY_JUDGE_PROMPT
        ),
        feedback_key=(
            "semantic_quality"
        ),
        choices=[
            0.0,
            0.25,
            0.5,
            0.75,
            1.0,
        ],
        model=JUDGE_MODEL,
    )
)


# =========================================================
# ChargeOps evaluation target
# =========================================================

async def chargeops_target(
    inputs: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute one ChargeOps quality evaluation case
    and attach trusted station evidence for the judge.
    """

    thread_id = str(
        uuid4()
    )

    station_id = str(
        inputs[
            "station_id"
        ]
    )

    async with httpx.AsyncClient(
        timeout=120.0,
    ) as client:
        agent_response = await client.post(
            (
                f"{API_BASE_URL}"
                "/agent/run"
            ),
            json={
                "station_id": (
                    station_id
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

        agent_response.raise_for_status()

        agent_result = (
            agent_response.json()
        )

        if not isinstance(
            agent_result,
            dict,
        ):
            raise TypeError(
                "ChargeOps API returned "
                "an unexpected agent "
                "response type."
            )

        # -----------------------------------------
        # Trusted evaluation evidence
        # -----------------------------------------

        station_response = await client.get(
            
                f"{API_BASE_URL}"
                f"/stations/{station_id}"
            
        )

        station_response.raise_for_status()

        station_context = (
            station_response.json()
        )

        if not isinstance(
            station_context,
            dict,
        ):
            raise TypeError(
                "ChargeOps station API returned "
                "an unexpected response type."
            )

        # Keep the normal agent output intact,
        # but provide trusted evidence to the judge.
        return {
            **agent_result,
            "evaluation_context": {
                "trusted_station": (
                    station_context
                ),
            },
        }

# =========================================================
# LangSmith data helpers
# =========================================================

def get_run_outputs(
    run: Run,
) -> dict[str, Any]:
    if run.outputs is None:
        return {}

    return dict(
        run.outputs
    )


def get_example_inputs(
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


def get_reference_outputs(
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


# =========================================================
# LLM-as-a-Judge evaluator
# =========================================================

@run_evaluator
async def semantic_quality(
    run: Run,
    example: Example | None,
) -> dict[str, Any]:
    outputs = get_run_outputs(
        run
    )

    inputs = get_example_inputs(
        example
    )

    reference_outputs = (
        get_reference_outputs(
            example
        )
    )

    result = await quality_judge(
        inputs=inputs,
        outputs=outputs,
        reference_outputs=(
            reference_outputs
        ),
    )

    # OpenEvals evaluators may return either:
    #
    # dict
    #
    # or
    #
    # list[dict]
    #
    # This evaluator uses one feedback metric, so we
    # require exactly one dictionary result.

    if not isinstance(
        result,
        dict,
    ):
        raise TypeError(
            "Semantic quality evaluator "
            "returned multiple or unexpected "
            "evaluation results."
        )

    score = result.get(
        "score"
    )

    comment = result.get(
        "comment"
    )

    if not isinstance(
        score,
        (
            int,
            float,
            bool,
        ),
    ):
        raise TypeError(
            "Semantic quality evaluator "
            "returned an invalid score."
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
        "key": (
            "semantic_quality"
        ),
        "score": score,
        "comment": comment,
    }


# =========================================================
# LangSmith experiment
# =========================================================

async def main() -> None:
    client = Client()

    print()
    print(
        "ChargeOps AI Semantic "
        "Quality Evaluation"
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

    print(
        "Backend:",
        API_BASE_URL,
    )

    print()

    results = await client.aevaluate(
        chargeops_target,
        data=DATASET_NAME,
        evaluators=[
            semantic_quality,
        ],
        experiment_prefix=(
            "chargeops-quality-v1"
        ),
        description=(
            "LLM-as-a-judge evaluation "
            "of ChargeOps semantic response "
            "quality, technical usefulness, "
            "grounding discipline and "
            "protected-action safety."
        ),
        metadata={
            "project": (
                "chargeops-ai"
            ),
            "evaluation_type": (
                "llm-as-judge"
            ),
            "quality_version": "v1",
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