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
    openrouter_gemini_model: str = "google/gemini-2.0-flash-exp:free"

    # Anthropic LLM provider (direct)
    anthropic_api_key: str = ""

    # Model routing tier
    model_routing: str = "fast"  # fast|balanced|premium

    # Multi-agent prompt mode
    multi_agent_prompt_mode: str = "raw"  # raw|tuned

    # Raw chat mode (ChatGPT-like behavior)
    raw_chat_mode: bool = True  # True = direct LLM, no auto-suggestions

    # Security settings
    quillo_api_key: str = ""
    quillo_ui_token: str = ""  # UI-facing token for frontend proxy (dev-safe)
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


def is_offline_mode() -> bool:
    """
    Check if the system is running in offline mode (no AI API keys configured).

    Returns True when both OPENROUTER_API_KEY and ANTHROPIC_API_KEY are missing
    or empty. In offline mode, the system uses rule-based classification and
    template-based execution instead of LLM calls.

    Returns:
        True if no AI API keys are configured, False otherwise
    """
    return not settings.openrouter_api_key and not settings.anthropic_api_key
