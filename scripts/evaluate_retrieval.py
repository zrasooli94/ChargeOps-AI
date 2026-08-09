import asyncio
import json
from pathlib import Path

from app.core.config import settings
from app.core.database import (
    AsyncSessionLocal,
)
from app.services.knowledge_service import (
    search_knowledge,
)

EVAL_PATH = Path(
    "evals/retrieval_cases.json"
)


async def main() -> None:
    cases = json.loads(
        EVAL_PATH.read_text(
            encoding="utf-8"
        )
    )

    total_cases = len(
        cases
    )

    hits = 0

    reciprocal_rank_total = 0.0

    async with AsyncSessionLocal() as session:
        for case in cases:
            results = await search_knowledge(
                session=session,
                query=case["query"],
                limit=case["top_k"],
                min_similarity=(
                    settings
                    .knowledge_min_similarity
                ),
                max_chunks_per_document=(
                    settings
                    .knowledge_max_chunks_per_document
                ),
            )

            expected = set(
                case[
                    "expected_document_keys"
                ]
            )

            retrieved = [
                result.document_key
                for result in results
            ]

            first_relevant_rank = None

            for rank, document_key in enumerate(
                retrieved,
                start=1,
            ):
                if document_key in expected:
                    first_relevant_rank = rank
                    break

            hit = (
                first_relevant_rank
                is not None
            )

            if first_relevant_rank is not None:
                hits += 1
            
                reciprocal_rank_total += (
                    1.0
                    / first_relevant_rank
                )
            

            print(
                "\n"
                "--------------------------------"
            )

            print(
                f"Case: {case['name']}"
            )

            print(
                f"Query: {case['query']}"
            )

            print(
                f"Expected: "
                f"{', '.join(expected)}"
            )

            print(
                "Retrieved:"
            )

            if results:
                for rank, result in enumerate(
                    results,
                    start=1,
                ):
                    print(
                        f"  {rank}. "
                        f"{result.document_key} | "
                        f"{result.title} | "
                        f"{result.similarity:.4f}"
                    )

            else:
                print(
                    "  No results passed threshold."
                )

            print(
                f"Hit@{case['top_k']}: "
                f"{'YES' if hit else 'NO'}"
            )

            print(
                f"First relevant rank: "
                f"{first_relevant_rank}"
            )

    hit_rate = (
        hits / total_cases
        if total_cases
        else 0.0
    )

    mrr = (
        reciprocal_rank_total
        / total_cases
        if total_cases
        else 0.0
    )

    print(
        "\n"
        "================================"
    )

    print(
        "RETRIEVAL EVALUATION"
    )

    print(
        "================================"
    )

    print(
        f"Cases: {total_cases}"
    )

    print(
        f"Hits: {hits}"
    )

    print(
        f"Hit Rate: {hit_rate:.1%}"
    )

    print(
        f"MRR: {mrr:.4f}"
    )

    print(
        f"Similarity Threshold: "
        f"{settings.knowledge_min_similarity}"
    )

    print(
        f"Max Chunks / Document: "
        f"{settings.knowledge_max_chunks_per_document}"
    )


if __name__ == "__main__":
    asyncio.run(
        main()
    )