"""
Application configuration using Pydantic Settings.

Follows backend_reference pattern with Pydantic v1 syntax.
"""

import secrets
from typing import List, Optional, Union

from pydantic import BaseSettings, Field, validator  # type: ignore


class Settings(BaseSettings):
    """Application settings with environment variable validation."""

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Hotly App"
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = Field(default_factory=list)

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from environment variable."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database Configuration
    POSTGRES_SERVER: str = Field(
        default="localhost", description="PostgreSQL server host"
    )
    POSTGRES_USER: str = Field(default="hotly_user", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(
        default="hotly_password", description="PostgreSQL password"
    )
    POSTGRES_DB: str = Field(default="hotly_db", description="PostgreSQL database name")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Assemble PostgreSQL database URI."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", description="Redis server host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")

    @property
    def REDIS_URL(self) -> str:
        """Assemble Redis connection URL."""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # External Services
    FIREBASE_CREDENTIALS_PATH: Optional[str] = Field(
        default=None, description="Firebase service account credentials file path"
    )
    FIREBASE_CREDENTIALS_JSON: Optional[str] = Field(
        default=None, description="Firebase service account credentials JSON string"
    )
    FCM_PROJECT_ID: Optional[str] = Field(
        default=None, description="Firebase Cloud Messaging project ID"
    )
    KAKAO_API_KEY: Optional[str] = Field(default=None, description="Kakao Map API key")
    GEMINI_API_KEY: Optional[str] = Field(
        default=None, description="Google Gemini API key"
    )

    # Push Notification Configuration
    NOTIFICATION_BATCH_SIZE: int = Field(
        default=500, description="Maximum number of notifications to send in one batch"
    )
    NOTIFICATION_RETRY_ATTEMPTS: int = Field(
        default=3, description="Number of retry attempts for failed notifications"
    )
    DEFAULT_NOTIFICATION_TTL: int = Field(
        default=3600,
        description="Default notification time-to-live in seconds (1 hour)",
    )
    MAX_DAILY_NOTIFICATIONS_PER_USER: int = Field(
        default=10, description="Maximum daily notifications per user"
    )
    QUIET_HOURS_START: int = Field(
        default=22,
        ge=0,
        le=23,
        description="Default quiet hours start (24-hour format)",
    )
    QUIET_HOURS_END: int = Field(
        default=7, ge=0, le=23, description="Default quiet hours end (24-hour format)"
    )

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    DEBUG: bool = Field(default=False, description="Debug mode")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Log level")

    # Testing
    TESTING: bool = Field(default=False, description="Testing mode")
    TEST_DATABASE_URL: Optional[str] = Field(
        default=None, description="Test database URL"
    )

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
