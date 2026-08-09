from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.station import Station

client = TestClient(app)


def build_station() -> Station:
    return Station(
        id=1,
        station_id="KL-205",
        name="ChargeOps Central",
        charger_model="ABB Terra 54",
        location="Kuala Lumpur, Malaysia",
        latitude=3.139,
        longitude=101.6869,
        status="active",
    )


def test_list_stations() -> None:
    station = build_station()

    with patch(
        "app.api.stations.get_all_stations",
        new=AsyncMock(
            return_value=[station]
        ),
    ):
        response = client.get(
            "/stations"
        )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["station_id"] == "KL-205"
    assert data[0]["charger_model"] == "ABB Terra 54"
    assert data[0]["status"] == "active"


def test_get_station() -> None:
    station = build_station()

    with patch(
        "app.api.stations.get_station",
        new=AsyncMock(
            return_value=station
        ),
    ):
        response = client.get(
            "/stations/KL-205"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["station_id"] == "KL-205"
    assert data["name"] == "ChargeOps Central"
    assert data["location"] == "Kuala Lumpur, Malaysia"


def test_station_not_found() -> None:
    with patch(
        "app.api.stations.get_station",
        new=AsyncMock(
            return_value=None
        ),
    ):
        response = client.get(
            "/stations/UNKNOWN"
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Station not found."