from fastapi.testclient import (
    TestClient,
)

from app.main import app

client = TestClient(app)


def test_viewer_cannot_upload_document(
    authenticated_viewer,
) -> None:
    response = client.post(
        "/knowledge/documents/upload",
        files={
            "file": (
                "test.txt",
                b"test knowledge",
                "text/plain",
            ),
        },
        data={
            "title": "Test Document",
            "category": "manual",
        },
    )

    assert response.status_code == 403


def test_operator_cannot_upload_document(
    authenticated_operator,
) -> None:
    response = client.post(
        "/knowledge/documents/upload",
        files={
            "file": (
                "test.txt",
                b"test knowledge",
                "text/plain",
            ),
        },
        data={
            "title": "Test Document",
            "category": "manual",
        },
    )

    assert response.status_code == 403


def test_viewer_cannot_delete_document(
    authenticated_viewer,
) -> None:
    response = client.delete(
        "/knowledge/documents/1"
    )

    assert response.status_code == 403


def test_operator_cannot_delete_document(
    authenticated_operator,
) -> None:
    response = client.delete(
        "/knowledge/documents/1"
    )

    assert response.status_code == 403


def test_viewer_cannot_update_incident(
    authenticated_viewer,
) -> None:
    response = client.patch(
        "/incidents/1",
        json={
            "status": "resolved",
        },
    )

    assert response.status_code == 403