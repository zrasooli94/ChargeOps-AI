from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class WeatherRequest(BaseModel):
    station_id: str = Field(
        min_length=1,
        max_length=50,
    )

    latitude: float = Field(
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ge=-180,
        le=180,
    )

    @field_validator("station_id")
    @classmethod
    def normalize_station_id(cls, value: str) -> str:
        return value.strip().upper()


class WeatherData(BaseModel):
    temperature_c: float
    precipitation_mm: float
    wind_speed_kmh: float
    weather_code: int


class WeatherResponse(BaseModel):
    station_id: str
    latitude: float
    longitude: float
    observed_at: datetime

    weather: WeatherData