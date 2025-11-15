"""
Service layer for Claude Agent SDK interactions.
"""
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock
from utils.prompt_loader import PromptLoader


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
        # Load and format prompt from file
        prompt = self.prompt_loader.format_prompt(
            "dispute_analysis",
            dispute_description=dispute_description,
            transaction_id=transaction_id,
            amount=amount
        )
        
        # Get system prompt
        system_prompt = self.prompt_loader.get_system_prompt("dispute_analysis")
        
        # Configure Claude options
        options = ClaudeAgentOptions(
            max_turns=self.max_turns,
            allowed_tools=[],
            system_prompt=system_prompt
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

