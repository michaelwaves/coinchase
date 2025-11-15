#!/usr/bin/env python3
"""
Standalone test script for Locus MCP integration.

This script tests the Locus MCP server directly without running the FastAPI app.
It demonstrates:
1. Connecting to the Locus MCP server
2. Listing available payment tools
3. Getting payment context (budget, balance, contacts)

Usage:
    python test_locus_standalone.py

Environment Variables Required:
    LOCUS_API_KEY: Your Locus API key (or LOCUS_CLIENT_ID/SECRET for OAuth)
"""

import os
import json
import asyncio
import httpx
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
LOCUS_MCP_URL = "https://mcp.paywithlocus.com/mcp"
LOCUS_API_KEY = os.getenv("LOCUS_API_KEY", "")
LOCUS_CLIENT_ID = os.getenv("LOCUS_CLIENT_ID", "")
LOCUS_CLIENT_SECRET = os.getenv("LOCUS_CLIENT_SECRET", "")
LOCUS_OAUTH_URL = "https://auth.paywithlocus.com/oauth2/token"


async def get_oauth_token() -> str:
    """
    Get OAuth access token using client credentials flow.
    
    Returns:
        Access token string
    """
    print(f"   Getting OAuth token from {LOCUS_OAUTH_URL}...")
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "client_credentials",
        "client_id": LOCUS_CLIENT_ID,
        "client_secret": LOCUS_CLIENT_SECRET,
        "scope": "payment_context:read contact_payments:write address_payments:write email_payments:write"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(LOCUS_OAUTH_URL, data=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            access_token = result["access_token"]
            print(f"   ✓ OAuth token obtained: {access_token[:20]}...")
            return access_token
        except httpx.HTTPStatusError as e:
            print(f"   ❌ OAuth failed: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"   ❌ OAuth error: {str(e)}")
            raise


async def call_mcp_method(
    method: str,
    params: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """
    Call an MCP method on the Locus server.
    
    Args:
        method: MCP method name (e.g., "tools/list", "resources/list")
        params: Method parameters
        
    Returns:
        MCP response result
    """
    # Determine authentication method
    # Prefer API key over OAuth (API key is simpler and directly supported by MCP)
    access_token = None
    
    if LOCUS_API_KEY:
        # Use API key authentication (recommended for MCP)
        access_token = LOCUS_API_KEY
    elif LOCUS_CLIENT_ID and LOCUS_CLIENT_SECRET:
        # Use OAuth authentication (for LangChain integration)
        access_token = await get_oauth_token()
    else:
        raise ValueError(
            "No Locus credentials configured.\n"
            "Generate an API key at https://app.paywithlocus.com/dashboard/agents\n"
            "Then set LOCUS_API_KEY in your .env file"
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
    
    print(f"\n📤 Calling MCP method: {method}")
    print(f"   Request: {json.dumps(request_data, indent=2)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                LOCUS_MCP_URL,
                json=request_data,
                headers=headers
            )
            response.raise_for_status()
            
            print(f"   Response status: {response.status_code}")
            
            # Parse SSE response format
            response_text = response.text
            
            # SSE format: "event: message\ndata: {json}\n"
            # Extract the JSON from the data line
            result = None
            for line in response_text.split('\n'):
                if line.startswith('data: '):
                    result = json.loads(line[6:])  # Skip "data: " prefix
                    break
            
            if not result:
                # Fallback: try to parse as plain JSON
                result = response.json()
            
            if "error" in result:
                error_msg = result["error"].get("message", "Unknown error")
                print(f"❌ MCP Error: {error_msg}")
                print(f"   Full error: {json.dumps(result['error'], indent=2)}")
                return {"error": error_msg}
            
            return result.get("result", {})
            
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"❌ Request Error: {str(e)}")
            raise


async def main():
    """Main test function."""
    print("=" * 60)
    print("🎯 Starting Locus MCP Integration Test")
    print("=" * 60)
    
    # Check authentication configuration
    if LOCUS_CLIENT_ID and LOCUS_CLIENT_SECRET:
        print(f"\n✓ Auth Method: OAuth 2.0")
        print(f"✓ Client ID: {LOCUS_CLIENT_ID[:20]}...")
        print(f"✓ Client Secret: {'*' * 20}")
    elif LOCUS_API_KEY:
        print(f"\n✓ Auth Method: API Key")
        print(f"✓ API Key: {LOCUS_API_KEY[:20]}...")
    else:
        print("❌ Error: No Locus credentials configured")
        print("\nPlease set one of the following:")
        print("\n  Option 1: API Key Authentication")
        print("    export LOCUS_API_KEY='your_api_key_here'")
        print("\n  Option 2: OAuth Authentication (Recommended)")
        print("    export LOCUS_CLIENT_ID='your_client_id_here'")
        print("    export LOCUS_CLIENT_SECRET='your_client_secret_here'")
        print("\nOr add to .env file")
        return
    
    print(f"✓ MCP URL: {LOCUS_MCP_URL}")
    
    try:
        # Step 1: List available tools
        print("\n" + "─" * 60)
        print("Step 1: Listing MCP Tools")
        print("─" * 60)
        
        tools_result = await call_mcp_method("tools/list")
        
        if "error" not in tools_result:
            tools = tools_result.get("tools", [])
            print(f"\n✓ Found {len(tools)} tools:")
            for i, tool in enumerate(tools, 1):
                tool_name = tool.get("name", "unnamed")
                tool_desc = tool.get("description", "No description")
                print(f"   {i}. {tool_name}")
                print(f"      {tool_desc}")
                
                # Show input schema if available
                if "inputSchema" in tool:
                    schema = tool["inputSchema"]
                    if "properties" in schema:
                        print(f"      Parameters:")
                        for param_name, param_info in schema["properties"].items():
                            param_type = param_info.get("type", "any")
                            param_desc = param_info.get("description", "")
                            required = param_name in schema.get("required", [])
                            req_str = " (required)" if required else ""
                            print(f"        - {param_name}: {param_type}{req_str}")
                            if param_desc:
                                print(f"          {param_desc}")
            
            # Step 3: Test get_payment_context tool
            tool_names = [tool.get("name") for tool in tools]
            
            if "get_payment_context" in tool_names:
                print("\n" + "─" * 60)
                print("Step 2: Testing get_payment_context Tool")
                print("─" * 60)
                
                context_result = await call_mcp_method(
                    "tools/call",
                    {
                        "name": "get_payment_context",
                        "arguments": {}
                    }
                )
                
                if "error" not in context_result:
                    print("\n✓ Payment Context:")
                    print(json.dumps(context_result, indent=2))
                else:
                    print(f"\n⚠️  Could not get payment context: {context_result.get('error')}")
            else:
                print("\n" + "─" * 60)
                print("Step 2: Skipped")
                print("─" * 60)
                print("\n⚠️  get_payment_context tool not available")
                print("   Available tools:", ", ".join(tool_names))
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ Test Completed Successfully!")
        print("=" * 60)
        print("\nNext Steps:")
        print("  • Test the FastAPI endpoint with: curl http://localhost:8000/locus/test")
        print("  • Use the tools to send payments")
        print("  • Integrate with your dispute resolution flow")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ Test Failed")
        print("=" * 60)
        print(f"\nError: {str(e)}")
        print("\nPlease check:")
        print("  • Your LOCUS_API_KEY is valid")
        print("  • You have network connectivity")
        print("  • The Locus MCP server is accessible")
        raise


if __name__ == "__main__":
    asyncio.run(main())

