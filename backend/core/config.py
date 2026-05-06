"""Core configuration module."""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "IntelliKnow"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DB_HOST: str = "192.168.20.218"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "lahmy1c"
    DB_NAME: str = "intelliknow"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # API
    API_PREFIX: str = "/api/v1"

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]

    # Crawler settings
    CRAWLER_TIMEOUT: int = 30
    CRAWLER_MAX_RETRIES: int = 3
    DEFAULT_RATE_LIMIT: int = 10

    # Similarity threshold
    SIMILARITY_THRESHOLD: float = 0.85

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
