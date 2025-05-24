'''
Manages LLM prompts, system prompts, and prompt injection functionality.

This module provides a manager class for handling various aspects of prompt management
including system prompts, user prompt injection, and specialized prompt templates.
'''

from typing import Optional


class LLMPromptManager:
    def __init__(self) -> None:
        """
        Initialize the LLM Prompt Manager.

        Sets up the default system prompt and initializes prompt management functionality.

        Returns:
            None
        """
        # Loads system prompts.
        # Handles prompt injection.
        # Defines specialist prompts.
        self._default_system_prompt: str = """You are an advanced AI assistant. You provide detailed, accurate, and helpful responses to user queries."""

        return None

    def get_system_prompt(self) -> str:
        """
        Get the system prompt.

        Returns:
            str: The default system prompt used for LLM interactions.
        """
        return self._default_system_prompt
    
    def user_prompt_injector(self, user_message: str, retrieval_context: Optional[str] = None) -> str:
        """
        Inject the user prompt with optional retrieval context.

        Args:
            user_message (str): The user's input message to be processed
            retrieval_context (Optional[str], optional): Additional context to be injected. Defaults to None.

        Returns:
            str: The processed prompt with injected context if provided
        """
        if retrieval_context:
            return f"{user_message} Here is what we currently know about it: {retrieval_context}"
        else:
            return user_message