from pydantic import BaseModel, Field, field_validator


class AgentRequest(BaseModel):
    station_id: str = Field(
        min_length=1,
        max_length=50,
    )

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


class AgentResponse(BaseModel):
    station_id: str
    answer: str
    used_tools: list[str]