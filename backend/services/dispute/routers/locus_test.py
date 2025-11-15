"""
Locus MCP Test Router - Test endpoint for Locus payment integration.
"""
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, Dict, Any
from pydantic import BaseModel

from config import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/locus",
    tags=["locus-test"]
)


class LocusTestResponse(BaseModel):
    """Response model for Locus test."""
    status: str
    mcp_connected: bool
    tools_available: list[str]
    payment_context: Dict[str, Any] | None = None
    resources: list[Dict[str, Any]] | None = None
    error: str | None = None


class MCPRequest(BaseModel):
    """MCP JSON-RPC request model."""
    jsonrpc: str = "2.0"
    id: int | str
    method: str
    params: Dict[str, Any] | None = None


class MCPResponse(BaseModel):
    """MCP JSON-RPC response model."""
    jsonrpc: str
    id: int | str
    result: Dict[str, Any] | None = None
    error: Dict[str, Any] | None = None


async def get_locus_access_token(settings: Settings) -> str:
    """
    Get access token for Locus API using OAuth client credentials flow.
    
    Args:
        settings: Application settings
        
    Returns:
        Access token string
        
    Raises:
        HTTPException: If token retrieval fails
    """
    oauth_url = "https://auth.paywithlocus.com/oauth2/token"
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "client_credentials",
        "client_id": settings.locus_client_id,
        "client_secret": settings.locus_client_secret,
        "scope": "payment_context:read contact_payments:write address_payments:write email_payments:write"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(oauth_url, data=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result["access_token"]
        except Exception as e:
            logger.error(f"Failed to get OAuth token: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to authenticate with Locus: {str(e)}"
            )


async def call_mcp_method(
    method: str,
    params: Dict[str, Any] | None,
    settings: Settings
) -> Dict[str, Any]:
    """
    Call an MCP method on the Locus server.
    
    Args:
        method: MCP method name (e.g., "tools/list", "tools/call")
        params: Method parameters
        settings: Application settings
        
    Returns:
        MCP response result
        
    Raises:
        HTTPException: If the request fails
    """
    # Determine authentication method
    # Prefer API key over OAuth (API key is simpler and directly supported by MCP)
    access_token = None
    
    if settings.locus_api_key:
        # Use API key authentication (recommended for MCP)
        logger.info("Using API key authentication")
        access_token = settings.locus_api_key
    elif settings.locus_client_id and settings.locus_client_secret:
        # Use OAuth authentication (for LangChain integration)
        logger.info("Using OAuth authentication")
        access_token = await get_locus_access_token(settings)
    else:
        raise HTTPException(
            status_code=500,
            detail="No Locus credentials configured. Generate an API key at https://app.paywithlocus.com/dashboard/agents and set LOCUS_API_KEY"
        )
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }
    
    logger.info(f"Calling MCP method: {method}")
    logger.debug(f"Request: {request_data}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                settings.locus_mcp_url,
                json=request_data,
                headers=headers
            )
            response.raise_for_status()
            
            # Parse SSE response format
            response_text = response.text
            logger.debug(f"Raw response: {response_text}")
            
            # SSE format: "event: message\ndata: {json}\n"
            # Extract the JSON from the data line
            result = None
            for line in response_text.split('\n'):
                if line.startswith('data: '):
                    import json
                    result = json.loads(line[6:])  # Skip "data: " prefix
                    break
            
            if not result:
                # Fallback: try to parse as plain JSON
                result = response.json()
            
            logger.debug(f"Parsed result: {result}")
            
            if "error" in result:
                error_msg = result["error"].get("message", "Unknown error")
                logger.error(f"MCP error: {error_msg}")
                raise HTTPException(
                    status_code=500,
                    detail=f"MCP error: {error_msg}"
                )
            
            return result.get("result", {})
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling MCP: {e}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"MCP request failed: {str(e)}"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error calling MCP: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"MCP server unreachable: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error calling MCP: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(e)}"
            )


@router.get("/test", response_model=LocusTestResponse)
async def test_locus_mcp(
    settings: Annotated[Settings, Depends(get_settings)]
) -> LocusTestResponse:
    """
    Test endpoint for Locus MCP integration.
    
    This endpoint tests:
    1. Listing available payment tools
    2. Getting payment context (budget, balance, contacts)
    
    Returns:
        LocusTestResponse: Test results with available tools and payment context
    """
    logger.info("Testing Locus MCP integration...")
    
    try:
        # 1. List available tools
        logger.info("Step 1: Listing MCP tools...")
        tools_result = await call_mcp_method(
            method="tools/list",
            params={},
            settings=settings
        )
        
        tools = tools_result.get("tools", [])
        tool_names = [tool.get("name") for tool in tools]
        logger.info(f"Found {len(tool_names)} tools: {tool_names}")
        
        # 2. Get payment context (if available)
        payment_context = None
        if "get_payment_context" in tool_names:
            logger.info("Step 2: Getting payment context...")
            try:
                context_result = await call_mcp_method(
                    method="tools/call",
                    params={
                        "name": "get_payment_context",
                        "arguments": {}
                    },
                    settings=settings
                )
                payment_context = context_result
                logger.info("Successfully retrieved payment context")
            except Exception as e:
                logger.warning(f"Could not get payment context: {e}")
        else:
            logger.info("Step 2: Skipped (get_payment_context not available)")
        
        return LocusTestResponse(
            status="success",
            mcp_connected=True,
            tools_available=tool_names,
            payment_context=payment_context,
            resources=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return LocusTestResponse(
            status="error",
            mcp_connected=False,
            tools_available=[],
            error=str(e)
        )


@router.post("/call-tool")
async def call_locus_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    settings: Annotated[Settings, Depends(get_settings)]
) -> Dict[str, Any]:
    """
    Call a specific Locus MCP tool.
    
    Args:
        tool_name: Name of the tool to call
        arguments: Tool arguments
        settings: Application settings
        
    Returns:
        Tool execution result
    """
    logger.info(f"Calling Locus tool: {tool_name}")
    
    result = await call_mcp_method(
        method="tools/call",
        params={
            "name": tool_name,
            "arguments": arguments
        },
        settings=settings
    )
    
    return result

