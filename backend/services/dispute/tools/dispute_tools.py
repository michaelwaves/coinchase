"""
Custom tools for Claude Agent SDK to handle dispute-related operations.
"""
from claude_agent_sdk import tool, create_sdk_mcp_server


@tool(
    name="analyze_dispute_pattern",
    description="Analyze a dispute to identify common patterns and recommend actions",
    input_schema={
        "type": "object",
        "properties": {
            "dispute_text": {
                "type": "string",
                "description": "The dispute description text"
            },
            "amount": {
                "type": "number",
                "description": "The disputed amount"
            }
        },
        "required": ["dispute_text"]
    }
)
async def analyze_dispute_pattern(args: dict) -> dict:
    """
    Analyze dispute patterns and provide recommendations.
    
    Args:
        args: Dictionary containing dispute_text and optional amount
        
    Returns:
        dict: Analysis results with recommendations
    """
    dispute_text = args.get("dispute_text", "")
    amount = args.get("amount", 0)
    
    # Simplified pattern analysis
    patterns = {
        "fraud": ["fraud", "unauthorized", "didn't authorize", "stolen"],
        "quality": ["defective", "broken", "damaged", "poor quality"],
        "delivery": ["not received", "late", "missing", "lost"],
        "refund": ["refund", "return", "money back"]
    }
    
    detected_patterns = []
    text_lower = dispute_text.lower()
    
    for pattern_type, keywords in patterns.items():
        if any(keyword in text_lower for keyword in keywords):
            detected_patterns.append(pattern_type)
    
    # Generate recommendations based on patterns
    recommendations = []
    if "fraud" in detected_patterns:
        recommendations.append("High priority: Potential fraud case. Verify transaction details immediately.")
    if "quality" in detected_patterns:
        recommendations.append("Request product evidence and review merchant policies.")
    if "delivery" in detected_patterns:
        recommendations.append("Check shipping records and tracking information.")
    if "refund" in detected_patterns:
        recommendations.append("Review refund policy compliance.")
    
    if not recommendations:
        recommendations.append("Standard review process: No specific patterns detected.")
    
    return {
        "content": [
            {
                "type": "text",
                "text": f"""
Dispute Analysis Results:
- Amount: ${amount if amount else 'Not specified'}
- Detected Patterns: {', '.join(detected_patterns) if detected_patterns else 'None'}

Recommendations:
{chr(10).join(f'  • {rec}' for rec in recommendations)}

Risk Level: {'High' if 'fraud' in detected_patterns else 'Medium' if detected_patterns else 'Low'}
"""
            }
        ]
    }


@tool(
    name="calculate_dispute_risk",
    description="Calculate risk score for a dispute based on various factors",
    input_schema={
        "type": "object",
        "properties": {
            "amount": {
                "type": "number",
                "description": "Disputed amount"
            },
            "customer_history": {
                "type": "string",
                "description": "Customer history: new, regular, vip"
            }
        },
        "required": ["amount"]
    }
)
async def calculate_dispute_risk(args: dict) -> dict:
    """
    Calculate risk score for a dispute.
    
    Args:
        args: Dictionary containing amount and optional customer_history
        
    Returns:
        dict: Risk score and details
    """
    amount = args.get("amount", 0)
    customer_history = args.get("customer_history", "new").lower()
    
    # Simple risk calculation
    risk_score = 0
    
    # Amount-based risk
    if amount > 1000:
        risk_score += 30
    elif amount > 500:
        risk_score += 20
    elif amount > 100:
        risk_score += 10
    else:
        risk_score += 5
    
    # Customer history risk
    history_scores = {
        "new": 25,
        "regular": 10,
        "vip": 5
    }
    risk_score += history_scores.get(customer_history, 15)
    
    risk_level = "Low"
    if risk_score > 40:
        risk_level = "High"
    elif risk_score > 25:
        risk_level = "Medium"
    
    return {
        "content": [
            {
                "type": "text",
                "text": f"""
Risk Assessment:
- Risk Score: {risk_score}/100
- Risk Level: {risk_level}
- Amount Risk: ${amount}
- Customer Type: {customer_history}

Recommendation: {'Immediate review required' if risk_level == 'High' else 'Standard processing' if risk_level == 'Medium' else 'Low priority'}
"""
            }
        ]
    }


def create_dispute_tools_server():
    """
    Create an SDK MCP server with dispute-related tools.
    
    Returns:
        SDK MCP Server instance
    """
    return create_sdk_mcp_server(
        name="dispute-tools",
        version="1.0.0",
        tools=[analyze_dispute_pattern, calculate_dispute_risk]
    )

