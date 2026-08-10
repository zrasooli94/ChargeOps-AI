from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
)


class AgentRunRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    thread_id: str
    station_id: str

    user_message: str

    status: str

    answer: str | None

    used_tools: list[str]

    trace: list[
        dict[str, Any]
    ]

    approval_required: bool

    approval_decision: (
        bool | None
    )

    model: str

    latency_ms: int

    started_at: datetime

    completed_at: (
        datetime | None
    )