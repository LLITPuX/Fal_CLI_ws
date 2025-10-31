"""Application configuration from environment variables."""

import os
from typing import Literal

from pydantic_settings import BaseSettings


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
    gemini_timeout: int = 90  # seconds
    google_cloud_project: str | None = os.getenv("GOOGLE_CLOUD_PROJECT")

    # Storage Settings
    default_output_dir: str = "data"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False


settings = Settings()

