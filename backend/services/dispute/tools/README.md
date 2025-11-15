# Dispute Resolution Tools

This directory contains custom tools for Claude Agent SDK to assist with dispute resolution.

## Shipment Evidence Tool

### Overview

The Shipment Evidence Tool provides access to proof of shipment and delivery information for physical goods purchases. This tool is essential for defending against "Item Not Received" or "Goods Not Delivered" disputes.

### Features

- **Multiple Lookup Methods**: Search by Order ID, Transaction ID, or Tracking Number
- **Comprehensive Evidence**: Includes tracking info, delivery confirmation, signatures, photos, and addresses
- **Logging**: All tool usage is automatically logged for audit trails
- **Claude Agent Integration**: Fully integrated with Claude Agent SDK as a custom MCP tool

### Evidence Categories

| Category | Information Provided |
|----------|---------------------|
| **Order Information** | Order ID, Transaction ID, Customer details, Amount |
| **Shipping Details** | Carrier, Tracking numbers, Shipping/Delivery dates |
| **Delivery Address** | Full shipping address with validation |
| **Delivery Confirmation** | Signature status, Delivery photos, Drop-off location, Timestamp |
| **Supporting Documents** | Shipping label URLs, Delivery photo URLs |
| **Return Logistics** | Return status, Current location, Expected delivery (when applicable) |

### Usage

#### Direct Python Usage

```python
from tools.shipment_evidence import get_shipment_evidence_tool

# Get the tool instance
tool = get_shipment_evidence_tool()

# Check evidence by order ID
result = tool.check_delivery_status("ORD-2024-001")
if result["found"]:
    print(result["summary"])
    
# Or by transaction ID
result = tool.check_delivery_status("TXN-20241101-A7B3")

# Or by tracking number
result = tool.check_delivery_status("794612345678")
```

#### Claude Agent SDK Usage

The tool is automatically registered with Claude Agent SDK and can be invoked by Claude during dispute analysis:

```python
from services.claude_service import ClaudeService

service = ClaudeService()
analysis = await service.analyze_dispute(
    dispute_description="Customer claims item not received",
    transaction_id="TXN-20241101-A7B3"
)
```

Claude will automatically use the `check_shipment_evidence` tool when it needs to verify delivery information.

### Tool Interface

**Tool Name**: `check_shipment_evidence`

**Description**: Check shipment and delivery evidence for dispute resolution. Provides tracking information, delivery confirmation, signatures, and photos.

**Parameters**:
- `identifier` (str): Order ID, Transaction ID, or Tracking Number

**Returns**: Formatted summary of shipment evidence including all relevant details

### Test Data

The tool includes 10 sample orders with diverse scenarios:

1. **ORD-2024-001**: Standard delivery with signature (FedEx)
2. **ORD-2024-002**: High-value item with signature (UPS)
3. **ORD-2024-003**: No-signature delivery (USPS)
4. **ORD-2024-004**: Business/reception delivery (DHL)
5. **ORD-2024-005**: Left at alternative location (FedEx)
6. **ORD-2024-006**: High-value with required signature (UPS)
7. **ORD-2024-007**: In-transit order with return logistics (USPS)
8. **ORD-2024-008**: Signature by building security (FedEx)
9. **ORD-2024-009**: Side door delivery (DHL)
10. **ORD-2024-010**: Standard successful delivery (UPS)

### Testing

Run the comprehensive test suite:

```bash
cd backend/services/dispute
python3 test_shipment_tool.py
```

The test suite covers:
- Lookup by Order ID
- Lookup by Transaction ID
- Lookup by Tracking Number
- Lookup by Customer ID
- Main delivery status check
- In-transit orders
- Claude Agent SDK interface

### Logging

All tool operations are logged with the following information:
- Tool initialization
- Lookup requests with identifiers
- Successful evidence retrieval
- Failed lookups (warnings)

Log format:
```
2025-11-15 12:37:53,789 - tools.shipment_evidence - INFO - Looking up shipment evidence for order_id: ORD-2024-001
2025-11-15 12:37:53,789 - tools.shipment_evidence - INFO - Found shipment evidence for order_id: ORD-2024-001
```

### Data Structure

Evidence data is stored in `data/shipment_evidence.json` with the following structure:

```json
{
  "orders": [
    {
      "order_id": "ORD-2024-001",
      "customer_id": "CUST-78291",
      "customer_name": "Sarah Johnson",
      "transaction_id": "TXN-20241101-A7B3",
      "amount": 249.99,
      "shipment": {
        "carrier_name": "FedEx",
        "tracking_number": "794612345678",
        "tracking_id": "FDX794612345678",
        "shipping_label_url": "...",
        "shipping_date": "2024-11-01T14:30:00Z",
        "delivery_date": "2024-11-04T16:45:00Z",
        "delivery_timestamp": "2024-11-04T16:45:23Z",
        "shipping_address": { ... },
        "delivery_confirmation": { ... },
        "return_logistics": null
      }
    }
  ]
}
```

### Adding New Evidence

To add new shipment evidence, edit `data/shipment_evidence.json` and add new order objects following the existing structure. The tool will automatically load the updated data on next initialization.

### Integration with Dispute Analysis

The tool is automatically available to Claude during dispute analysis. Claude can invoke it when:
- A customer claims non-delivery
- Verification of delivery status is needed
- Shipment tracking information is required
- Evidence collection for dispute resolution

Example Claude usage scenario:
```
User: "Analyze dispute for transaction TXN-20241101-A7B3 - customer claims item not received"
Claude: *uses check_shipment_evidence tool*
Claude: "Based on the shipment evidence, I can see that:
- The item was delivered on 2024-11-04 at 16:45:23
- Signature was obtained from S. Johnson
- Delivery photo is available at [URL]
- Item was left at the front door
This evidence strongly supports that the item was delivered successfully."
```

### API Endpoint Integration

The tool is integrated with the `/claude/analyze-dispute` endpoint and will be automatically available when the Claude service is initialized.

### Future Enhancements

Potential improvements:
- Real-time carrier API integration
- Automated evidence collection from shipping providers
- Image analysis of delivery photos
- Geolocation verification
- Customer signature verification

