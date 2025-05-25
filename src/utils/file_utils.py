"""
Utility functions for file operations.
"""

import os
from datetime import datetime
from typing import Optional

def save_llm_output(content: str, thinking: Optional[str] = None, retrieval_info: Optional[str] = None) -> str:
    """
    Save LLM output to a markdown file in the datasets/saved directory.
    
    Args:
        content (str): The main LLM response content
        thinking (Optional[str]): Optional thinking/reasoning process
        retrieval_info (Optional[str]): Optional knowledge base retrieval information
        
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
    
    # Format the content with enhanced metadata
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    output = f"# {os.getenv('HF_MODEL')}\n"
    output += "---\n\n"
    output += "## Response\n\n"
    output += content + "\n"
    
    if retrieval_info:
        output += "\n---\n\n"
        output += "## Knowledge Base Sources\n\n"
        output += retrieval_info + "\n"
    
    if thinking:
        output += "\n---\n\n"
        output += "## Thinking Process\n\n"
        output += thinking + "\n"
    
    output += "\n---\n\n"
    output += "*This output was saved from Alexandria terminal interface*\n"
    
    # Save to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(output)
    
    return filepath 