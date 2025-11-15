#!/bin/bash
# Test curl commands for Dispute Analysis with Shipment Evidence Tool

echo "🧪 Testing Dispute Analysis API with Shipment Evidence Tool"
echo "============================================================"
echo ""

# Test 1: Item Not Received (Evidence exists - delivered with signature)
echo "📦 Test 1: Customer claims non-delivery (Transaction: TXN-20241101-A7B3)"
echo "Expected: Agent finds evidence of successful delivery with signature"
echo ""
curl -X POST http://localhost:8000/claude/analyze-dispute \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "Customer claims they never received their order. They are requesting a full refund of $249.99. Customer says there was no delivery attempt and no package was left at their address.",
    "transaction_id": "TXN-20241101-A7B3",
    "amount": 249.99
  }' | python3 -m json.tool

echo ""
echo "============================================================"
echo ""

# Test 2: In-Transit Order
echo "📦 Test 2: Customer dispute for in-transit order (Transaction: TXN-20241107-G4H9)"
echo "Expected: Agent finds evidence showing item is still in transit"
echo ""
curl -X POST http://localhost:8000/claude/analyze-dispute \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "Customer filed a dispute saying the item has not arrived after 2 weeks. They want to know where their package is.",
    "transaction_id": "TXN-20241107-G4H9",
    "amount": 349.99
  }' | python3 -m json.tool

echo ""
echo "============================================================"
echo ""

# Test 3: High-value item with signature
echo "📦 Test 3: High-value laptop delivery dispute (Transaction: TXN-20241102-B8C4)"
echo "Expected: Agent finds delivery confirmation with signature"
echo ""
curl -X POST http://localhost:8000/claude/analyze-dispute \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "Customer disputes receiving a $1299 laptop. Claims signature on delivery confirmation is not theirs.",
    "transaction_id": "TXN-20241102-B8C4",
    "amount": 1299.00
  }' | python3 -m json.tool

echo ""
echo "============================================================"
echo ""

# Test 4: Invalid transaction ID
echo "📦 Test 4: Non-existent transaction ID"
echo "Expected: Agent attempts to find evidence but returns not found"
echo ""
curl -X POST http://localhost:8000/claude/analyze-dispute \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "Customer claims non-delivery.",
    "transaction_id": "INVALID-TXN-999",
    "amount": 99.99
  }' | python3 -m json.tool

echo ""
echo "============================================================"
echo "✅ All tests completed"

