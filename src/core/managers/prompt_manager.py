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
        # Loads system prompts.
        # Handles prompt injection.
        # Defines specialist prompts.
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
            return f"{user_message}\n\nRelevant context from knowledge base:\n{retrieval_context}"
        else:
            return user_message

    def format_retrieval_context(self, matches: List[Dict[str, Any]], include_metadata: bool = True) -> str:
        """
        Format retrieval matches into a context string.

        Args:
            matches: List of document matches from retrieval
            include_metadata: Whether to include source metadata

        Returns:
            str: Formatted context string
        """
        if not matches:
            return ""
        
        context_parts = []
        for i, match in enumerate(matches):
            content = match.get('content', '')
            source_info = ""
            
            if include_metadata:
                filename = match.get('filename', 'Unknown')
                similarity = match.get('similarity_score', 0.0)
                source_info = f" (Source: {filename}, Relevance: {similarity:.2f})"
            
            context_parts.append(f"{i+1}. {content.strip()}{source_info}")
        
        return "\n\n".join(context_parts)

    def create_rag_prompt(self, user_query: str, context: str, include_instructions: bool = True) -> str:
        """
        Create a RAG-enhanced prompt with context.

        Args:
            user_query: The user's original question
            context: Retrieved context from documents
            include_instructions: Whether to include RAG-specific instructions

        Returns:
            str: Enhanced prompt with context and instructions
        """
        if include_instructions:
            instructions = "\nPlease provide a comprehensive answer using the context above where relevant. If the context doesn't contain relevant information, please indicate that and answer based on your general knowledge."
        else:
            instructions = ""

        return f"""{user_query}

Based on the following relevant information from the knowledge base:

{context}{instructions}"""

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