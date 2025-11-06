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

    # Service Configuration
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"


settings = Settings()
