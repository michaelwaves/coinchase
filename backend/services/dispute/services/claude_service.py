"""
Service layer for Claude Agent SDK interactions.
"""
from typing import Any
import os
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    tool,
    create_sdk_mcp_server,
    ClaudeSDKClient
)
from utils.prompt_loader import PromptLoader
from tools.shipment_evidence import get_shipment_evidence_tool
import logging

logger = logging.getLogger(__name__)


# Define the shipment evidence tool for Claude Agent SDK
@tool(
    "check_shipment_evidence",
    "Check shipment and delivery evidence for dispute resolution. Provides tracking information, delivery confirmation, signatures, and photos.",
    {"identifier": str}
)
async def check_shipment_evidence_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Tool wrapper for shipment evidence lookup.
    
    Args:
        args: Dictionary with 'identifier' key (order ID, transaction ID, or tracking number)
        
    Returns:
        Tool response with shipment evidence
    """
    try:
        identifier = args.get("identifier", "")
        logger.info(f"🔧 Tool called: check_shipment_evidence (identifier: {identifier})")
        
        if not identifier:
            return {
                "content": [
                    {"type": "text", "text": "❌ No identifier provided. Please provide an order ID, transaction ID, or tracking number."}
                ],
                "is_error": False
            }
        
        tool = get_shipment_evidence_tool()
        result = tool.check_delivery_status(identifier)
        
        if result["found"]:
            logger.info(f"✅ Evidence found: {result.get('order_id')} (delivered: {result.get('delivered')})")
            return {
                "content": [
                    {"type": "text", "text": result["summary"]}
                ]
            }
        else:
            logger.info(f"❌ No evidence found for: {identifier}")
            return {
                "content": [
                    {"type": "text", "text": f"❌ {result['message']}\n\nPlease verify the identifier and try again."}
                ],
                "is_error": False
            }
            
    except Exception as e:
        logger.error(f"Error in check_shipment_evidence_tool: {str(e)}")
        return {
            "content": [
                {"type": "text", "text": f"❌ Error checking shipment evidence: {str(e)}"}
            ],
            "is_error": True
        }


class ClaudeService:
    """Service for interacting with Claude Agent SDK."""
    
    def __init__(self, max_turns: int = 5, allowed_tools: list[str] = None):
        """
        Initialize Claude service.
        
        Args:
            max_turns: Maximum conversation turns
            allowed_tools: List of allowed tools
        """
        self.max_turns = max_turns
        self.allowed_tools = allowed_tools or ["Read"]
        self.prompt_loader = PromptLoader()
        
        # Create MCP server with custom tools
        self.mcp_server = create_sdk_mcp_server(
            name="dispute-tools",
            version="1.0.0",
            tools=[check_shipment_evidence_tool]
        )
        logger.info("Claude service initialized with shipment evidence tool")
        
    async def analyze_dispute(
        self,
        dispute_description: str,
        transaction_id: str = None,
        amount: float = None
    ) -> str:
        """
        Analyze a dispute using Claude Agent SDK.
        
        Args:
            dispute_description: Description of the dispute
            transaction_id: Optional transaction ID
            amount: Optional disputed amount
            
        Returns:
            str: Claude's analysis of the dispute
        """
        try:
            logger.info(f"Starting dispute analysis (transaction: {transaction_id})")
            
            # Load and format prompt from file
            prompt = self.prompt_loader.format_prompt(
                "dispute_analysis",
                dispute_description=dispute_description,
                transaction_id=transaction_id,
                amount=amount
            )
            
            # Get system prompt
            system_prompt = self.prompt_loader.get_system_prompt("dispute_analysis")
            
            # Configure Claude options with custom MCP tools
            options = ClaudeAgentOptions(
                max_turns=self.max_turns,
                allowed_tools=["mcp__dispute-tools__check_shipment_evidence"],
                mcp_servers={"dispute-tools": self.mcp_server},
                system_prompt=system_prompt
            )
            
            # Ensure API key is set
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
            
            # Query Claude using ClaudeSDKClient
            full_response = []
            
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)
                
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                full_response.append(block.text)
            
            result = "\n".join(full_response) if full_response else "No analysis generated."
            logger.info(f"Dispute analysis completed (transaction: {transaction_id})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in analyze_dispute: {str(e)}", exc_info=True)
            raise
    
    async def simple_query(self, prompt: str, use_tools: bool = False) -> str:
        """
        Send a simple query to Claude.
        
        Args:
            prompt: The prompt to send
            use_tools: Whether to enable custom tools
            
        Returns:
            str: Claude's response
        """
        try:
            if use_tools:
                options = ClaudeAgentOptions(
                    max_turns=self.max_turns,
                    allowed_tools=["mcp__dispute-tools__check_shipment_evidence"],
                    mcp_servers={"dispute-tools": self.mcp_server}
                )
            else:
                options = ClaudeAgentOptions(
                    max_turns=1,
                    allowed_tools=[]
                )
            
            full_response = []
            
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)
                
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                full_response.append(block.text)
            
            return "\n".join(full_response) if full_response else "No response generated."
            
        except Exception as e:
            logger.error(f"Error in simple_query: {e}")
            raise

