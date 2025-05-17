"""
Utility functions for file operations.
"""

import os
from datetime import datetime
from typing import Optional

def save_llm_output(content: str, thinking: Optional[str] = None) -> str:
    """
    Save LLM output to a markdown file in the datasets/saved directory.
    
    Args:
        content (str): The main LLM response content
        thinking (Optional[str]): Optional thinking/reasoning process
        
    Returns:
        str: Path to the saved file
    """
    # Create timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"llm_output_{timestamp}.md"
    
    # Ensure the saved directory exists
    save_dir = "datasets/saved"
    os.makedirs(save_dir, exist_ok=True)
    
    filepath = os.path.join(save_dir, filename)
    
    # Format the content
    output = f"# LLM Output - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    output += "## Response\n\n"
    output += content + "\n"
    
    if thinking:
        output += "\n## Thinking Process\n\n"
        output += thinking + "\n"
    
    # Save to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(output)
    
    return filepath 