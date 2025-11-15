# Dispute Resolution API - Test Cases

This document provides example cURL commands to test the dispute resolution API with both legitimate and fraudulent claims.

---

## 🚨 FRAUD CASES (Should be DENIED)

### 1. Fraud: False "Item Not Received" Claim

**Scenario:** Customer claims item never arrived, but shipment evidence shows successful delivery with signature.

```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "I never received my order! The package never arrived at my address. I want a full refund immediately.",
    "transaction_id": "TXN-20241101-A7B3",
    "amount": 249.99
  }' | python3 -m json.tool
```

**Expected Result:**
- Status: `completed` (step 1)
- Decision: `DENY_REFUND`
- Confidence: ~90-95%
- Reason: Delivery confirmed with signature "A. Johnson" on 2024-11-03

---

### 2. Fraud: User Claims Unauthorized Purchase (But Actually Authorized)

**Scenario:** User claims they never authorized the purchase, but prompt logs show clear authorization.

**Step 1:** Initial claim
```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "I never told the AI agent to buy anything! This is unauthorized!",
    "transaction_id": "TXN-AUTH-FRAUD-001",
    "amount": 150.00
  }' | python3 -m json.tool
```

**Step 2:** Provide user prompt evidence (shows clear authorization)
```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_ID_FROM_STEP_1",
    "transaction_id": "TXN-AUTH-FRAUD-001",
    "dispute_description": "User authorization evidence",
    "additional_evidence": {
      "type": "user_prompt",
      "data": {
        "original_instruction": "Buy me noise canceling headphones, up to $150",
        "timestamp": "2024-11-15T10:00:00Z",
        "authorized_budget": 150.00,
        "user_confirmation": "Yes, proceed with purchase"
      }
    }
  }' | python3 -m json.tool
```

**Expected Result:**
- Decision: `DENY_REFUND`
- Confidence: ~95%
- Reason: User explicitly authorized the purchase with clear budget

---

### 3. Fraud: Claims Agent Exceeded Budget (But It Didn't)

**Scenario:** User claims agent spent over budget, but agent logs show it stayed within limits.

**Step 1:** Initial claim
```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "The AI agent spent way more than I authorized! I said $100 max but it spent $150!",
    "transaction_id": "TXN-BUDGET-FRAUD-001",
    "amount": 150.00
  }' | python3 -m json.tool
```

**Step 2:** Provide user prompt evidence
```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_ID_FROM_STEP_1",
    "transaction_id": "TXN-BUDGET-FRAUD-001",
    "dispute_description": "User prompt evidence",
    "additional_evidence": {
      "type": "user_prompt",
      "data": {
        "original_instruction": "Buy headphones, budget up to $200",
        "authorized_budget": 200.00,
        "timestamp": "2024-11-15T09:00:00Z"
      }
    }
  }' | python3 -m json.tool
```

**Step 3:** Provide agent decision evidence
```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_ID_FROM_STEP_2",
    "transaction_id": "TXN-BUDGET-FRAUD-001",
    "dispute_description": "Agent decision evidence",
    "additional_evidence": {
      "type": "agent_decision",
      "data": {
        "item_purchased": "Sony WH-1000XM5 Headphones",
        "actual_price": 150.00,
        "authorized_budget": 200.00,
        "budget_check": "PASS - Within budget",
        "user_approval": "Auto-approved within budget limits"
      }
    }
  }' | python3 -m json.tool
```

**Expected Result:**
- Decision: `DENY_REFUND`
- Confidence: ~95%
- Reason: Agent stayed within authorized $200 budget, purchased item for $150

---

## ✅ LEGITIMATE CASES (Should be APPROVED)

### 4. Legitimate: Item Actually Not Delivered

**Scenario:** Customer claims non-delivery, and shipment shows "Delivery Failed".

```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "I never received my package. Tracking shows delivery failed.",
    "transaction_id": "TXN-20241106-F3G8",
    "amount": 89.99
  }' | python3 -m json.tool
```

**Expected Result:**
- Status: `completed` (step 1)
- Decision: `APPROVE_REFUND`
- Confidence: ~90-95%
- Reason: Shipment shows "Delivery Failed" status, no delivery date

---

### 5. Legitimate: Agent Exceeded Budget Without Permission

**Scenario:** User set $100 budget, but agent purchased $500 item without asking.

**Step 1:** Initial claim
```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "AI agent bought something way over budget! I said max $100 but it purchased a $500 item without asking me!",
    "transaction_id": "TXN-BUDGET-001",
    "amount": 500.00
  }' | python3 -m json.tool
```

**Step 2:** Provide user prompt evidence (shows $100 limit)
```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_ID_FROM_STEP_1",
    "transaction_id": "TXN-BUDGET-001",
    "dispute_description": "User authorization evidence",
    "additional_evidence": {
      "type": "user_prompt",
      "data": {
        "original_instruction": "Buy wireless headphones, max budget $100",
        "timestamp": "2024-11-15T09:00:00Z",
        "authorized_budget": 100.00
      }
    }
  }' | python3 -m json.tool
```

**Expected Result:**
- Decision: `APPROVE_REFUND`
- Confidence: ~95%
- Reason: Agent violated explicit $100 budget limit by purchasing $500 item

---

### 6. Legitimate: Unauthorized Purchase by Agent

**Scenario:** User never authorized any purchase, agent made decision independently.

**Step 1:** Initial claim
```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "I never authorized this purchase! The AI agent bought something without my permission.",
    "transaction_id": "TXN-UNAUTH-001",
    "amount": 299.99
  }' | python3 -m json.tool
```

**Step 2:** Provide user prompt evidence (shows no authorization)
```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_ID_FROM_STEP_1",
    "transaction_id": "TXN-UNAUTH-001",
    "dispute_description": "User prompt evidence",
    "additional_evidence": {
      "type": "user_prompt",
      "data": {
        "original_instruction": "Show me some headphone options, DON'T buy anything yet",
        "authorized_to_purchase": false,
        "timestamp": "2024-11-15T10:30:00Z"
      }
    }
  }' | python3 -m json.tool
```

**Step 3:** Provide agent decision evidence (confirms unauthorized action)
```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_ID_FROM_STEP_2",
    "transaction_id": "TXN-UNAUTH-001",
    "dispute_description": "Agent decision evidence",
    "additional_evidence": {
      "type": "agent_decision",
      "data": {
        "item_purchased": "Bose QuietComfort Headphones",
        "actual_price": 299.99,
        "user_approval_requested": false,
        "agent_rationale": "User seemed interested, proceeded with purchase",
        "authorization_status": "None - agent made autonomous decision"
      }
    }
  }' | python3 -m json.tool
```

**Expected Result:**
- Decision: `APPROVE_REFUND`
- Confidence: ~95%
- Reason: User explicitly stated "DON'T buy", agent violated clear instruction

---

## Quick Test Script

Run all tests at once:

```bash
#!/bin/bash
echo "Testing Fraud Case 1: False non-delivery claim..."
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{"dispute_description": "I never received my order!", "transaction_id": "TXN-20241101-A7B3", "amount": 249.99}' \
  | python3 -m json.tool

echo -e "\n\nTesting Legitimate Case: Actual delivery failure..."
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -d '{"dispute_description": "Package never arrived", "transaction_id": "TXN-20241106-F3G8", "amount": 89.99}' \
  | python3 -m json.tool
```

---

## Expected Decision Summary

| Case | Type | Decision | Confidence | Reason |
|------|------|----------|-----------|--------|
| 1 | Fraud | DENY | 90-95% | Delivery confirmed |
| 2 | Fraud | DENY | 95% | User authorized purchase |
| 3 | Fraud | DENY | 95% | Agent within budget |
| 4 | Legit | APPROVE | 90-95% | Delivery failed |
| 5 | Legit | APPROVE | 95% | Budget exceeded 5x |
| 6 | Legit | APPROVE | 95% | No authorization given |

