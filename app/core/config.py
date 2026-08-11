from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    app_name: str = "ChargeOps AI"
    app_environment: str = "development"

    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"

    weather_base_url: str = (
        "https://api.open-meteo.com/v1/forecast"
    )

    embedding_model: str = (
        "text-embedding-3-small"
    )

    embedding_dimensions: int = 1536

    knowledge_min_similarity: float = 0.45
    knowledge_max_chunks_per_document: int = 2
    knowledge_candidate_multiplier: int = 6

    database_url: str = (
        "postgresql+psycopg://"
        "chargeops:chargeops@"
        "localhost:5432/chargeops"
    )

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # =============================================
    # Login rate limiting
    # =============================================

    login_rate_limit_ip_attempts: int = Field(
        default=20,
        ge=1,
    )

    login_rate_limit_account_attempts: int = Field(
        default=5,
        ge=1,
    )

    login_rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def checkpoint_database_url(
        self,
    ) -> str:
        return self.database_url.replace(
            "postgresql+psycopg://",
            "postgresql://",
            1,
        )


settings = Settings()