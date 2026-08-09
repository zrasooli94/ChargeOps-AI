from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ChargeOps AI"
    app_environment: str = "development"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    weather_base_url: str = "https://api.open-meteo.com/v1/forecast"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        "postgresql+psycopg://chargeops:chargeops@localhost:5432/chargeops"
    )


settings = Settings()