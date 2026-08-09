from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.incident import Incident

client = TestClient(app)


def build_incident() -> Incident:
    return Incident(
        id=1,
        station_id="KL-205",
        issue="Charger stops with over-temperature warning.",
        category="hardware",
        severity="high",
        confidence=0.91,
        summary="Possible thermal management fault.",
        likely_causes=[
            "Cooling system issue",
        ],
        diagnostic_steps=[
            {
                "step": 1,
                "action": "Inspect cooling system.",
            }
        ],
        needs_human_escalation=True,
        status="open",
        created_at=datetime.now(
            timezone.utc
        ),
    )


def test_list_incidents() -> None:
    incident = build_incident()

    with patch(
        "app.api.incidents.get_recent_incidents",
        new=AsyncMock(
            return_value=[incident]
        ),
    ):
        response = client.get(
            "/incidents",
            params={
                "station_id": "KL-205",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["station_id"] == "KL-205"
    assert data[0]["severity"] == "high"


def test_get_incident() -> None:
    incident = build_incident()

    with patch(
        "app.api.incidents.get_incident",
        new=AsyncMock(
            return_value=incident
        ),
    ):
        response = client.get(
            "/incidents/1"
        )

    assert response.status_code == 200

    assert response.json()["id"] == 1


def test_incident_not_found() -> None:
    with patch(
        "app.api.incidents.get_incident",
        new=AsyncMock(
            return_value=None
        ),
    ):
        response = client.get(
            "/incidents/999"
        )

    assert response.status_code == 404


def test_update_incident_status() -> None:
    incident = build_incident()
    incident.status = "resolved"

    with patch(
        "app.api.incidents.update_incident_status",
        new=AsyncMock(
            return_value=incident
        ),
    ):
        response = client.patch(
            "/incidents/1",
            json={
                "status": "resolved",
            },
        )

    assert response.status_code == 200

    assert (
        response.json()["status"]
        == "resolved"
    )


def test_rejects_invalid_incident_status() -> None:
    response = client.patch(
        "/incidents/1",
        json={
            "status": "deleted",
        },
    )

    assert response.status_code == 422