"""
Test script for the Shipment Evidence Tool.
"""
import logging
from tools.shipment_evidence import get_shipment_evidence_tool, check_shipment_evidence

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_lookup_by_order_id():
    """Test looking up evidence by order ID."""
    print("\n" + "="*80)
    print("TEST 1: Lookup by Order ID")
    print("="*80)
    
    tool = get_shipment_evidence_tool()
    evidence = tool.get_evidence_by_order_id("ORD-2024-001")
    
    if evidence:
        print(tool.format_evidence_summary(evidence))
    else:
        print("❌ No evidence found")


def test_lookup_by_transaction_id():
    """Test looking up evidence by transaction ID."""
    print("\n" + "="*80)
    print("TEST 2: Lookup by Transaction ID")
    print("="*80)
    
    tool = get_shipment_evidence_tool()
    evidence = tool.get_evidence_by_transaction_id("TXN-20241102-B8C4")
    
    if evidence:
        print(tool.format_evidence_summary(evidence))
    else:
        print("❌ No evidence found")


def test_lookup_by_tracking_number():
    """Test looking up evidence by tracking number."""
    print("\n" + "="*80)
    print("TEST 3: Lookup by Tracking Number")
    print("="*80)
    
    tool = get_shipment_evidence_tool()
    evidence = tool.get_evidence_by_tracking_number("9400111899562842976089")
    
    if evidence:
        print(tool.format_evidence_summary(evidence))
    else:
        print("❌ No evidence found")


def test_lookup_by_customer_id():
    """Test looking up all orders for a customer."""
    print("\n" + "="*80)
    print("TEST 4: Lookup by Customer ID")
    print("="*80)
    
    tool = get_shipment_evidence_tool()
    orders = tool.get_evidence_by_customer_id("CUST-78291")
    
    print(f"Found {len(orders)} order(s) for customer CUST-78291")
    for order in orders:
        print(tool.format_evidence_summary(order))


def test_check_delivery_status():
    """Test the main check_delivery_status method."""
    print("\n" + "="*80)
    print("TEST 5: Check Delivery Status (Main Method)")
    print("="*80)
    
    tool = get_shipment_evidence_tool()
    
    # Test with various identifiers
    test_ids = [
        "ORD-2024-005",
        "TXN-20241106-F3G8",
        "1Z999AA10987654321",
        "INVALID-ID-12345"
    ]
    
    for test_id in test_ids:
        print(f"\n--- Testing with: {test_id} ---")
        result = tool.check_delivery_status(test_id)
        
        if result["found"]:
            print(f"✅ Found: {result['order_id']}")
            print(f"   Transaction: {result['transaction_id']}")
            print(f"   Delivered: {result['delivered']}")
            print(f"   Tracking: {result['tracking_number']}")
            print(f"   Carrier: {result['carrier']}")
            print(f"   Has Signature: {result['has_signature']}")
            print(f"   Has Photo: {result['has_photo']}")
        else:
            print(f"❌ Not found: {result['message']}")


def test_in_transit_order():
    """Test an order that is still in transit."""
    print("\n" + "="*80)
    print("TEST 6: In-Transit Order (Not Yet Delivered)")
    print("="*80)
    
    tool = get_shipment_evidence_tool()
    evidence = tool.get_evidence_by_order_id("ORD-2024-007")
    
    if evidence:
        print(tool.format_evidence_summary(evidence))
    else:
        print("❌ No evidence found")


def test_claude_agent_interface():
    """Test the Claude Agent SDK interface function."""
    print("\n" + "="*80)
    print("TEST 7: Claude Agent SDK Interface")
    print("="*80)
    
    # This is how Claude Agent would call the tool
    result = check_shipment_evidence("TXN-20241108-H5I1")
    print(result)
    
    print("\n--- Testing with invalid identifier ---")
    result = check_shipment_evidence("NONEXISTENT-123")
    print(result)


def run_all_tests():
    """Run all test cases."""
    print("\n" + "="*80)
    print("🧪 SHIPMENT EVIDENCE TOOL - TEST SUITE")
    print("="*80)
    
    try:
        test_lookup_by_order_id()
        test_lookup_by_transaction_id()
        test_lookup_by_tracking_number()
        test_lookup_by_customer_id()
        test_check_delivery_status()
        test_in_transit_order()
        test_claude_agent_interface()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        print(f"\n❌ TEST FAILED: {e}")


if __name__ == "__main__":
    run_all_tests()

