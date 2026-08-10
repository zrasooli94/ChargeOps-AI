from typing import (
    Any,
    Literal,
)
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


class AgentApprovalRequest(BaseModel):
    type: str
    tool: str
    action: str

    station_id: str
    station_name: str

    current_status: str
    requested_status: str

    warning: str


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


class AgentResumeRequest(BaseModel):
    thread_id: UUID
    approved: bool


class AgentResponse(BaseModel):
    run_id: UUID
    
    thread_id: UUID

    answer: str = ""

    used_tools: list[str]

    trace: list[ToolTrace]

    approval_required: bool = False

    approval_request: (
        AgentApprovalRequest | None
    ) = None

    retrieved_evidence: list[
        dict[str, Any]
    ] = Field(
        default_factory=list
    )
    