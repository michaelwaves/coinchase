# Dispute Analysis Examples - Approved vs Denied

This document shows examples of transactions that will be **APPROVED** vs **DENIED** based on the shipment evidence data.

## ✅ APPROVED Refund Example

### Transaction: TXN-20241106-F3G8
**Customer:** Frank Garcia
**Shipment Status:** Delivery Failed
**Evidence:** Address not found - attempting redelivery

**Dispute Claim:**
```json
{
  "dispute_description": "I never received my order. The tracking shows delivery failed because the address could not be found, but my address is correct and I have received packages here before. I would like a full refund.",
  "transaction_id": "TXN-20241106-F3G8",
  "amount": 45.00,
  "recipient_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}
```

**Why Approved:**
- ✓ Shipment evidence confirms delivery failure
- ✓ Customer's claim matches the evidence
- ✓ No indication of fraud
- ✓ Legitimate reason for refund

**Expected Decision:**
```json
{
  "decision": "APPROVE_REFUND",
  "confidence": 0.95,
  "justification": "Delivery failed due to address issue..."
}
```

**Automatic Action:**
- ✅ **Refund of $45.00 automatically sent to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb**
- ✅ Memo: "Refund for dispute - Transaction: TXN-20241106-F3G8"

---

## ❌ DENIED Refund Example

### Transaction: TXN-20241101-A7B3
**Customer:** Alice Johnson
**Shipment Status:** Delivered
**Evidence:**
- Delivered on 2024-11-03
- Signature: A. Johnson
- Delivery photo available
- Left at front door per customer instructions

**Dispute Claim:**
```json
{
  "dispute_description": "I never received my order and want a refund.",
  "transaction_id": "TXN-20241101-A7B3",
  "amount": 75.00,
  "recipient_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}
```

**Why Denied:**
- ❌ Shipment evidence shows successful delivery
- ❌ Customer's signature on file (A. Johnson)
- ❌ Delivery photo exists
- ❌ Package left per customer's own instructions
- ❌ Claim contradicts evidence = potential fraud

**Expected Decision:**
```json
{
  "decision": "DENY_REFUND",
  "confidence": 0.90,
  "justification": "Package was successfully delivered with signature confirmation and photo evidence. Customer signed for package (A. Johnson). Claim of non-receipt contradicts shipment evidence."
}
```

**Automatic Action:**
- ❌ **No refund sent** (refund only triggers on APPROVE_REFUND)

---

## 🤔 NEEDS EVIDENCE Example

### Transaction: TXN-20241104-D1E6
**Customer:** David Chen
**Shipment Status:** Delivered
**Evidence:**
- Delivered on 2024-11-06
- Signature: "Neighbor (apt 5A)"
- Delivered to neighbor with permission

**Dispute Claim:**
```json
{
  "dispute_description": "My neighbor says they never received my package even though tracking says delivered to them.",
  "transaction_id": "TXN-20241104-D1E6",
  "amount": 60.00,
  "recipient_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}
```

**Why More Evidence Needed:**
- ⚠️ Package was delivered to neighbor
- ⚠️ Unclear if neighbor actually lost package or is lying
- ⚠️ Need to verify neighbor communication
- ⚠️ Confidence < 70%

**Expected Response:**
```json
{
  "status": "needs_evidence",
  "evidence_requested": {
    "evidence_type": "neighbor_communication",
    "reason": "Need to verify interaction with neighbor who received package",
    "fields": ["neighbor_name", "communication_date", "neighbor_statement"]
  }
}
```

**Automatic Action:**
- ⏸️ **Refund on hold** - waiting for additional evidence
- Session ID provided to continue conversation

---

## Summary of Refund Triggers

| Condition | Requirement |
|-----------|-------------|
| **Decision** | Must be `APPROVE_REFUND` |
| **Confidence** | Agent feels confident (typically >70%) |
| **Max Turns** | `session.step < 3` (not exceeded) |
| **Amount** | Must be provided in request |
| **Recipient Address** | Must be valid wallet address (0x...) |
| **Transaction ID** | Must be provided in request |

**All conditions must be met** for automatic refund to process.

---

## Testing Different Scenarios

### Scenario 1: Quick Approval (1 turn)
- Clear evidence supporting customer
- High confidence decision
- ✅ Refund sent immediately

### Scenario 2: Approval After Evidence (2-3 turns)
- Initial uncertainty
- Customer provides additional evidence
- Confidence increases to >70%
- ✅ Refund sent after evidence review

### Scenario 3: Denial Without Refund
- Evidence contradicts customer claim
- High confidence in fraud detection
- ❌ No refund sent

### Scenario 4: Max Turns Exceeded
- Too much uncertainty even after evidence
- Reaches 3 turns without high confidence
- ❌ Default DENY_REFUND (fraud prevention)
- ❌ No refund sent

---

## Available Test Transactions

From `data/shipment_evidence.json`:

**Likely APPROVED:**
- TXN-20241106-F3G8 (Delivery Failed)
- TXN-20241103-C9D5 (In Transit, delayed)
- TXN-20241110-J7K3 (In Transit, delayed)

**Likely DENIED:**
- TXN-20241101-A7B3 (Delivered with signature)
- TXN-20241102-B8C4 (Delivered with signature)
- TXN-20241105-E2F7 (Delivered with signature)
- TXN-20241107-G4H9 (Delivered with signature)
- TXN-20241108-H5I1 (Delivered with signature)
- TXN-20241109-I6J2 (Delivered with signature)

**Uncertain (may need evidence):**
- TXN-20241104-D1E6 (Delivered to neighbor)
