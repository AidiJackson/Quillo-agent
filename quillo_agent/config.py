"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )

    app_env: str = "dev"
    app_port: int = 8000
    database_url: str = "sqlite:///./quillo.db"
    openrouter_api_key: str = ""
    anthropic_api_key: str = ""
    model_routing: str = "fast"  # fast|balanced|premium


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton"""
    return Settings()


settings = get_settings()
