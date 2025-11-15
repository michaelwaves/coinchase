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
        logger.info("="*60)
        logger.info("🔧 TOOL CALLED: check_shipment_evidence")
        logger.info(f"Arguments received: {args}")
        
        identifier = args.get("identifier", "")
        logger.info(f"Extracted identifier: '{identifier}'")
        
        if not identifier:
            logger.warning("No identifier provided in arguments")
            return {
                "content": [
                    {"type": "text", "text": "❌ No identifier provided. Please provide an order ID, transaction ID, or tracking number."}
                ],
                "is_error": False
            }
        
        logger.info(f"Calling get_shipment_evidence_tool()")
        tool = get_shipment_evidence_tool()
        logger.info(f"Tool instance obtained: {type(tool).__name__}")
        
        logger.info(f"Checking delivery status for: {identifier}")
        result = tool.check_delivery_status(identifier)
        logger.info(f"Tool result - Found: {result.get('found', False)}")
        
        if result["found"]:
            logger.info(f"✅ Evidence found for: {identifier}")
            logger.info(f"Order ID: {result.get('order_id')}")
            logger.info(f"Delivered: {result.get('delivered')}")
            logger.info(f"Has signature: {result.get('has_signature')}")
            logger.info(f"Has photo: {result.get('has_photo')}")
            
            response = {
                "content": [
                    {"type": "text", "text": result["summary"]}
                ]
            }
            logger.info(f"Returning success response with {len(result['summary'])} characters")
            logger.info("="*60)
            return response
        else:
            logger.warning(f"❌ No evidence found for: {identifier}")
            response = {
                "content": [
                    {"type": "text", "text": f"❌ {result['message']}\n\nPlease verify the identifier and try again."}
                ],
                "is_error": False  # Not a critical error, just not found
            }
            logger.info("Returning not-found response")
            logger.info("="*60)
            return response
            
    except Exception as e:
        logger.error("="*60)
        logger.error("❌ ERROR in check_shipment_evidence_tool")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception message: {str(e)}")
        logger.error("Full traceback:", exc_info=True)
        logger.error("="*60)
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
            logger.info("="*80)
            logger.info("Starting dispute analysis")
            logger.info(f"Transaction ID: {transaction_id}")
            logger.info(f"Amount: {amount}")
            logger.info(f"Description: {dispute_description[:100]}...")
            
            # Load and format prompt from file
            logger.info("Loading and formatting prompt")
            prompt = self.prompt_loader.format_prompt(
                "dispute_analysis",
                dispute_description=dispute_description,
                transaction_id=transaction_id,
                amount=amount
            )
            logger.info(f"Formatted prompt length: {len(prompt)} characters")
            
            # Get system prompt
            logger.info("Loading system prompt")
            system_prompt = self.prompt_loader.get_system_prompt("dispute_analysis")
            logger.info(f"System prompt: {system_prompt[:200]}...")
            
            # Configure Claude options with custom MCP tools
            logger.info("Configuring Claude options")
            logger.info(f"Max turns: {self.max_turns}")
            logger.info(f"Allowed tools: ['mcp__dispute-tools__check_shipment_evidence']")
            logger.info(f"MCP server configured: dispute-tools")
            
            options = ClaudeAgentOptions(
                max_turns=self.max_turns,
                allowed_tools=["mcp__dispute-tools__check_shipment_evidence"],
                mcp_servers={"dispute-tools": self.mcp_server},
                system_prompt=system_prompt
            )
            logger.info("Claude options configured successfully")
            
            # Query Claude using ClaudeSDKClient for better control
            full_response = []
            logger.info("Creating Claude SDK client")
            
            # Ensure API key is set
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
            
            logger.info("Starting Claude query with SDK client")
            message_count = 0
            
            async with ClaudeSDKClient(options=options) as client:
                logger.info("Client initialized, sending query")
                await client.query(prompt)
                
                logger.info("Receiving responses")
                async for message in client.receive_response():
                    message_count += 1
                    logger.info(f"Received message #{message_count}: {type(message).__name__}")
                    
                    if isinstance(message, AssistantMessage):
                        logger.info(f"Processing AssistantMessage with {len(message.content)} content blocks")
                        for idx, block in enumerate(message.content):
                            logger.info(f"  Block #{idx + 1}: {type(block).__name__}")
                            if isinstance(block, TextBlock):
                                text_preview = block.text[:100] if len(block.text) > 100 else block.text
                                logger.info(f"    Text preview: {text_preview}...")
                                full_response.append(block.text)
                            else:
                                logger.info(f"    Block content: {str(block)[:200]}")
                    else:
                        logger.info(f"Non-AssistantMessage: {type(message)}")
                        logger.info(f"Message content: {str(message)[:500]}")
            
            logger.info(f"Query completed. Received {message_count} messages")
            logger.info(f"Collected {len(full_response)} text blocks")
            
            result = "\n".join(full_response) if full_response else "No analysis generated."
            logger.info(f"Final response length: {len(result)} characters")
            logger.info("Dispute analysis completed successfully")
            logger.info("="*80)
            
            return result
            
        except Exception as e:
            logger.error("="*80)
            logger.error("ERROR in analyze_dispute")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception message: {str(e)}")
            logger.error("Full traceback:", exc_info=True)
            logger.error("="*80)
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
            logger.info(f"Simple query request (use_tools={use_tools})")
            
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
            
            result = "\n".join(full_response) if full_response else "No response generated."
            logger.info(f"Simple query completed ({len(result)} chars)")
            return result
            
        except Exception as e:
            logger.error(f"Error in simple_query: {e}", exc_info=True)
            raise

