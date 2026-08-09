from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.weather import WeatherData
from app.services.weather_service import WeatherServiceError

client = TestClient(app)


def test_current_weather_success() -> None:
    mock_weather = WeatherData(
        temperature_c=31.5,
        precipitation_mm=0.2,
        wind_speed_kmh=12.4,
        weather_code=3,
    )

    with patch(
        "app.api.weather.get_current_weather",
        new=AsyncMock(
            return_value=(
                datetime.fromisoformat("2026-08-09T05:00:00"),
                mock_weather,
            )
        ),
    ):
        response = client.post(
            "/weather/current",
            json={
                "station_id": "kl-205",
                "latitude": 3.139,
                "longitude": 101.6869,
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["station_id"] == "KL-205"
    assert data["weather"]["temperature_c"] == 31.5
    assert data["weather"]["precipitation_mm"] == 0.2


def test_weather_rejects_invalid_latitude() -> None:
    response = client.post(
        "/weather/current",
        json={
            "station_id": "KL-205",
            "latitude": 200,
            "longitude": 101.6869,
        },
    )

    assert response.status_code == 422


def test_weather_service_failure() -> None:
    with patch(
        "app.api.weather.get_current_weather",
        new=AsyncMock(
            side_effect=WeatherServiceError(
                "Failed to retrieve weather data."
            )
        ),
    ):
        response = client.post(
            "/weather/current",
            json={
                "station_id": "KL-205",
                "latitude": 3.139,
                "longitude": 101.6869,
            },
        )

    assert response.status_code == 503