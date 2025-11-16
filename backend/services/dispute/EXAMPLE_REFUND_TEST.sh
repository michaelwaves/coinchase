#!/bin/bash
# Example test script for automatic refund processing in dispute flow

# Set your API key
API_KEY="your_api_key_here"
BASE_URL="http://localhost:8000"

echo "=========================================="
echo "Testing Automatic Refund Processing"
echo "=========================================="
echo ""

echo "Step 1: Submit initial dispute analysis request with refund details"
echo "This will trigger the analysis agent to evaluate the dispute."
echo ""

curl -X POST "$BASE_URL/dispute/analyze" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "dispute_description": "I ordered a blue widget but received a red one. The seller refuses to provide a refund despite their return policy.",
    "transaction_id": "tx_12345",
    "amount": 0.001,
    "recipient_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
  }'

echo ""
echo ""
echo "=========================================="
echo "Expected Behavior:"
echo "=========================================="
echo "1. If the agent determines this is NOT fraud (APPROVE_REFUND)"
echo "2. AND the decision is made before max turns (step < 3)"
echo "3. THEN the system will automatically:"
echo "   - Call the Locus send_to_address endpoint"
echo "   - Send \$25.00 USDC to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
echo "   - Include transaction ID tx_12345 in the memo"
echo "   - Return status 'completed' with payment confirmation"
echo ""
echo "4. If the agent needs more evidence:"
echo "   - Status will be 'needs_evidence'"
echo "   - A session_id will be returned"
echo "   - Use the session_id to provide additional evidence"
echo ""
echo "=========================================="
echo "Notes:"
echo "=========================================="
echo "- Ensure LOCUS_API_KEY is set in your .env file"
echo "- The recipient_address must be a valid wallet address"
echo "- The amount must match the disputed amount"
echo "- Payment is only triggered for APPROVE_REFUND decisions"
echo ""
