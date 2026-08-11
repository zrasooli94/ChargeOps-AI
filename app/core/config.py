from typing import Literal

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    app_name: str = "ChargeOps AI"
    app_environment: Literal[
        "development",
        "test",
        "production",
    ] = "development"

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

    # =============================================
    # JWT / session security
    # =============================================
    
    jwt_secret_key: str = ""
    
    jwt_algorithm: Literal[
        "HS256"
    ] = "HS256"
    
    jwt_issuer: str = "chargeops-ai"
    
    jwt_audience: str = "chargeops-api"
    
    jwt_leeway_seconds: int = Field(
        default=30,
        ge=0,
        le=120,
    )
    
    access_token_expire_minutes: int = Field(
        default=30,
        ge=5,
        le=60,
    )

    cors_allowed_origins: str = (
        "http://localhost:8501,"
        "http://127.0.0.1:8501"
    )

    @property
    def cors_allowed_origins_list(
        self,
    ) -> list[str]:
        origins = [
            origin.strip()
            for origin in (
                self.cors_allowed_origins
                .split(",")
            )
            if origin.strip()
        ]
    
        if "*" in origins:
            raise ValueError(
                "Wildcard CORS origins are not "
                "allowed for ChargeOps."
            )
    
        return origins

    security_enable_hsts: bool = False
    
    security_hsts_max_age: int = Field(
        default=31536000,
        ge=0,
    )

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