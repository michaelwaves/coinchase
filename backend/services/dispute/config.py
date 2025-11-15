"""
Configuration settings for the Dispute Service.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    app_name: str = "Dispute Service"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Anthropic API Configuration
    anthropic_api_key: str
    
    # Claude Agent Configuration
    max_turns: int = 5
    allowed_tools: list[str] = ["Read", "Write", "Bash"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()

