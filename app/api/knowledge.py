from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.knowledge import (
    KnowledgeDocumentResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.services.document_ingestion_service import (
    DocumentIngestionError,
    DuplicateDocumentError,
    ingest_document,
)
from app.services.knowledge_service import (
    KnowledgeServiceError,
    delete_knowledge_document,
    list_knowledge_documents,
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


@router.post(
    "/documents/upload",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
    file: Annotated[
        UploadFile,
        File(),
    ],
    title: Annotated[
        str | None,
        Form(),
    ] = None,
    category: Annotated[
        str,
        Form(),
    ] = "manual",
) -> KnowledgeDocumentResponse:
    filename = (
        file.filename
        or "uploaded-document"
    )

    content = await file.read()

    try:
        document = await ingest_document(
            session=session,
            filename=filename,
            media_type=(
                file.content_type
                or "application/octet-stream"
            ),
            content=content,
            title=title,
            category=category,
        )

        return (
            KnowledgeDocumentResponse
            .model_validate(
                document
            )
        )

    except DuplicateDocumentError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    except DocumentIngestionError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.get(
    "/documents",
    response_model=list[
        KnowledgeDocumentResponse
    ],
)
async def documents(
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> list[
    KnowledgeDocumentResponse
]:
    documents = (
        await list_knowledge_documents(
            session
        )
    )

    return [
        KnowledgeDocumentResponse
        .model_validate(
            document
        )
        for document in documents
    ]


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_document(
    document_id: int,
    session: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> Response:
    deleted = (
        await delete_knowledge_document(
            session=session,
            document_id=document_id,
        )
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=(
                "Knowledge document not found."
            ),
        )

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )