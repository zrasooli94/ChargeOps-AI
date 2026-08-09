import hashlib
import logging
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import (
    KnowledgeChunk,
    KnowledgeDocument,
)
from app.services.embedding_service import (
    EmbeddingServiceError,
    create_embeddings,
)

logger = logging.getLogger(__name__)


MAX_FILE_SIZE = 10 * 1024 * 1024

CHUNK_SIZE = 1800
CHUNK_OVERLAP = 250

EMBEDDING_BATCH_SIZE = 64

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
}


class DocumentIngestionError(Exception):
    """Raised when document ingestion fails."""


class DuplicateDocumentError(
    DocumentIngestionError
):
    """Raised when a document already exists."""


@dataclass
class ExtractedUnit:
    text: str
    page_number: int | None


@dataclass
class PreparedChunk:
    text: str
    page_number: int | None


def normalize_text(
    text: str,
) -> str:
    text = text.replace(
        "\x00",
        " ",
    )

    lines = []

    for line in text.splitlines():
        clean_line = re.sub(
            r"[ \t]+",
            " ",
            line,
        ).strip()

        if clean_line:
            lines.append(
                clean_line
            )

    return "\n".join(
        lines
    )


def chunk_text(
    text: str,
    max_chars: int = CHUNK_SIZE,
    overlap_chars: int = CHUNK_OVERLAP,
) -> list[str]:
    clean_text = normalize_text(
        text
    )

    if not clean_text:
        return []

    if len(clean_text) <= max_chars:
        return [
            clean_text
        ]

    chunks: list[str] = []

    start = 0

    while start < len(clean_text):
        end = min(
            start + max_chars,
            len(clean_text),
        )

        if end < len(clean_text):
            sentence_break = (
                clean_text.rfind(
                    ". ",
                    start,
                    end,
                )
            )

            space_break = (
                clean_text.rfind(
                    " ",
                    start,
                    end,
                )
            )

            preferred_break = max(
                sentence_break,
                space_break,
            )

            minimum_break = (
                start
                + max_chars // 2
            )

            if (
                preferred_break
                > minimum_break
            ):
                end = (
                    preferred_break
                    + 1
                )

        chunk = clean_text[
            start:end
        ].strip()

        if chunk:
            chunks.append(
                chunk
            )

        if end >= len(clean_text):
            break

        next_start = (
            end
            - overlap_chars
        )

        start = max(
            next_start,
            start + 1,
        )

    return chunks


def extract_pdf(
    content: bytes,
) -> list[ExtractedUnit]:
    try:
        reader = PdfReader(
            BytesIO(content)
        )

    except Exception as error:
        raise DocumentIngestionError(
            "The PDF could not be read."
        ) from error

    if reader.is_encrypted:
        raise DocumentIngestionError(
            "Encrypted PDFs are not supported."
        )

    units: list[
        ExtractedUnit
    ] = []

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):
        text = normalize_text(
            page.extract_text() or ""
        )

        if text:
            units.append(
                ExtractedUnit(
                    text=text,
                    page_number=page_number,
                )
            )

    total_text = sum(
        len(unit.text)
        for unit in units
    )

    if total_text < 100:
        raise DocumentIngestionError(
            "Very little extractable text was found. "
            "This PDF may be scanned or image-only."
        )

    return units


def extract_text_file(
    content: bytes,
) -> list[ExtractedUnit]:
    try:
        text = content.decode(
            "utf-8-sig"
        )

    except UnicodeDecodeError as error:
        raise DocumentIngestionError(
            "Text files must use UTF-8 encoding."
        ) from error

    clean_text = normalize_text(
        text
    )

    if len(clean_text) < 20:
        raise DocumentIngestionError(
            "The document contains too little text."
        )

    return [
        ExtractedUnit(
            text=clean_text,
            page_number=None,
        )
    ]


def extract_document(
    filename: str,
    content: bytes,
) -> list[ExtractedUnit]:
    extension = (
        Path(filename)
        .suffix
        .lower()
    )

    if (
        extension
        not in SUPPORTED_EXTENSIONS
    ):
        raise DocumentIngestionError(
            "Supported file types are PDF, TXT, and MD."
        )

    if extension == ".pdf":
        return extract_pdf(
            content
        )

    return extract_text_file(
        content
    )


def prepare_chunks(
    units: list[ExtractedUnit],
) -> list[PreparedChunk]:
    prepared: list[
        PreparedChunk
    ] = []

    for unit in units:
        unit_chunks = chunk_text(
            unit.text
        )

        for chunk in unit_chunks:
            prepared.append(
                PreparedChunk(
                    text=chunk,
                    page_number=(
                        unit.page_number
                    ),
                )
            )

    return prepared


async def create_chunk_embeddings(
    chunks: list[PreparedChunk],
) -> list[list[float]]:
    embeddings: list[
        list[float]
    ] = []

    for start in range(
        0,
        len(chunks),
        EMBEDDING_BATCH_SIZE,
    ):
        batch = chunks[
            start:
            start + EMBEDDING_BATCH_SIZE
        ]

        batch_embeddings = (
            await create_embeddings(
                [
                    chunk.text
                    for chunk in batch
                ]
            )
        )

        embeddings.extend(
            batch_embeddings
        )

    return embeddings


async def ingest_document(
    session: AsyncSession,
    filename: str,
    media_type: str,
    content: bytes,
    title: str | None,
    category: str,
) -> KnowledgeDocument:
    if not content:
        raise DocumentIngestionError(
            "The uploaded file is empty."
        )

    if len(content) > MAX_FILE_SIZE:
        raise DocumentIngestionError(
            "The maximum file size is 10 MB."
        )

    file_hash = hashlib.sha256(
        content
    ).hexdigest()

    existing_result = await session.execute(
        select(
            KnowledgeDocument
        ).where(
            KnowledgeDocument.sha256
            == file_hash
        )
    )

    existing = (
        existing_result
        .scalar_one_or_none()
    )

    if existing is not None:
        raise DuplicateDocumentError(
            f"Document already exists as "
            f"#{existing.id}: {existing.title}"
        )

    units = extract_document(
        filename=filename,
        content=content,
    )

    prepared_chunks = (
        prepare_chunks(
            units
        )
    )

    if not prepared_chunks:
        raise DocumentIngestionError(
            "No usable text chunks were generated."
        )

    try:
        embeddings = (
            await create_chunk_embeddings(
                prepared_chunks
            )
        )

        if (
            len(embeddings)
            != len(prepared_chunks)
        ):
            raise DocumentIngestionError(
                "Embedding count did not match chunk count."
            )

        document_key = (
            f"doc-{file_hash[:16]}"
        )

        clean_title = (
            title.strip()
            if title
            and title.strip()
            else Path(filename).stem
        )

        clean_category = (
            category.strip()
            or "manual"
        )

        document = KnowledgeDocument(
            document_key=document_key,
            title=clean_title,
            category=clean_category,
            source_filename=filename,
            media_type=(
                media_type
                or "application/octet-stream"
            ),
            sha256=file_hash,
            status="ready",
            chunk_count=(
                len(prepared_chunks)
            ),
        )

        session.add(
            document
        )

        await session.flush()

        for index, (
            prepared_chunk,
            embedding,
        ) in enumerate(
            zip(
                prepared_chunks,
                embeddings,
                strict=True,
            )
        ):
            chunk_hash = (
                hashlib.sha256(
                    prepared_chunk.text.encode(
                        "utf-8"
                    )
                ).hexdigest()
            )

            chunk = KnowledgeChunk(
                document_key=(
                    f"{document_key}-"
                    f"{index:04d}"
                ),
                title=clean_title,
                category=clean_category,
                source=filename,
                content=(
                    prepared_chunk.text
                ),
                embedding=embedding,
                knowledge_document_id=(
                    document.id
                ),
                chunk_index=index,
                page_number=(
                    prepared_chunk
                    .page_number
                ),
                content_hash=chunk_hash,
                char_count=len(
                    prepared_chunk.text
                ),
            )

            session.add(
                chunk
            )

        await session.commit()

        await session.refresh(
            document
        )

        logger.info(
            "Ingested document id=%s chunks=%s filename=%s",
            document.id,
            document.chunk_count,
            filename,
        )

        return document

    except (
        EmbeddingServiceError,
        SQLAlchemyError,
    ) as error:
        await session.rollback()

        logger.exception(
            "Document ingestion failed"
        )

        raise DocumentIngestionError(
            "Document ingestion failed."
        ) from error