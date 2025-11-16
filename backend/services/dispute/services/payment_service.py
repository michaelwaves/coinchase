"""
Service for handling Locus payments.
"""
import logging
import httpx
from typing import Dict, Any, Optional
from config import Settings, get_settings

logger = logging.getLogger(__name__)


async def get_locus_access_token(settings: Settings) -> str:
    """Get OAuth access token for Locus API."""
    oauth_url = "https://auth.paywithlocus.com/oauth2/token"

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": settings.locus_client_id,
        "client_secret": settings.locus_client_secret,
        "scope": "payment_context:read contact_payments:write address_payments:write email_payments:write"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(oauth_url, data=data, headers=headers)
        response.raise_for_status()
        return response.json()["access_token"]


async def call_locus_mcp(
    method: str,
    params: Dict[str, Any],
    settings: Settings
) -> Dict[str, Any]:
    """Call Locus MCP endpoint."""
    access_token = (
        settings.locus_api_key
        if settings.locus_api_key
        else await get_locus_access_token(settings)
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
        "params": params
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            settings.locus_mcp_url,
            json=request_data,
            headers=headers
        )
        response.raise_for_status()

        result = None
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                import json
                result = json.loads(line[6:])
                break

        if not result:
            result = response.json()

        if "error" in result:
            raise Exception(result["error"].get("message", "MCP error"))

        return result.get("result", {})


async def send_refund_to_address(
    address: str,
    amount: float,
    transaction_id: str,
    settings: Optional[Settings] = None
) -> Dict[str, Any]:
    """
    Send USDC refund to wallet address using Locus.

    Args:
        address: Recipient wallet address (0x...)
        amount: Amount in USDC to send
        transaction_id: Original transaction ID for memo
        settings: Application settings (fetched if not provided)

    Returns:
        Payment result with transaction ID and status
    """
    if not settings:
        settings = get_settings()

    logger.info(f"Sending refund: ${amount} to {address} (tx: {transaction_id})")

    result = await call_locus_mcp(
        method="tools/call",
        params={
            "name": "send_to_address",
            "arguments": {
                "address": address,
                "amount": amount,
                "memo": f"Refund for dispute - Transaction: {transaction_id}"
            }
        },
        settings=settings
    )

    logger.info(f"Refund sent successfully: {result}")
    return result
