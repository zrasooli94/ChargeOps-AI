from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.analysis import DiagnosticStep


class IncidentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    station_id: str
    issue: str
    category: str
    severity: str
    confidence: float
    summary: str
    likely_causes: list[str]
    diagnostic_steps: list[DiagnosticStep]
    needs_human_escalation: bool
    status: str
    created_at: datetime


class IncidentStatusUpdate(BaseModel):
    status: Literal[
        "open",
        "investigating",
        "resolved",
    ]