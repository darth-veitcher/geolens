"""
Configuration management for GeoLens.
Environment variables are loaded from .env file if present.
"""
from functools import lru_cache
from typing import Optional

from pydantic import PostgresDsn, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "geolens"
    POSTGRES_PORT: int = 5433
    POSTGRES_HOST: str = "localhost"
    DATABASE_POOL_SIZE: int = 20
    
    # Derived database URL
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_url(cls, v: Optional[str], values) -> str:
        """Construct database URL from components."""
        if v:
            return v
        
        user = values.data.get("POSTGRES_USER")
        password = values.data.get("POSTGRES_PASSWORD")
        db = values.data.get("POSTGRES_DB")
        port = values.data.get("POSTGRES_PORT")
        host = values.data.get("POSTGRES_HOST")

        if all([user, password, db, port, host]):
            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
        
        raise ValueError("Database connection details incomplete")

    # Application
    DEBUG: bool = False
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4

    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


@lru_cache()
def get_settings() -> Settings:
    """Create cached settings instance."""
    return Settings()