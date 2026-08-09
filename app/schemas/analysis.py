from typing import Literal

from pydantic import BaseModel, Field


class ChargingIssueAnalysis(BaseModel):
    category: Literal[
        "hardware",
        "software",
        "network",
        "power",
        "payment",
        "unknown",
    ]

    severity: Literal[
        "low",
        "medium",
        "high",
        "critical",
    ]

    summary: str = Field(min_length=1)

    recommended_action: str = Field(min_length=1)