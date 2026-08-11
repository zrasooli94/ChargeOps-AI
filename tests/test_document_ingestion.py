from datetime import (
    datetime,
    timezone,
)
from unittest.mock import (
    AsyncMock,
    patch,
)

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.knowledge import (
    KnowledgeDocument,
)
from app.services.document_ingestion_service import (
    chunk_text,
    extract_text_file,
)

pytestmark = pytest.mark.usefixtures(
    "authenticated_admin"
)

client = TestClient(
    app
)


def test_chunk_text_creates_overlap() -> None:
    text = (
        "EV charger troubleshooting information. "
        * 150
    )

    chunks = chunk_text(
        text=text,
        max_chars=500,
        overlap_chars=100,
    )

    assert len(chunks) > 1

    assert all(
        len(chunk) <= 510
        for chunk in chunks
    )


def test_extract_text_file() -> None:
    units = extract_text_file(
        
            b"EV charging manual with enough "
            b"technical troubleshooting content."
        
    )

    assert len(units) == 1

    assert (
        "EV charging manual"
        in units[0].text
    )


def test_upload_document() -> None:
    document = KnowledgeDocument(
        id=10,
        document_key="doc-test123",
        title="ABB Charger Manual",
        category="manual",
        source_filename="manual.txt",
        media_type="text/plain",
        sha256="a" * 64,
        status="ready",
        chunk_count=5,
        created_at=datetime.now(
            timezone.utc
        ),
    )

    with patch(
        "app.api.knowledge.ingest_document",
        new=AsyncMock(
            return_value=document
        ),
    ):
        response = client.post(
            "/knowledge/documents/upload",
            files={
                "file": (
                    "manual.txt",
                    b"EV charger manual content.",
                    "text/plain",
                )
            },
            data={
                "title": (
                    "ABB Charger Manual"
                ),
                "category": "manual",
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert (
        data["title"]
        == "ABB Charger Manual"
    )

    assert (
        data["chunk_count"]
        == 5
    )

def test_list_knowledge_documents() -> None:
    document = KnowledgeDocument(
        id=10,
        document_key="doc-test123",
        title="ABB Charger Manual",
        category="manual",
        source_filename="manual.pdf",
        media_type="application/pdf",
        sha256="a" * 64,
        status="ready",
        chunk_count=12,
        created_at=datetime.now(
            timezone.utc
        ),
    )

    with patch(
        "app.api.knowledge.list_knowledge_documents",
        new=AsyncMock(
            return_value=[document]
        ),
    ):
        response = client.get(
            "/knowledge/documents"
        )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == 10
    assert data[0]["chunk_count"] == 12


def test_delete_knowledge_document() -> None:
    with patch(
        "app.api.knowledge.delete_knowledge_document",
        new=AsyncMock(
            return_value=True
        ),
    ):
        response = client.delete(
            "/knowledge/documents/10"
        )

    assert response.status_code == 204


def test_delete_missing_knowledge_document() -> None:
    with patch(
        "app.api.knowledge.delete_knowledge_document",
        new=AsyncMock(
            return_value=False
        ),
    ):
        response = client.delete(
            "/knowledge/documents/999"
        )

    assert response.status_code == 404