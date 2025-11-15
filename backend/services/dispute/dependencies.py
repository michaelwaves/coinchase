"""
FastAPI dependency functions.
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from config import Settings, get_settings
import os


async def verify_api_key(settings: Annotated[Settings, Depends(get_settings)]) -> str:
    """
    Verify that the Anthropic API key is configured.
    
    Returns:
        str: The API key
        
    Raises:
        HTTPException: If API key is not configured
    """
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Anthropic API key not configured"
        )
    
    # Set the API key in environment for claude-agent-sdk
    os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
    
    return settings.anthropic_api_key


async def get_claude_config(
    settings: Annotated[Settings, Depends(get_settings)]
) -> dict:
    """
    Get Claude Agent configuration.
    
    Returns:
        dict: Configuration for Claude Agent
    """
    return {
        "max_turns": settings.max_turns,
        "allowed_tools": settings.allowed_tools,
    }

