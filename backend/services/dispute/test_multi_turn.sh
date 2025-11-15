#!/bin/bash

# Multi-Turn Dispute Resolution - Quick Test Script

BASE_URL="http://localhost:8000"

echo "🧪 Multi-Turn Dispute Resolution Testing"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Simple single-step resolution
echo -e "${YELLOW}Test 1: Simple Dispute - Item Not Received${NC}"
echo "Expected: Agent checks shipment evidence and denies refund (1 step)"
echo ""

RESPONSE1=$(curl -s -X POST $BASE_URL/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "Customer claims they never received their order. Demanding full refund.",
    "transaction_id": "TXN-20241101-A7B3",
    "amount": 249.99
  }')

echo "Response:"
echo "$RESPONSE1" | python3 -m json.tool

STATUS=$(echo "$RESPONSE1" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))" 2>/dev/null)
STEP=$(echo "$RESPONSE1" | python3 -c "import sys, json; print(json.load(sys.stdin).get('step', 0))" 2>/dev/null)

if [ "$STATUS" == "completed" ]; then
    DECISION=$(echo "$RESPONSE1" | python3 -c "import sys, json; print(json.load(sys.stdin).get('decision', {}).get('decision', 'unknown'))" 2>/dev/null)
    echo ""
    echo -e "${GREEN}✅ Test 1 Passed: Decision made in $STEP step(s) - $DECISION${NC}"
else
    echo ""
    echo -e "${RED}❌ Test 1 Issue: Status is $STATUS (expected 'completed')${NC}"
fi

echo ""
echo "================================================"
echo ""

# Test 2: Multi-step with evidence request
echo -e "${YELLOW}Test 2: Budget Override Dispute - Requires Evidence${NC}"
echo "Expected: Agent requests user prompt evidence, then decides (2-3 steps)"
echo ""

echo "Step 1: Initial request"
RESPONSE2=$(curl -s -X POST $BASE_URL/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "The AI agent purchased an item that cost WAY more than I authorized. I said $100 max but it bought something for $500!",
    "transaction_id": "TXN-BUDGET-TEST",
    "amount": 500.00
  }')

echo "$RESPONSE2" | python3 -m json.tool

SESSION_ID=$(echo "$RESPONSE2" | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', ''))" 2>/dev/null)
STATUS2=$(echo "$RESPONSE2" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))" 2>/dev/null)
EVIDENCE_TYPE=$(echo "$RESPONSE2" | python3 -c "import sys, json; print(json.load(sys.stdin).get('evidence_requested', {}).get('evidence_type', ''))" 2>/dev/null)

echo ""
if [ "$STATUS2" == "needs_evidence" ] && [ ! -z "$SESSION_ID" ]; then
    echo -e "${GREEN}✅ Agent requested evidence: $EVIDENCE_TYPE${NC}"
    echo "Session ID: $SESSION_ID"
    echo ""
    echo "Step 2: Providing $EVIDENCE_TYPE evidence"
    
    # Provide the requested evidence
    if [ "$EVIDENCE_TYPE" == "user_prompt" ]; then
        RESPONSE3=$(curl -s -X POST $BASE_URL/dispute/analyze \
          -H "Content-Type: application/json" \
          -d "{
            \"dispute_description\": \"Here is the user prompt evidence\",
            \"transaction_id\": \"TXN-BUDGET-TEST\",
            \"session_id\": \"$SESSION_ID\",
            \"additional_evidence\": {
              \"type\": \"user_prompt\",
              \"data\": {
                \"original_prompt\": \"Buy me wireless headphones, maximum budget is $100\",
                \"authorized_budget\": 100.00,
                \"product_type\": \"headphones\",
                \"merchant\": \"any\",
                \"authorization_timestamp\": \"2024-11-15T10:00:00Z\"
              }
            }
          }")
    elif [ "$EVIDENCE_TYPE" == "agent_decision" ]; then
        RESPONSE3=$(curl -s -X POST $BASE_URL/dispute/analyze \
          -H "Content-Type: application/json" \
          -d "{
            \"dispute_description\": \"Here is the agent decision evidence\",
            \"transaction_id\": \"TXN-BUDGET-TEST\",
            \"session_id\": \"$SESSION_ID\",
            \"additional_evidence\": {
              \"type\": \"agent_decision\",
              \"data\": {
                \"selection_rationale\": \"Found premium headphones with best reviews\",
                \"product_name\": \"Bose QuietComfort Ultra\",
                \"final_price\": 500.00,
                \"authorized_budget\": 100.00,
                \"budget_variance\": 400.00,
                \"approval_required\": true,
                \"user_approved\": false
              }
            }
          }")
    fi
    
    echo ""
    echo "$RESPONSE3" | python3 -m json.tool
    
    STATUS3=$(echo "$RESPONSE3" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))" 2>/dev/null)
    
    if [ "$STATUS3" == "completed" ]; then
        DECISION3=$(echo "$RESPONSE3" | python3 -c "import sys, json; print(json.load(sys.stdin).get('decision', {}).get('decision', 'unknown'))" 2>/dev/null)
        STEP3=$(echo "$RESPONSE3" | python3 -c "import sys, json; print(json.load(sys.stdin).get('step', 0))" 2>/dev/null)
        echo ""
        echo -e "${GREEN}✅ Test 2 Passed: Decision made in $STEP3 step(s) - $DECISION3${NC}"
    elif [ "$STATUS3" == "needs_evidence" ]; then
        # Need another round
        SESSION_ID2=$(echo "$RESPONSE3" | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', ''))" 2>/dev/null)
        EVIDENCE_TYPE2=$(echo "$RESPONSE3" | python3 -c "import sys, json; print(json.load(sys.stdin).get('evidence_requested', {}).get('evidence_type', ''))" 2>/dev/null)
        
        echo ""
        echo -e "${YELLOW}Agent needs more evidence: $EVIDENCE_TYPE2${NC}"
        echo "Session continues: $SESSION_ID2"
        echo ""
        echo "Step 3: Providing $EVIDENCE_TYPE2 evidence"
        
        if [ "$EVIDENCE_TYPE2" == "agent_decision" ]; then
            RESPONSE4=$(curl -s -X POST $BASE_URL/dispute/analyze \
              -H "Content-Type: application/json" \
              -d "{
                \"dispute_description\": \"Agent decision evidence\",
                \"transaction_id\": \"TXN-BUDGET-TEST\",
                \"session_id\": \"$SESSION_ID2\",
                \"additional_evidence\": {
                  \"type\": \"agent_decision\",
                  \"data\": {
                    \"selection_rationale\": \"Premium headphones selected\",
                    \"product_name\": \"Bose QuietComfort Ultra\",
                    \"final_price\": 500.00,
                    \"authorized_budget\": 100.00,
                    \"budget_variance\": 400.00,
                    \"approval_required\": true,
                    \"user_approved\": false
                  }
                }
              }")
        fi
        
        echo ""
        echo "$RESPONSE4" | python3 -m json.tool
        
        STATUS4=$(echo "$RESPONSE4" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))" 2>/dev/null)
        if [ "$STATUS4" == "completed" ]; then
            DECISION4=$(echo "$RESPONSE4" | python3 -c "import sys, json; print(json.load(sys.stdin).get('decision', {}).get('decision', 'unknown'))" 2>/dev/null)
            STEP4=$(echo "$RESPONSE4" | python3 -c "import sys, json; print(json.load(sys.stdin).get('step', 0))" 2>/dev/null)
            echo ""
            echo -e "${GREEN}✅ Test 2 Passed: Decision made in $STEP4 step(s) - $DECISION4${NC}"
        fi
    else
        echo ""
        echo -e "${RED}❌ Test 2 Issue: Status is $STATUS3${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Agent made immediate decision (no evidence needed)${NC}"
    if [ "$STATUS2" == "completed" ]; then
        DECISION2=$(echo "$RESPONSE2" | python3 -c "import sys, json; print(json.load(sys.stdin).get('decision', {}).get('decision', 'unknown'))" 2>/dev/null)
        echo "Decision: $DECISION2"
    fi
fi

echo ""
echo "================================================"
echo ""
echo -e "${GREEN}✅ All tests completed!${NC}"
echo ""
echo "📚 See MULTI_TURN_TESTING.md for detailed documentation"

