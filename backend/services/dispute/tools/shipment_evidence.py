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
        logger.info(f"Looking up shipment evidence for order_id: {order_id}")
        
        for order in self.data.get("orders", []):
            if order.get("order_id") == order_id:
                logger.info(f"Found shipment evidence for order_id: {order_id}")
                return order
        
        logger.warning(f"No shipment evidence found for order_id: {order_id}")
        return None
    
    def get_evidence_by_transaction_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve shipment evidence by transaction ID.
        
        Args:
            transaction_id: The transaction ID to look up
            
        Returns:
            Dictionary containing shipment evidence or None if not found
        """
        logger.info(f"Looking up shipment evidence for transaction_id: {transaction_id}")
        
        for order in self.data.get("orders", []):
            if order.get("transaction_id") == transaction_id:
                logger.info(f"Found shipment evidence for transaction_id: {transaction_id}")
                return order
        
        logger.warning(f"No shipment evidence found for transaction_id: {transaction_id}")
        return None
    
    def get_evidence_by_tracking_number(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve shipment evidence by tracking number.
        
        Args:
            tracking_number: The tracking number to look up
            
        Returns:
            Dictionary containing shipment evidence or None if not found
        """
        logger.info(f"Looking up shipment evidence for tracking_number: {tracking_number}")
        
        for order in self.data.get("orders", []):
            shipment = order.get("shipment", {})
            if shipment.get("tracking_number") == tracking_number:
                logger.info(f"Found shipment evidence for tracking_number: {tracking_number}")
                return order
        
        logger.warning(f"No shipment evidence found for tracking_number: {tracking_number}")
        return None
    
    def get_evidence_by_customer_id(self, customer_id: str) -> list[Dict[str, Any]]:
        """
        Retrieve all shipment evidence for a specific customer.
        
        Args:
            customer_id: The customer ID to look up
            
        Returns:
            List of orders for the customer
        """
        logger.info(f"Looking up shipment evidence for customer_id: {customer_id}")
        
        orders = [
            order for order in self.data.get("orders", [])
            if order.get("customer_id") == customer_id
        ]
        
        logger.info(f"Found {len(orders)} orders for customer_id: {customer_id}")
        return orders
    
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
        
        shipment = evidence.get("shipment", {})
        delivery_conf = shipment.get("delivery_confirmation", {})
        address = shipment.get("shipping_address", {})
        return_info = shipment.get("return_logistics")
        
        summary = f"""
📦 Shipment Evidence Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Order Information:
  • Order ID: {evidence.get('order_id', 'N/A')}
  • Transaction ID: {evidence.get('transaction_id', 'N/A')}
  • Customer: {evidence.get('customer_name', 'N/A')} ({evidence.get('customer_id', 'N/A')})
  • Amount: ${evidence.get('amount', 0):.2f}

Shipping Details:
  • Carrier: {shipment.get('carrier_name', 'N/A')}
  • Tracking Number: {shipment.get('tracking_number', 'N/A')}
  • Tracking ID: {shipment.get('tracking_id', 'N/A')}
  • Shipping Date: {shipment.get('shipping_date', 'N/A')}
  • Delivery Date: {shipment.get('delivery_date', 'Not yet delivered')}

Shipping Address:
  • {address.get('street', 'N/A')}
  • {address.get('city', 'N/A')}, {address.get('state', 'N/A')} {address.get('zip_code', 'N/A')}
  • {address.get('country', 'N/A')}

Delivery Confirmation:
  • Delivered: {'Yes' if shipment.get('delivery_date') else 'No'}
  • Signature: {'Yes - ' + delivery_conf.get('signature_name', '') if delivery_conf.get('signature_present') else 'No'}
  • Delivery Photo: {'Available' if delivery_conf.get('delivery_photo_url') else 'Not available'}
  • Left At: {delivery_conf.get('left_at', 'N/A')}
  • Delivery Timestamp: {shipment.get('delivery_timestamp', 'N/A')}

Supporting Documents:
  • Shipping Label: {shipment.get('shipping_label_url', 'N/A')}
  • Delivery Photo: {delivery_conf.get('delivery_photo_url', 'N/A')}
"""
        
        if return_info:
            summary += f"""
Return Logistics:
  • Status: {return_info.get('status', 'N/A')}
  • Current Location: {return_info.get('current_location', 'N/A')}
  • Expected Delivery: {return_info.get('expected_delivery', 'N/A')}
"""
        
        summary += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
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
        logger.info(f"Checking delivery status for identifier: {identifier}")
        
        # Try each lookup method
        evidence = (
            self.get_evidence_by_order_id(identifier) or
            self.get_evidence_by_transaction_id(identifier) or
            self.get_evidence_by_tracking_number(identifier)
        )
        
        if not evidence:
            logger.warning(f"No evidence found for identifier: {identifier}")
            return {
                "found": False,
                "identifier": identifier,
                "message": "No shipment evidence found for this identifier.",
                "summary": None
            }
        
        shipment = evidence.get("shipment", {})
        delivered = bool(shipment.get("delivery_date"))
        
        result = {
            "found": True,
            "identifier": identifier,
            "order_id": evidence.get("order_id"),
            "transaction_id": evidence.get("transaction_id"),
            "delivered": delivered,
            "tracking_number": shipment.get("tracking_number"),
            "carrier": shipment.get("carrier_name"),
            "delivery_date": shipment.get("delivery_date"),
            "has_signature": shipment.get("delivery_confirmation", {}).get("signature_present", False),
            "has_photo": bool(shipment.get("delivery_confirmation", {}).get("delivery_photo_url")),
            "summary": self.format_evidence_summary(evidence),
            "full_evidence": evidence
        }
        
        logger.info(f"Successfully retrieved evidence for identifier: {identifier}")
        return result


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

