"""Application configuration."""
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Link Analyzer"

    # CORS - Store as string, parse in main.py
    BACKEND_CORS_ORIGINS: str = Field(default="")

    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if not self.BACKEND_CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]

    # Redis Configuration (for caching)
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1  # Use different DB from main backend

    # External Services
    GEMINI_API_KEY: str = ""

    # Rate Limiting Configuration
    GEMINI_MIN_REQUEST_INTERVAL: float = Field(default=2.0)  # Minimum seconds between requests
    GEMINI_MAX_RETRIES: int = Field(default=3)  # Maximum retry attempts
    GEMINI_RETRY_MIN_WAIT: float = Field(default=4.0)  # Minimum wait time for exponential backoff (seconds)
    GEMINI_RETRY_MAX_WAIT: float = Field(default=60.0)  # Maximum wait time for exponential backoff (seconds)

    # Service Configuration
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"


settings = Settings()
