from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AgentRequest(BaseModel):
    station_id: str = Field(
        min_length=1,
        max_length=50,
    )
    charger_model: str | None = None
    
    # charger_model: str | None = Field(
    #     default=None,
    #     max_length=100,
    # )

    latitude: float = Field(
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ge=-180,
        le=180,
    )

    message: str = Field(
        min_length=3,
        max_length=5000,
    )

    @field_validator("station_id")
    @classmethod
    def normalize_station_id(cls, value: str) -> str:
        return value.strip().upper()


class ToolTrace(BaseModel):
    tool: str
    status: Literal["success"]
    summary: str


class AgentResponse(BaseModel):
    station_id: str
    answer: str
    used_tools: list[str]
    trace: list[ToolTrace]