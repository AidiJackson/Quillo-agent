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

    # OpenRouter LLM provider
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_fast_model: str = "anthropic/claude-3-haiku"
    openrouter_balanced_model: str = "anthropic/claude-3.5-sonnet"
    openrouter_premium_model: str = "anthropic/claude-opus-4"

    # Anthropic LLM provider (direct)
    anthropic_api_key: str = ""

    # Model routing tier
    model_routing: str = "fast"  # fast|balanced|premium

    # Security settings
    quillo_api_key: str = ""
    cors_allowed_origins: str = ""

    @property
    def cors_origins_list(self) -> list:
        """Parse CORS origins from comma-separated string"""
        if self.cors_allowed_origins:
            return [origin.strip() for origin in self.cors_allowed_origins.split(",")]
        # Default based on environment
        if self.app_env == "dev":
            return ["http://localhost:3000", "http://localhost:8000"]
        else:
            return ["https://app.quillography.ai"]


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton"""
    return Settings()


settings = get_settings()
