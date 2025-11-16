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
    
    # Locus API Configuration (supports both OAuth and API Key auth)
    locus_api_key: str = ""  # Simple API key authentication
    locus_client_id: str = ""  # OAuth Client ID
    locus_client_secret: str = ""  # OAuth Client Secret
    locus_mcp_url: str = "https://mcp.paywithlocus.com/mcp"
    
    # Claude Agent Configuration
    max_turns: int = 5
    allowed_tools: list[str] = ["Read", "Write", "Bash"]

    # CDP Wallet Configuration
    cdp_api_key_id: str = ""
    cdp_api_key_secret: str = ""
    public_merchant_wallet_address: str = ""
    merchant_wallet_private_key: str = ""

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

