# Multi-Turn Dispute Resolution - Testing Guide

## Overview

The new dispute resolution system supports a conversational flow where:
- The AI agent analyzes disputes in up to 3 steps
- Agent can request additional evidence at any step
- You provide evidence and the agent continues analysis
- Agent makes a FINAL DECISION (APPROVE_REFUND or DENY_REFUND) with justification

## Endpoint

```
POST /dispute/analyze
```

## How It Works

### Step 1: Initial Request
Send the dispute description without a session_id.

### Step 2-3: Follow-up (If Needed)
If agent requests evidence:
- Response will include `status: "needs_evidence"`
- Response includes `session_id` and `evidence_requested`
- Send follow-up request WITH the session_id and additional_evidence

### Final: Decision
Agent responds with:
- `status: "completed"`
- `decision`: APPROVE_REFUND or DENY_REFUND
- `confidence`: 0-1
- `justification`: Detailed reasoning

## Available Evidence Types

### 1. Shipment Evidence (Automatic)
Agent can check this directly using transaction ID:
- Tracking information
- Delivery confirmation
- Signatures and photos

### 2. User Prompt Evidence (Request-based)
Original user authorization:
```json
{
  "type": "user_prompt",
  "data": {
    "original_prompt": "Buy me wireless headphones under $100",
    "authorized_budget": 100.00,
    "product_type": "headphones",
    "merchant": "any",
    "authorization_timestamp": "2024-11-15T10:30:00Z"
  }
}
```

### 3. Agent Decision Evidence (Request-based)
AI agent's decision log:
```json
{
  "type": "agent_decision",
  "data": {
    "selection_rationale": "Selected based on best reviews and price match",
    "product_name": "Sony WH-1000XM5",
    "final_price": 298.00,
    "authorized_budget": 100.00,
    "budget_variance": 198.00,
    "approval_required": true,
    "user_approved": false
  }
}
```

---

## Test Scenarios

### Scenario 1: Simple Case - Delivery Confirmed (1 Step)

**Initial Request:**
```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "Customer claims they never received their order",
    "transaction_id": "TXN-20241101-A7B3",
    "amount": 249.99
  }'
```

**Expected Response:**
```json
{
  "status": "completed",
  "session_id": null,
  "transaction_id": "TXN-20241101-A7B3",
  "decision": {
    "decision": "DENY_REFUND",
    "confidence": 0.95,
    "justification": "Shipment evidence shows item was delivered on 2024-11-04 with signature confirmation from S. Johnson...",
    "evidence_reviewed": ["dispute_description", "shipment_evidence"]
  },
  "message": "Decision: DENY_REFUND",
  "step": 1
}
```

---

### Scenario 2: Needs User Authorization (2 Steps)

**Step 1 - Initial Request:**
```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "Customer disputes a $1299 laptop purchase. Claims they never authorized spending that much.",
    "transaction_id": "TXN-20241102-B8C4",
    "amount": 1299.00
  }'
```

**Expected Response:**
```json
{
  "status": "needs_evidence",
  "session_id": "abc123-session-id",
  "transaction_id": "TXN-20241102-B8C4",
  "evidence_requested": {
    "evidence_type": "user_prompt",
    "reason": "Need to verify user's original authorization and intent",
    "fields": ["original_prompt", "authorized_budget", "product_specifications", "user_authorization"]
  },
  "message": "Additional evidence required: user_prompt. Please provide this evidence in your next request using the session_id.",
  "step": 1
}
```

**Step 2 - Provide Evidence:**
```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "Providing requested user prompt evidence",
    "transaction_id": "TXN-20241102-B8C4",
    "session_id": "abc123-session-id",
    "additional_evidence": {
      "type": "user_prompt",
      "data": {
        "original_prompt": "Buy me a laptop for work, budget is $1500",
        "authorized_budget": 1500.00,
        "product_type": "laptop",
        "product_specifications": "work laptop, good performance",
        "user_authorization": "confirmed",
        "authorization_timestamp": "2024-11-02T09:00:00Z"
      }
    }
  }'
```

**Expected Response:**
```json
{
  "status": "completed",
  "session_id": null,
  "transaction_id": "TXN-20241102-B8C4",
  "decision": {
    "decision": "DENY_REFUND",
    "confidence": 0.9,
    "justification": "User authorized up to $1500 for a work laptop. Purchase of $1299 was within budget. Item was delivered with signature. No grounds for refund.",
    "evidence_reviewed": ["dispute_description", "shipment_evidence", "user_prompt"]
  },
  "message": "Decision: DENY_REFUND",
  "step": 2
}
```

---

### Scenario 3: Agent Exceeded Budget (3 Steps)

**Step 1 - Initial:**
```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "AI agent purchased item that cost more than I authorized",
    "transaction_id": "TXN-TEST-001",
    "amount": 500.00
  }'
```

**Step 2 - Agent Requests User Prompt:**
Response will request `user_prompt` evidence. Provide it:

```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "User authorization evidence",
    "transaction_id": "TXN-TEST-001",
    "session_id": "SESSION_ID_FROM_STEP1",
    "additional_evidence": {
      "type": "user_prompt",
      "data": {
        "original_prompt": "Buy me headphones, max budget $100",
        "authorized_budget": 100.00,
        "product_type": "headphones",
        "merchant": "any"
      }
    }
  }'
```

**Step 3 - Agent Requests Agent Decision:**
Response will request `agent_decision` evidence. Provide it:

```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "Agent decision evidence",
    "transaction_id": "TXN-TEST-001",
    "session_id": "SESSION_ID_FROM_STEP2",
    "additional_evidence": {
      "type": "agent_decision",
      "data": {
        "selection_rationale": "Found premium headphones with excellent reviews",
        "product_name": "Bose QuietComfort Ultra",
        "final_price": 500.00,
        "authorized_budget": 100.00,
        "budget_variance": 400.00,
        "approval_required": true,
        "user_approved": false,
        "agent_id": "AGENT-AI-001"
      }
    }
  }'
```

**Expected Final Response:**
```json
{
  "status": "completed",
  "session_id": null,
  "transaction_id": "TXN-TEST-001",
  "decision": {
    "decision": "APPROVE_REFUND",
    "confidence": 0.95,
    "justification": "Agent exceeded authorized budget by $400 (500% over limit). User authorized max $100, agent purchased $500 item without approval. This is a clear violation of authorization boundaries. Full refund approved.",
    "evidence_reviewed": ["dispute_description", "user_prompt", "agent_decision"]
  },
  "message": "Decision: APPROVE_REFUND",
  "step": 3
}
```

---

## Testing Script

Save as `test_multi_turn.sh`:

```bash
#!/bin/bash

echo "🧪 Multi-Turn Dispute Resolution Tests"
echo "======================================"
echo ""

# Test 1: Simple case (1 step)
echo "Test 1: Simple delivery dispute (expects 1 step)"
echo "------------------------------------------------"
RESPONSE1=$(curl -s -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "Customer claims non-delivery",
    "transaction_id": "TXN-20241101-A7B3",
    "amount": 249.99
  }')

echo "$RESPONSE1" | python3 -m json.tool
STATUS1=$(echo "$RESPONSE1" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
echo "Status: $STATUS1"
echo ""

# Test 2: Multi-step case
echo "Test 2: Budget dispute requiring evidence (expects 2-3 steps)"
echo "------------------------------------------------------------"
RESPONSE2=$(curl -s -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "Agent purchased item that exceeded my $100 budget",
    "transaction_id": "TXN-TEST-MULTI",
    "amount": 500.00
  }')

echo "$RESPONSE2" | python3 -m json.tool
SESSION_ID=$(echo "$RESPONSE2" | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', 'null'))")
EVIDENCE_TYPE=$(echo "$RESPONSE2" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('evidence_requested', {}).get('evidence_type', 'none'))" 2>/dev/null || echo "none")

if [ "$SESSION_ID" != "null" ] && [ "$EVIDENCE_TYPE" != "none" ]; then
    echo ""
    echo "Agent requested evidence: $EVIDENCE_TYPE"
    echo "Session ID: $SESSION_ID"
    echo ""
    echo "Providing $EVIDENCE_TYPE evidence..."
    
    if [ "$EVIDENCE_TYPE" == "user_prompt" ]; then
        RESPONSE3=$(curl -s -X POST http://localhost:8000/dispute/analyze \
          -H "Content-Type: application/json" \
          -d "{
            \"dispute_description\": \"Providing user prompt evidence\",
            \"transaction_id\": \"TXN-TEST-MULTI\",
            \"session_id\": \"$SESSION_ID\",
            \"additional_evidence\": {
              \"type\": \"user_prompt\",
              \"data\": {
                \"original_prompt\": \"Buy headphones under \\$100\",
                \"authorized_budget\": 100.00,
                \"product_type\": \"headphones\"
              }
            }
          }")
        
        echo "$RESPONSE3" | python3 -m json.tool
    fi
fi

echo ""
echo "✅ Tests completed"
```

Make executable:
```bash
chmod +x test_multi_turn.sh
```

---

## Key Points

1. **Session Management**: Session IDs are automatically generated and must be included in follow-up requests

2. **3-Step Limit**: Agent MUST make a decision within 3 steps. If not, system applies default DENY_REFUND

3. **Evidence Format**: Always wrap evidence in `additional_evidence` with `type` and `data` fields

4. **Decision Format**: Final decisions always include decision type, confidence level, and detailed justification

5. **Session Cleanup**: Sessions expire after 30 minutes of inactivity or upon completion

---

## Troubleshooting

**Session Not Found:**
- Session may have expired (30 min timeout)
- Check that you're using the correct session_id from previous response

**Max Steps Reached:**
- Agent took too long to decide
- Default decision applied
- Start new session to retry

**Invalid Evidence Format:**
- Ensure `additional_evidence` has both `type` and `data` fields
- Check that evidence type matches what agent requested

---

## Production Integration

When integrating with real systems:

1. Replace test data in `data/shipment_evidence.json` with real API calls
2. Implement actual user prompt/agent decision logging
3. Add authentication and rate limiting
4. Store conversation histories in database
5. Add webhook notifications for decisions
6. Implement appeals process for disputed decisions

