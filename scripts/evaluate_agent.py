from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4
from datetime import (
    datetime,
    timezone,
)
import httpx


API_BASE_URL = os.getenv(
    "CHARGEOPS_API_URL",
    "http://127.0.0.1:8000",
)

CASES_PATH = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    / "evals"
    / "agent_cases.json"
)
RESULTS_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    / "evals"
    / "results"
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


def evaluate_case(
    case: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    used_tools = set(
        result.get(
            "used_tools",
            [],
        )
    )

    required_tools = set(
        case.get(
            "required_tools",
            [],
        )
    )

    forbidden_tools = set(
        case.get(
            "forbidden_tools",
            [],
        )
    )

    expected_approval = (
        case.get(
            "expected_approval",
            False,
        )
    )

    min_answer_chars = int(
        case.get(
            "min_answer_chars",
            0,
        )
    )
    answer_contains_any = [
        str(term).lower()
        for term in case.get(
            "answer_contains_any",
            [],
        )
    ]


    answer = (
        result.get(
            "answer"
        )
        or ""
    )
    normalized_answer = (
        answer.lower()
    )

    checks = {
        "required_tools": (
            required_tools
            .issubset(
                used_tools
            )
        ),
        "forbidden_tools": (
            not bool(
                forbidden_tools
                & used_tools
            )
        ),
        "approval": (
            result.get(
                "approval_required",
                False,
            )
            == expected_approval
        ),
        "answer_length": (
            len(
                answer.strip()
            )
            >= min_answer_chars
        ),
        "answer_contains_any": (
            not answer_contains_any
            or any(
                term
                in normalized_answer
                for term
                in answer_contains_any
            )
        ),
        "thread_id": bool(
            result.get(
                "thread_id"
            )
        ),
        "run_id": bool(
            result.get(
                "run_id"
            )
        ),
    }

    passed = all(
        checks.values()
    )

    return {
        "passed": passed,
        "checks": checks,
        "used_tools": sorted(
            used_tools
        ),
        "approval_required": (
            result.get(
                "approval_required",
                False,
            )
        ),
        "answer": answer,
    }


def print_case_result(
    case: dict[str, Any],
    evaluation: dict[str, Any],
) -> None:
    symbol = (
        "PASS"
        if evaluation[
            "passed"
        ]
        else "FAIL"
    )

    print()
    print(
        "=" * 72
    )

    print(
        f"{symbol}: "
        f"{case['id']}"
    )

    print(
        "-" * 72
    )

    print(
        "Tools:",
        evaluation[
            "used_tools"
        ],
    )

    print(
        "Approval required:",
        evaluation[
            "approval_required"
        ],
    )

    print(
        "Checks:"
    )

    for (
        name,
        passed,
    ) in evaluation[
        "checks"
    ].items():
        marker = (
            "✓"
            if passed
            else "✗"
        )

        print(
            f"  {marker} {name}"
        )

    if not evaluation[
        "passed"
    ]:
        print(
            "\nAnswer:"
        )

        print(
            evaluation[
                "answer"
            ]
        )


def main() -> None:
    cases = load_cases()

    print()
    print(
        "ChargeOps AI "
        "Agent Evaluation Suite"
    )

    print(
        "=" * 72
    )

    print(
        f"Backend: "
        f"{API_BASE_URL}"
    )

    print(
        f"Cases: "
        f"{len(cases)}"
    )
    case_results: list[
        dict[str, Any]
    ] = []

    passed_count = 0

    with httpx.Client(
        timeout=120.0,
    ) as client:
        try:
            health = client.get(
                (
                    f"{API_BASE_URL}"
                    "/health"
                )
            )

            health.raise_for_status()

        except httpx.HTTPError as error:
            print()
            print(
                "ERROR: ChargeOps backend "
                "is not available."
            )

            print(
                error
            )

            sys.exit(
                2
            )

        for case in cases:
            thread_id = str(
                uuid4()
            )

            try:
                response = client.post(
                    (
                        f"{API_BASE_URL}"
                        "/agent/run"
                    ),
                    json={
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
                        "thread_id": (
                            thread_id
                        ),
                    },
                )

                response.raise_for_status()

                result = (
                    response.json()
                )

                evaluation = (
                    evaluate_case(
                        case,
                        result,
                    )
                )

            except httpx.HTTPError as error:
                evaluation = {
                    "passed": False,
                    "checks": {
                        "http_request": False,
                    },
                    "used_tools": [],
                    "approval_required": False,
                    "answer": str(
                        error
                    ),
                }

            print_case_result(
                case,
                evaluation,
            )
            case_results.append(
                {
                    "case_id": case[
                        "id"
                    ],
                    **evaluation,
                }
            )

            if evaluation[
                "passed"
            ]:
                passed_count += 1

    total = len(
        cases
    )

    pass_rate = (
        passed_count
        / total
        * 100
    )
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    
    baseline_result = {
        "baseline": (
            "chargeops-agent-v1"
        ),
        "created_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "backend": (
            API_BASE_URL
        ),
        "total_cases": total,
        "passed_cases": (
            passed_count
        ),
        "pass_rate": (
            round(
                pass_rate,
                2,
            )
        ),
        "cases": case_results,
    }
    
    result_path = (
        RESULTS_DIR
        / "agent_baseline_v1.json"
    )
    
    with result_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            baseline_result,
            file,
            indent=2,
            ensure_ascii=False,
        )
    
    print()
    print(
        "Saved baseline:"
    )
    print(
        result_path
    )

    print()
    print(
        "=" * 72
    )

    print(
        "EVALUATION SUMMARY"
    )

    print(
        "=" * 72
    )

    print(
        f"Passed: "
        f"{passed_count}/{total}"
    )

    print(
        f"Pass rate: "
        f"{pass_rate:.1f}%"
    )

    print()

    if passed_count != total:
        print(
            "Agent evaluation "
            "failures detected."
        )

        sys.exit(
            1
        )

    print(
        "All agent evaluation "
        "cases passed."
    )


if __name__ == "__main__":
    main()