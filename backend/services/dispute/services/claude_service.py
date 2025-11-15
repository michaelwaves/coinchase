"""
Service layer for Claude Agent SDK interactions.
"""
from typing import AsyncIterator
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock
from tools.dispute_tools import create_dispute_tools_server


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
        # Build comprehensive prompt with pattern analysis logic built-in
        prompt = f"""
You are a dispute analysis expert. Analyze the following dispute and provide:

1. **Summary of the Dispute**: Brief overview of what happened
2. **Pattern Detection**: Identify if this matches common patterns:
   - Fraud (unauthorized, stolen, didn't authorize)
   - Quality Issues (defective, broken, damaged)
   - Delivery Problems (not received, late, missing)
   - Refund Requests (money back, return)
3. **Risk Assessment**: Calculate risk level based on amount and patterns
   - Low Risk: < $100, no fraud indicators
   - Medium Risk: $100-$500, some concerns
   - High Risk: > $500, fraud indicators present
4. **Recommended Actions**: Specific steps to take
5. **Priority Level**: Immediate, High, Medium, or Low

Dispute Details:
- Description: {dispute_description}
"""
        if transaction_id:
            prompt += f"- Transaction ID: {transaction_id}\n"
        if amount:
            prompt += f"- Amount: ${amount}\n"
        
        prompt += """
Please provide a structured analysis covering all the points above.
"""
        
        # Configure Claude options (simplified - no custom MCP tools for now)
        options = ClaudeAgentOptions(
            max_turns=self.max_turns,
            allowed_tools=[],  # No tools needed - Claude will analyze based on prompt
            system_prompt="You are an expert dispute analyst with deep knowledge of payment disputes, fraud patterns, and customer service best practices."
        )
        
        # Query Claude and collect response
        full_response = []
        
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        full_response.append(block.text)
        
        return "\n".join(full_response) if full_response else "No analysis generated."
    
    async def simple_query(self, prompt: str) -> str:
        """
        Send a simple query to Claude without custom tools.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            str: Claude's response
        """
        options = ClaudeAgentOptions(
            max_turns=1,
            allowed_tools=[]
        )
        
        full_response = []
        
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        full_response.append(block.text)
        
        return "\n".join(full_response) if full_response else "No response generated."

