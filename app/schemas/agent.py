from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


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

    @field_validator("station_id")
    @classmethod
    def normalize_station_id(
        cls,
        value: str,
    ) -> str:
        return value.strip().upper()


class ToolTrace(BaseModel):
    tool: str

    status: Literal[
        "success",
        "error",
    ]

    summary: str


class AgentResponse(BaseModel):
    station_id: str
    answer: str
    used_tools: list[str]
    trace: list[ToolTrace]