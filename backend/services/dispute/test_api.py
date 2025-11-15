"""
Simple test script to verify the API endpoints.
Run this after starting the service to test functionality.

Usage:
    python test_api.py
"""
import httpx
import asyncio
from typing import Optional


BASE_URL = "http://localhost:8000"


async def test_health_check():
    """Test the health check endpoint."""
    print("\n=== Testing Health Check ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200


async def test_simple_query(prompt: str):
    """Test the simple query endpoint."""
    print(f"\n=== Testing Simple Query ===")
    print(f"Prompt: {prompt}")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/claude/query",
            params={"prompt": prompt}
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {result.get('response', 'No response')[:200]}...")
        return response.status_code == 200


async def test_analyze_dispute(
    description: str,
    transaction_id: Optional[str] = None,
    amount: Optional[float] = None
):
    """Test the analyze dispute endpoint."""
    print(f"\n=== Testing Dispute Analysis ===")
    print(f"Description: {description}")
    
    payload = {
        "dispute_description": description,
        "transaction_id": transaction_id,
        "amount": amount
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{BASE_URL}/claude/analyze-dispute",
            json=payload
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Analysis Preview: {result.get('analysis', 'No analysis')[:300]}...")
            print(f"Status: {result.get('status')}")
        else:
            print(f"Error: {response.text}")
        return response.status_code == 200


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Starting API Tests")
    print("=" * 60)
    
    # Test 1: Health Check
    try:
        success = await test_health_check()
        print(f"✅ Health check passed" if success else "❌ Health check failed")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Simple Query
    try:
        success = await test_simple_query("What is 2 + 2?")
        print(f"✅ Simple query passed" if success else "❌ Simple query failed")
    except Exception as e:
        print(f"❌ Simple query error: {e}")
    
    # Test 3: Dispute Analysis
    try:
        success = await test_analyze_dispute(
            description="Customer claims they never received the product. The tracking shows it was delivered, but the customer insists they didn't get it. The order value is $500.",
            transaction_id="TXN-2025-001",
            amount=500.00
        )
        print(f"✅ Dispute analysis passed" if success else "❌ Dispute analysis failed")
    except Exception as e:
        print(f"❌ Dispute analysis error: {e}")
    
    print("\n" + "=" * 60)
    print("Tests Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

