from pydantic import BaseModel, ConfigDict


class StationResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    station_id: str
    name: str
    charger_model: str
    location: str
    latitude: float
    longitude: float
    status: str