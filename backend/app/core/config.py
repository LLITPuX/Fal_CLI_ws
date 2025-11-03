"""Application configuration from environment variables."""

import os
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # API Settings
    api_title: str = "Gemini Text Structurer API"
    api_version: str = "2.0.0"
    api_description: str = "Async FastAPI service for structuring text via Gemini CLI"
    api_port: int = int(os.getenv("API_PORT", "8000"))

    # CORS Settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Gemini CLI Settings
    gemini_cli: str = os.getenv("GEMINI_CLI", "gemini")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_timeout: int = 300  # seconds (5 minutes per model)
    google_cloud_project: str | None = os.getenv("GOOGLE_CLOUD_PROJECT")

    # Gemini models for testing
    # For free tier, use only gemini-2.5-flash to avoid quota limits
    # gemini-2.5-pro has very low RPM (2) and daily limits
    # Provide a comma-separated list via GEMINI_MODELS env var when needed
    gemini_models: list[str] | str = Field(
        default_factory=lambda: [
            "gemini-2.5-flash",  # Best balance: 15 RPM, good quality
            # "gemini-2.5-pro",  # Uncomment for paid tier only (2 RPM)
        ]
    )

    @model_validator(mode="after")
    def normalize_gemini_models(self) -> "Settings":
        """Ensure gemini_models is a non-empty list."""

        value = self.gemini_models
        if isinstance(value, str):
            models = [item.strip() for item in value.split(",") if item.strip()]
        else:
            models = list(value)

        if not models:
            models = ["gemini-2.5-flash"]

        self.gemini_models = models
        return self

    # Storage Settings
    default_output_dir: str = "data"

    # FalkorDB Settings
    falkordb_host: str = os.getenv("FALKORDB_HOST", "falkordb")
    falkordb_port: int = int(os.getenv("FALKORDB_PORT", "6379"))
    falkordb_graph_name: str = os.getenv("FALKORDB_GRAPH_NAME", "gemini_graph")
    falkordb_max_query_time: int = int(os.getenv("FALKORDB_MAX_QUERY_TIME", "30"))

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )


settings = Settings()

