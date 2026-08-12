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

    # =============================================
    # OpenAI
    # =============================================

    openai_api_key: str | None = None

    openai_model: str = "gpt-5-mini"

    openai_timeout_seconds: float = Field(
        default=45.0,
        ge=5.0,
        le=120.0,
    )

    openai_connect_timeout_seconds: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
    )

    openai_max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
    )

    observability_write_timeout_seconds: float = Field(
        default=2.0,
        ge=0.5,
        le=10.0,
    )

    # =============================================
    # Weather
    # =============================================

    weather_base_url: str = (
        "https://api.open-meteo.com/"
        "v1/forecast"
    )

    weather_connect_timeout_seconds: float = Field(
        default=3.0,
        ge=0.5,
        le=30.0,
    )

    weather_read_timeout_seconds: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
    )

    weather_write_timeout_seconds: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
    )

    weather_pool_timeout_seconds: float = Field(
        default=2.0,
        ge=0.5,
        le=30.0,
    )

    weather_max_connections: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    weather_max_keepalive_connections: int = Field(
        default=10,
        ge=1,
        le=50,
    )

    weather_max_attempts: int = Field(
        default=3,
        ge=1,
        le=5,
    )

    weather_retry_base_delay_seconds: float = Field(
        default=0.25,
        ge=0.0,
        le=5.0,
    )

    # =============================================
    # Embeddings / knowledge
    # =============================================

    embedding_model: str = (
        "text-embedding-3-small"
    )

    embedding_dimensions: int = 1536

    knowledge_min_similarity: float = 0.45

    knowledge_max_chunks_per_document: int = 2

    knowledge_candidate_multiplier: int = 6

    # =============================================
    # PostgreSQL
    # =============================================

    database_url: str = (
        "postgresql+psycopg://"
        "chargeops:chargeops@"
        "localhost:5432/chargeops"
    )

    database_pool_size: int = Field(
        default=5,
        ge=1,
        le=50,
    )

    database_max_overflow: int = Field(
        default=10,
        ge=0,
        le=50,
    )

    database_pool_timeout_seconds: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
    )

    database_pool_recycle_seconds: int = Field(
        default=1800,
        ge=60,
        le=86400,
    )

    database_ready_timeout_seconds: float = Field(
        default=3.0,
        ge=0.5,
        le=15.0,
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

    # =============================================
    # CORS
    # =============================================

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

    # =============================================
    # Security headers
    # =============================================

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

    # =============================================
    # Model Context Protocol
    # =============================================
    
    mcp_host: str = "127.0.0.1"
    
    mcp_port: int = Field(
        default=8001,
        ge=1024,
        le=65535,
    )
    
    mcp_streamable_http_path: str = "/mcp"


    # =============================================
    # External MCP client
    # =============================================
    
    external_mcp_timeout_seconds: float = Field(
        default=45.0,
        ge=5.0,
        le=90.0,
    )
    
    external_mcp_max_content_chars: int = Field(
        default=8000,
        ge=1000,
        le=20000,
    )
    
    external_mcp_allowed_hosts: str = (
        "openchargealliance.org"
    )
    
    @property
    def external_mcp_allowed_hosts_list(
        self,
    ) -> list[str]:
        return [
            host.strip().lower()
            for host in (
                self.external_mcp_allowed_hosts
                .split(",")
            )
            if host.strip()
        ]

    # =============================================
    # Pydantic settings
    # =============================================

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