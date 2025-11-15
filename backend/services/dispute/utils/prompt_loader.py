"""
Utility for loading and managing prompts from text files.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PromptLoader:
    """Loads and manages prompts from the prompts directory."""
    
    def __init__(self, prompts_dir: str = "prompts"):
        """
        Initialize the prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt files
        """
        self.prompts_dir = Path(prompts_dir)
        self.index_file = self.prompts_dir / "prompts_index.json"
        self._index: Optional[Dict] = None
        self._system_prompts: Optional[Dict] = None
    
    @property
    def index(self) -> Dict:
        """Load and cache the prompts index."""
        if self._index is None:
            with open(self.index_file, 'r') as f:
                self._index = json.load(f)
        return self._index
    
    @property
    def system_prompts(self) -> Dict:
        """Load and cache system prompts."""
        if self._system_prompts is None:
            system_prompts_file = self.prompts_dir / "system_prompts.txt"
            self._system_prompts = {}
            
            with open(system_prompts_file, 'r') as f:
                content = f.read()
            
            # Parse multi-line prompts separated by key: value format
            # Each prompt starts with "key:" on its own consideration
            current_key = None
            current_lines = []
            
            for line in content.split('\n'):
                # Check if this is a new prompt key (has : and no leading space)
                if line and not line.startswith(' ') and not line.startswith('\t') and ':' in line:
                    # Save previous prompt if exists
                    if current_key:
                        self._system_prompts[current_key] = '\n'.join(current_lines).strip()
                    
                    # Start new prompt
                    key, value = line.split(':', 1)
                    current_key = key.strip()
                    current_lines = [value.strip()] if value.strip() else []
                elif current_key:
                    # Continue current prompt
                    current_lines.append(line)
            
            # Save last prompt
            if current_key:
                self._system_prompts[current_key] = '\n'.join(current_lines).strip()
        
        return self._system_prompts
    
    def load_prompt(self, prompt_name: str) -> str:
        """
        Load a prompt from file.
        
        Args:
            prompt_name: Name of the prompt (key in index)
            
        Returns:
            str: The prompt text
            
        Raises:
            FileNotFoundError: If prompt file doesn't exist
            KeyError: If prompt name not in index
        """
        if prompt_name not in self.index:
            raise KeyError(f"Prompt '{prompt_name}' not found in index")
        
        prompt_info = self.index[prompt_name]
        prompt_file = self.prompts_dir / prompt_info['file']
        
        with open(prompt_file, 'r') as f:
            return f.read()
    
    def get_system_prompt(self, prompt_name: str) -> str:
        """
        Get the system prompt for a given prompt.
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            str: The system prompt text
        """
        prompt_info = self.index.get(prompt_name, {})
        system_prompt_key = prompt_info.get('system_prompt')
        
        if system_prompt_key:
            return self.system_prompts.get(system_prompt_key, "")
        
        return ""
    
    def format_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Load and format a prompt with variables.
        
        Args:
            prompt_name: Name of the prompt
            **kwargs: Variables to format into the prompt
            
        Returns:
            str: Formatted prompt
        """
        prompt = self.load_prompt(prompt_name)
        
        # Handle optional variables
        for key, value in kwargs.items():
            if value is not None:
                placeholder = f"{{{key}}}"
                if placeholder in prompt:
                    # Format with proper prefix
                    if key == "transaction_id":
                        prompt = prompt.replace(placeholder, f"- Transaction ID: {value}")
                    elif key == "amount":
                        prompt = prompt.replace(placeholder, f"- Amount: ${value}")
                    else:
                        prompt = prompt.replace(placeholder, str(value))
            else:
                # Remove the placeholder line if value is None
                placeholder = f"{{{key}}}"
                lines = prompt.split('\n')
                prompt = '\n'.join(line for line in lines if placeholder not in line)
        
        return prompt

