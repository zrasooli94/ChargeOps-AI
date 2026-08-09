from typing import Literal

from pydantic import BaseModel, Field


class DiagnosticStep(BaseModel):
    step: int = Field(ge=1)
    action: str = Field(min_length=1)


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

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    summary: str = Field(min_length=1)

    likely_causes: list[str]

    diagnostic_steps: list[DiagnosticStep]

    needs_human_escalation: bool