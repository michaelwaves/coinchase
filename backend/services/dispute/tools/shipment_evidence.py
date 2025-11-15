"""
Tool for retrieving shipment and delivery evidence for dispute resolution.
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class ShipmentEvidenceTool:
    """
    Tool for accessing shipment and delivery evidence to support dispute resolution.
    
    This tool provides access to proof of shipment and delivery information including:
    - Tracking numbers and carrier information
    - Delivery confirmations and timestamps
    - Shipping labels and addresses
    - Delivery signatures and photos
    - Return logistics status
    """
    
    def __init__(self, data_file: Optional[str] = None):
        """
        Initialize the shipment evidence tool.
        
        Args:
            data_file: Path to the JSON file containing shipment data.
                      If None, uses the default data file.
        """
        if data_file is None:
            # Default to the data file in the same directory structure
            current_dir = Path(__file__).parent.parent
            data_file = current_dir / "data" / "shipment_evidence.json"
        
        self.data_file = Path(data_file)
        self._load_data()
        logger.info(f"ShipmentEvidenceTool initialized with data file: {self.data_file}")
    
    def _load_data(self) -> None:
        """Load shipment evidence data from JSON file."""
        try:
            with open(self.data_file, 'r') as f:
                self.data = json.load(f)
            logger.info(f"Loaded {len(self.data.get('orders', []))} orders from evidence database")
        except FileNotFoundError:
            logger.error(f"Data file not found: {self.data_file}")
            self.data = {"orders": []}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON data: {e}")
            self.data = {"orders": []}
    
    def get_evidence_by_order_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve shipment evidence by order ID.
        
        Args:
            order_id: The order ID to look up
            
        Returns:
            Dictionary containing shipment evidence or None if not found
        """
        for order in self.data.get("orders", []):
            if order.get("order_id") == order_id:
                return order
        return None
    
    def get_evidence_by_transaction_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve shipment evidence by transaction ID.
        
        Args:
            transaction_id: The transaction ID to look up
            
        Returns:
            Dictionary containing shipment evidence or None if not found
        """
        for order in self.data.get("orders", []):
            if order.get("transaction_id") == transaction_id:
                return order
        return None
    
    def get_evidence_by_tracking_number(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve shipment evidence by tracking number.
        
        Args:
            tracking_number: The tracking number to look up
            
        Returns:
            Dictionary containing shipment evidence or None if not found
        """
        for order in self.data.get("orders", []):
            shipment = order.get("shipment", {})
            if shipment.get("tracking_number") == tracking_number:
                return order
        return None
    
    def get_evidence_by_customer_id(self, customer_id: str) -> list[Dict[str, Any]]:
        """
        Retrieve all shipment evidence for a specific customer.
        
        Args:
            customer_id: The customer ID to look up
            
        Returns:
            List of orders for the customer
        """
        return [
            order for order in self.data.get("orders", [])
            if order.get("customer_id") == customer_id
        ]
    
    def format_evidence_summary(self, evidence: Dict[str, Any]) -> str:
        """
        Format shipment evidence into a human-readable summary.
        
        Args:
            evidence: The evidence dictionary to format
            
        Returns:
            Formatted string summary of the evidence
        """
        if not evidence:
            return "No evidence available."
        
        summary = f"""
📦 Shipment Evidence Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Order Information:
  • Order ID: {evidence.get('order_id', 'N/A')}
  • Transaction ID: {evidence.get('transaction_id', 'N/A')}
  • Customer: {evidence.get('customer_name', 'N/A')}

Shipping Details:
  • Carrier: {evidence.get('carrier', 'N/A')}
  • Tracking Number: {evidence.get('tracking_number', 'N/A')}
  • Shipping Date: {evidence.get('shipping_date', 'N/A')}
  • Delivery Date: {evidence.get('delivery_date', 'Not yet delivered')}
  • Status: {evidence.get('delivery_status', 'Unknown')}

Shipping Address:
  • {evidence.get('shipping_address', 'N/A')}

Delivery Confirmation:
  • Delivered: {'✅ Yes' if evidence.get('delivery_date') else '❌ No'}
  • Signature: {evidence.get('signature', 'No signature')}
  • Delivery Photo: {'✅ Available' if evidence.get('delivery_photo_url') else '❌ Not available'}
  • Notes: {evidence.get('notes', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return summary
    
    def check_delivery_status(self, identifier: str) -> Dict[str, Any]:
        """
        Check delivery status for any identifier (order ID, transaction ID, or tracking number).
        
        This is the main method that should be called by the Claude agent.
        
        Args:
            identifier: Order ID, Transaction ID, or Tracking Number
            
        Returns:
            Dictionary with delivery status and evidence
        """
        # Try each lookup method
        evidence = (
            self.get_evidence_by_order_id(identifier) or
            self.get_evidence_by_transaction_id(identifier) or
            self.get_evidence_by_tracking_number(identifier)
        )
        
        if not evidence:
            return {
                "found": False,
                "identifier": identifier,
                "message": "No shipment evidence found for this identifier.",
                "summary": None
            }
        
        delivered = bool(evidence.get("delivery_date"))
        
        return {
            "found": True,
            "identifier": identifier,
            "order_id": evidence.get("order_id"),
            "transaction_id": evidence.get("transaction_id"),
            "delivered": delivered,
            "tracking_number": evidence.get("tracking_number"),
            "carrier": evidence.get("carrier"),
            "delivery_date": evidence.get("delivery_date"),
            "has_signature": bool(evidence.get("signature")),
            "has_photo": bool(evidence.get("delivery_photo_url")),
            "summary": self.format_evidence_summary(evidence),
            "full_evidence": evidence
        }


# Singleton instance for easy access
_tool_instance = None


def get_shipment_evidence_tool() -> ShipmentEvidenceTool:
    """Get or create the singleton ShipmentEvidenceTool instance."""
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = ShipmentEvidenceTool()
    return _tool_instance


# Claude Agent SDK tool interface
def check_shipment_evidence(identifier: str) -> str:
    """
    Check shipment and delivery evidence for dispute resolution.
    
    This function is designed to be called by Claude Agent SDK as a custom tool.
    
    Args:
        identifier: Order ID, Transaction ID, or Tracking Number
        
    Returns:
        Formatted string with shipment evidence details
    """
    tool = get_shipment_evidence_tool()
    result = tool.check_delivery_status(identifier)
    
    if result["found"]:
        return result["summary"]
    else:
        return f"❌ {result['message']}\n\nPlease verify the identifier and try again."

