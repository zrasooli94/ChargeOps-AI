from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.knowledge import (
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.services.knowledge_service import (
    KnowledgeServiceError,
    search_knowledge,
)

router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge"],
)


@router.post(
    "/search",
    response_model=KnowledgeSearchResponse,
)
async def knowledge_search(
    request: KnowledgeSearchRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> KnowledgeSearchResponse:
    try:
        results = await search_knowledge(
            session=session,
            query=request.query,
            limit=request.limit,
        )

        return KnowledgeSearchResponse(
            query=request.query,
            results=results,
        )

    except KnowledgeServiceError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error