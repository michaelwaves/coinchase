#!/bin/bash
# Example: Transaction that WILL BE APPROVED for automatic refund
#
# This example uses transaction TXN-20241106-F3G8 which has:
# - Delivery Status: "Delivery Failed"
# - Notes: "Address not found - attempting redelivery"
# - This is a clear case for refund since package was never delivered

API_KEY="your_api_key_here"
BASE_URL="http://localhost:8000"

echo "=========================================="
echo "Testing APPROVED Refund - Delivery Failed"
echo "=========================================="
echo ""
echo "Transaction: TXN-20241106-F3G8"
echo "Customer: Frank Garcia"
echo "Issue: Package delivery failed (address not found)"
echo "Expected: APPROVE_REFUND + Automatic payment"
echo ""
echo "Submitting dispute analysis..."
echo ""

curl -X POST "$BASE_URL/dispute/analyze" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "dispute_description": "I never received my order. The tracking shows delivery failed because the address could not be found, but my address is correct and I have received packages here before. I would like a full refund.",
    "transaction_id": "TXN-20241106-F3G8",
    "amount": 45.00,
    "recipient_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
  }'

echo ""
echo ""
echo "=========================================="
echo "What Happens Behind The Scenes:"
echo "=========================================="
echo "1. ✓ Agent receives dispute claim"
echo "2. ✓ Shipment evidence auto-loaded from data/shipment_evidence.json"
echo "3. ✓ Evidence shows: delivery_status = 'Delivery Failed'"
echo "4. ✓ Agent determines this is legitimate (NOT fraud)"
echo "5. ✓ Agent returns: APPROVE_REFUND with high confidence (>70%)"
echo "6. ✓ Conditions checked:"
echo "   - Decision = APPROVE_REFUND ✓"
echo "   - Max turns not exceeded (step < 3) ✓"
echo "   - Amount provided: \$45.00 ✓"
echo "   - Recipient address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb ✓"
echo "   - Transaction ID: TXN-20241106-F3G8 ✓"
echo "7. ✓ Automatic payment triggered!"
echo "8. ✓ Locus send_to_address called:"
echo "   POST https://mcp.paywithlocus.com/mcp"
echo "   {\"
echo "     \"method\": \"tools/call\","
echo "     \"params\": {"
echo "       \"name\": \"send_to_address\","
echo "       \"arguments\": {"
echo "         \"address\": \"0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb\","
echo "         \"amount\": 45.00,"
echo "         \"memo\": \"Refund for dispute - Transaction: TXN-20241106-F3G8\""
echo "       }"
echo "     }"
echo "   }"
echo "9. ✓ Payment confirmed and returned in response"
echo ""
echo "=========================================="
echo "Expected Response:"
echo "=========================================="
echo '{'
echo '  "status": "completed",'
echo '  "transaction_id": "TXN-20241106-F3G8",'
echo '  "decision": {'
echo '    "decision": "APPROVE_REFUND",'
echo '    "confidence": 0.95,'
echo '    "justification": "Delivery failed due to address issue. Customer claims address is correct and has received packages before. Shipment evidence confirms delivery failure. Legitimate refund request.",'
echo '    "evidence_reviewed": ["shipment_evidence", "dispute_description"]'
echo '  },'
echo '  "message": "Decision: APPROVE_REFUND - Refund sent successfully",'
echo '  "step": 1'
echo '}'
echo ""
echo "=========================================="
echo "Key Success Indicators:"
echo "=========================================="
echo "✓ status: 'completed' (not 'needs_evidence')"
echo "✓ decision: 'APPROVE_REFUND'"
echo "✓ message includes: 'Refund sent successfully'"
echo "✓ confidence: >0.7 (high confidence)"
echo "✓ step: 1 (resolved quickly, no additional evidence needed)"
echo ""
