from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class ToolTrace(BaseModel):
    tool: str
    status: Literal[
        "success",
        "error",
    ]
    summary: str


class AgentRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    station_id: str = Field(
        min_length=1,
        max_length=50,
    )

    message: str = Field(
        min_length=3,
        max_length=5000,
    )

    thread_id: UUID | None = None

    @field_validator(
        "station_id"
    )
    @classmethod
    def normalize_station_id(
        cls,
        value: str,
    ) -> str:
        return value.strip().upper()


class AgentResponse(BaseModel):
    thread_id: UUID
    answer: str
    used_tools: list[str]
    trace: list[ToolTrace]