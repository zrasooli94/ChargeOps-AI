from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
        description="The user's message to ChargeOps AI.",
    )


class ChatResponse(BaseModel):
    answer: str