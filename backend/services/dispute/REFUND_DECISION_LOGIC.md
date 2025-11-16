# Automatic Refund Decision Logic

## Overview

The dispute system now automatically processes refunds when the AI agent approves a dispute with high confidence. The system is flexible and supports **both structured and natural language decision formats**.

## Refund Trigger Conditions

A refund will be automatically processed when **ALL** of the following conditions are met:

### 1. Decision is Approval ✅
The agent's response contains approval indicators in **any** of these forms:

**Structured Format:**
```
DECISION: APPROVE_REFUND | CONFIDENCE: 0.95 | JUSTIFICATION: ...
```

**Natural Language Format:**
The response contains any of these keywords (case-insensitive):
- `APPROVED`
- `REFUND AUTHORIZED`
- `AUTHORIZE REFUND`
- `APPROVE REFUND`

### 2. High Confidence ✅
- **Minimum confidence:** 70% (0.70)
- Detected from patterns like:
  - `Certainty Level: 95%`
  - `Confidence: 0.95`
  - `CONFIDENCE: 95%`

### 3. Under Max Turns ✅
- `session.step < 3` (not exceeded)
- Prevents refunds on uncertain cases that required too many evidence rounds

### 4. Required Fields Present ✅
All of these must be provided in the request:
- `amount` - The refund amount
- `recipient_address` - Wallet address (0x...)
- `transaction_id` - Transaction identifier

---

## Example: Natural Language Approval

### Request:
```json
{
  "dispute_description": "I didn't receive the package, it's already 2024-11-14",
  "transaction_id": "TXN-20241103-C9D5",
  "amount": 0.001,
  "recipient_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}
```

### Agent Response:
```markdown
# DISPUTE RESOLUTION DECISION - UPDATED

**Case ID:** TXN-20241103-C9D5
**Claimant:** Carol White
**Dispute Amount:** $0.001

---

## ANALYSIS

**Timeline:**
- Order shipped: 2024-11-03
- Expected delivery: 2024-11-07
- Current date (claim date): 2024-11-14
- **Days overdue: 7 days**

**Tracking Status:**
- Carrier: USPS
- Tracking #: 9405511899223197428490
- Current Status: **In Transit**
- Delivery Confirmation: ❌ None

---

## DECISION

**✅ DISPUTE APPROVED - REFUND AUTHORIZED**

**Certainty Level:** 95%

**Rationale:**
1. Package is **11 days overdue** from expected delivery date
2. USPS tracking shows **no delivery event** has occurred
3. No delivery confirmation, signature, or photo proof exists
4. Customer's claim is **fully supported** by carrier tracking data
5. Package appears **lost in USPS transit**

**Resolution:**
- **Refund Status:** ✅ **APPROVED**
- **Refund Amount:** $0.001
- **Reason:** Non-delivery - Lost in transit
```

### What Happens:

1. ✅ **Keywords Detected:** "APPROVED", "REFUND AUTHORIZED" found in response
2. ✅ **Confidence Extracted:** 95% (from "Certainty Level: 95%")
3. ✅ **Conditions Met:**
   - Approval: ✅ (multiple approval keywords found)
   - Confidence: ✅ (95% > 70% threshold)
   - Max turns: ✅ (step 2 < 3)
   - Amount: ✅ ($0.001)
   - Address: ✅ (0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb)
   - Transaction ID: ✅ (TXN-20241103-C9D5)

4. 🚀 **Automatic Refund Triggered:**
   ```bash
   POST https://mcp.paywithlocus.com/mcp
   {
     "method": "tools/call",
     "params": {
       "name": "send_to_address",
       "arguments": {
         "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
         "amount": 0.001,
         "memo": "Refund for dispute - Transaction: TXN-20241103-C9D5"
       }
     }
   }
   ```

5. ✅ **Response Updated:**
   ```json
   {
     "status": "analyzing",
     "session_id": "97b8229a-ed92-4c8e-a088-9fdc63c93fd4",
     "message": "[Original message...]\n\n✅ Refund of $0.001 automatically processed to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
   }
   ```

---

## How It Works: Code Flow

### Step 1: Parse Agent Response (`parse_agent_response`)

```python
# Checks for approval keywords
approval_keywords = ["APPROVED", "REFUND AUTHORIZED", "AUTHORIZE REFUND", "APPROVE REFUND"]
is_approval = any(keyword in response_upper for keyword in approval_keywords)

# Extracts confidence
confidence_match = re.search(r"(?:CERTAINTY|CONFIDENCE).*?(\d+)%", response_text, re.IGNORECASE)
confidence = float(confidence_match.group(1)) / 100

# Returns completed status if approval/denial detected
if is_approval or is_denial:
    return ("completed", {
        "decision": "APPROVE_REFUND" if is_approval else "DENY_REFUND",
        "confidence": confidence,
        "justification": response_text[:500]
    })
```

### Step 2: Process Refund (`_build_completed_response` or analyzing branch)

**Option A: Completed Status**
```python
async def _build_completed_response(...):
    should_process_refund = (
        data["decision"] == "APPROVE_REFUND" and
        session.step < 3 and
        request.amount and
        request.recipient_address and
        request.transaction_id
    )

    if should_process_refund:
        payment_result = await send_refund_to_address(...)
```

**Option B: Analyzing Status with High-Confidence Approval**
```python
else:  # analyzing
    has_approval = any(keyword in message_upper for keyword in ["APPROVED", "REFUND AUTHORIZED", ...])
    confidence = extract_confidence_from_message(...)

    if has_approval and confidence >= 0.70 and [all other conditions]:
        payment_result = await send_refund_to_address(...)
```

---

## Decision Matrix

| Agent Response | Keywords Found | Confidence | Status | Refund Triggered? |
|----------------|----------------|------------|--------|-------------------|
| "✅ APPROVED" + "95%" | ✅ APPROVED | 95% | completed | ✅ YES |
| "REFUND AUTHORIZED" + "80%" | ✅ REFUND AUTHORIZED | 80% | completed | ✅ YES |
| "Approved" + "65%" | ✅ APPROVED | 65% | completed | ❌ NO (low confidence) |
| "DENIED" + "90%" | ❌ DENIED | 90% | completed | ❌ NO (denial) |
| "Still reviewing..." | ❌ None | N/A | analyzing | ❌ NO |
| "APPROVED" + "95%" (step 4) | ✅ APPROVED | 95% | completed | ❌ NO (max turns) |
| "APPROVED" + "95%" (no address) | ✅ APPROVED | 95% | completed | ❌ NO (missing data) |

---

## Testing

### Test with Natural Language Response:
```bash
curl -X POST http://localhost:8000/dispute/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "dispute_description": "Package never arrived, tracking shows lost in transit",
    "transaction_id": "TXN-20241103-C9D5",
    "amount": 45.00,
    "recipient_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
  }'
```

### Expected Behavior:
- Agent analyzes case
- Detects keywords: "APPROVED", "AUTHORIZED", etc.
- Extracts confidence from "Certainty: X%" or "Confidence: X%"
- If confidence ≥ 70%, automatically triggers refund
- Response includes: "✅ Refund of $X automatically processed to 0x..."

---

## Supported Decision Formats

### ✅ Format 1: Structured (Original)
```
DECISION: APPROVE_REFUND | CONFIDENCE: 0.95 | JUSTIFICATION: Package lost in transit
```

### ✅ Format 2: Natural Language
```
✅ DISPUTE APPROVED - REFUND AUTHORIZED
Certainty Level: 95%
```

### ✅ Format 3: Simple
```
Refund approved for this case.
Confidence: 85%
```

### ✅ Format 4: Mixed
```
After reviewing the evidence, I approve the refund request.
My confidence in this decision is 92%.
```

All formats will trigger automatic refund as long as:
- Approval keywords are present
- Confidence ≥ 70%
- All required fields provided
- Under max turns (step < 3)

---

## Configuration

### Confidence Threshold
Change in `dispute_conversation.py:370`:
```python
if has_approval and confidence >= 0.70:  # Change 0.70 to desired threshold
```

### Max Turns
Change in `dispute_conversation.py:370`:
```python
if has_approval and confidence >= 0.70 and session.step < 3:  # Change 3 to desired max
```

### Approval Keywords
Add/modify in `dispute_conversation.py:91-92`:
```python
approval_keywords = ["APPROVED", "REFUND AUTHORIZED", "AUTHORIZE REFUND", "APPROVE REFUND", "YOUR_CUSTOM_KEYWORD"]
```
