from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class ChargingIssueRequest(BaseModel):
    station_id: str = Field(
        min_length=1,
        max_length=50,
    )

    issue: str = Field(
        min_length=10,
        max_length=3000,
    )

    charger_model: str | None = Field(
        default=None,
        max_length=100,
    )

    @field_validator("station_id")
    @classmethod
    def normalize_station_id(cls, value: str) -> str:
        return value.strip().upper()


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

    @model_validator(mode="after")
    def validate_escalation(self) -> "ChargingIssueAnalysis":
        if self.severity == "critical":
            self.needs_human_escalation = True

        return self


class ChargingIssueResponse(BaseModel):
    analysis_id: UUID
    created_at: datetime
    model: str

    station_id: str
    charger_model: str | None

    analysis: ChargingIssueAnalysis