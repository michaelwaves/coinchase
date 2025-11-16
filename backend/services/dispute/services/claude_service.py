"""
Service layer for Claude Agent SDK interactions.
"""

from typing import Any, Optional, List, Dict
import os
from anthropic import Anthropic
from utils.prompt_loader import PromptLoader
import logging

logger = logging.getLogger(__name__)


class ClaudeService:
    """Service for interacting with Claude API."""

    def __init__(self):
        """Initialize Claude service."""
        self.prompt_loader = PromptLoader()

        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

        self.client = Anthropic(api_key=api_key)
        logger.info("Claude service initialized")

    def _build_message_content(
        self, text: str, images: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Build message content with text and optional images.

        Args:
            text: Text content
            images: Optional list of images with 'data' (base64) and 'mediaType' fields

        Returns:
            List of content blocks for Claude API
        """
        content = []

        # Add images first if provided
        if images:
            for image in images:
                content.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image["mediaType"],
                            "data": image["data"],
                        },
                    }
                )
            logger.info(f"Added {len(images)} image(s) to message content")

        # Add text content
        content.append({"type": "text", "text": text})

        return content

    async def analyze_dispute(
        self,
        dispute_description: str,
        transaction_id: str = None,
        amount: float = None,
        conversation_history: list[dict] = None,
        images: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Analyze a dispute using Claude Agent SDK.

        Args:
            dispute_description: Description of the dispute
            transaction_id: Optional transaction ID
            amount: Optional disputed amount
            conversation_history: Optional conversation history for multi-turn
            images: Optional list of images with 'data' (base64) and 'mediaType' fields

        Returns:
            str: Claude's analysis of the dispute
        """
        try:
            logger.info(f"Starting dispute analysis (transaction: {transaction_id})")

            # Load and format prompt from file
            user_prompt = self.prompt_loader.format_prompt(
                "dispute_analysis",
                dispute_description=dispute_description,
                transaction_id=transaction_id,
                amount=amount,
            )

            # Get system prompt
            system_prompt = self.prompt_loader.get_system_prompt("dispute_analysis")

            # Build messages from history or single message
            if conversation_history:
                messages = conversation_history
            else:
                # Build content with text and optional images
                content = self._build_message_content(user_prompt, images)
                messages = [{"role": "user", "content": content}]

            # Call Claude API directly
            message = self.client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
            )

            # Extract text response
            result = ""
            for block in message.content:
                if block.type == "text":
                    result += block.text

            logger.info(f"Dispute analysis completed (transaction: {transaction_id})")
            return result if result else "No analysis generated."

        except Exception as e:
            logger.error(f"Error in analyze_dispute: {str(e)}", exc_info=True)
            raise
