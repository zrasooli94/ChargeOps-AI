from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(
        min_length=3,
        max_length=3000,
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=20,
    )


class KnowledgeSearchResult(BaseModel):
    id: int
    document_key: str
    title: str
    category: str
    source: str
    content: str
    similarity: float


class KnowledgeSearchResponse(BaseModel):
    query: str

    results: list[
        KnowledgeSearchResult
    ]


class KnowledgeDocumentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    document_key: str
    title: str
    category: str
    source_filename: str
    media_type: str
    status: str
    chunk_count: int
    created_at: datetime