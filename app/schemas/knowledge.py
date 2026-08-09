from pydantic import BaseModel, Field


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