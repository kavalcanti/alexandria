'''
Manages LLM prompts, system prompts, and prompt injection functionality.

This module provides a manager class for handling various aspects of prompt management
including system prompts, user prompt injection, and specialized prompt templates.
'''

from typing import Optional, List, Dict, Any


class LLMPromptManager:
    def __init__(self) -> None:
        """
        Initialize the LLM Prompt Manager.

        Sets up the default system prompt and initializes prompt management functionality.

        Returns:
            None
        """
        self._default_system_prompt: str = """You are an advanced AI assistant. You provide detailed, accurate, and helpful responses to user queries."""
        
        self._rag_system_prompt: str = """You are an advanced AI assistant with access to a knowledge base. When provided with relevant context from documents, use this information to provide comprehensive and accurate responses. Always acknowledge when you're using information from the provided context and cite sources when available."""

        return None

    def get_system_prompt(self, use_rag: bool = False) -> str:
        """
        Get the system prompt.

        Args:
            use_rag: Whether to use the RAG-enhanced system prompt

        Returns:
            str: The system prompt used for LLM interactions.
        """
        return self._rag_system_prompt if use_rag else self._default_system_prompt
    
    def insert_retrieval_in_usr_msg(self, user_message: str, retrieval_context: Optional[str] = None) -> str:
        """
        Inject the user prompt with optional retrieval context.

        Args:
            user_message (str): The user's input message to be processed
            retrieval_context (Optional[str], optional): Additional context to be injected. Defaults to None.

        Returns:
            str: The processed prompt with injected context if provided
        """
        if retrieval_context:
            return f"{user_message}\n\nRelevant context from knowledge base:\n{retrieval_context}"
        else:
            return user_message

    def insert_retrieval_in_system_prompt(self, retrieval_context: str) -> str:
        retrieval_system_msg = {
            'role': 'system',
            'content': f"You have access to the following relevant information from the knowledge base:\n\n{retrieval_context}\n\nUse this information to provide accurate and comprehensive answers."
        }
        return retrieval_system_msg

    def get_thinking_prompt_enhancement(self) -> str:
        """
        Get additional prompt enhancement for thinking models when using RAG.

        Returns:
            str: Additional instructions for thinking models
        """
        return """When answering, consider:
1. How well the provided context addresses the question
2. Whether additional context might be needed
3. How to best synthesize the context with your knowledge
4. What limitations exist in the available information"""