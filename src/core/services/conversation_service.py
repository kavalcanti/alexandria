"""
Main conversation service that acts as a facade for conversation management.

This service provides a unified interface for conversation-related functionality
and serves as the main entry point for the UI layer. It focuses purely on
business logic coordination without handling dependency creation.

The service coordinates:
- Context management for conversation history
- LLM interactions and response generation
- Message management
- Optional retrieval-augmented generation (RAG)
"""

from typing import List, Dict, Any, Optional, Tuple
from src.logger import get_module_logger
from src.core.context.context_window import ContextWindow
from src.core.generation.llm_generator import LLMGenerator
from src.core.memory.llm_db_msg import MessagesController

logger = get_module_logger(__name__) 

class ConversationService:
    def __init__(
        self,
        conversation_id: int,
        context_window: ContextWindow,
        llm_generator: LLMGenerator,
        messages_controller: MessagesController,
    ) -> None:
        """
        Initialize the conversation service with injected dependencies.

        This constructor follows dependency injection principles, receiving
        all required components as parameters rather than creating them internally.
        This makes the service more testable and follows the Single Responsibility Principle.

        Args:
            conversation_id: ID of the conversation this service manages
            context_window: Manager for handling conversation context and history
            llm_generator: Manager for LLM interactions and response generation
            messages_controller: Controller for message database operations
            rag_manager: Optional manager for retrieval-augmented generation

        Returns:
            None
        """
        self.conversation_id = conversation_id
        self.context_window = context_window
        self.llm_generator = llm_generator
        self.messages_controller = messages_controller

        logger.info(f"Conversation Service initialized with conversation ID: {self.conversation_id}")

    def add_message(self, role: str, message: str) -> None:
        """
        Update the context window with a new message.

        Delegates context window management to the context manager component.

        Args:
            role: The role of the message sender (e.g., 'user', 'assistant', 'system')
            message: The content of the message to add to context

        Returns:
            None
        """
        self.context_window.add_message(role, message)

    def generate_chat_response(self, rag_enabled: bool = False, thinking_model: bool = True, max_new_tokens: int = 8096) -> Tuple[str, Optional[str], Optional[Any]]:
        """
        Generate a response using the LLM based on current context.

        Args:
            rag_enabled: Whether to enable retrieval-augmented generation.
                Defaults to False.
            thinking_model: Whether to use the thinking model for response generation.
                Defaults to True.
            max_new_tokens: Maximum number of tokens to generate in the response.
                Defaults to 8096.

        Returns:
            Tuple[str, Optional[str], Optional[Any]]: The generated response, thinking, and retrieval result from the LLM
        """
        if rag_enabled:
            # For RAG, we need to get the last user message and process it
            user_message = ""
            for message in reversed(self.context_window.context_window):
                if message['role'] == 'user':
                    user_message = message['content']
                    break
            
            # Use LLMGenerator for RAG processing (it handles context management internally)
            return self.llm_generator.generate_response(user_message, thinking_model, max_new_tokens, rag_enabled=True)
        else:
            # For standard generation, use LLM controller directly with current context
            response, thinking = self.llm_generator.llm_controller.generate_response_from_context(
                self.context_window.context_window, thinking_model, max_new_tokens
            )
            
            # Store assistant response in context
            self.context_window.add_message('assistant', response)
            if thinking:
                self.context_window.add_message('assistant-reasoning', thinking)
                
            return response, thinking, None

    def search_documents(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Search documents in the knowledge base.

        Provides direct access to document search functionality without generation.

        Args:
            query: Search query
            **kwargs: Additional search parameters

        Returns:
            Dict containing search results
        """
        if not self.rag_manager:
            raise RuntimeError("RAG manager not configured. Document search not available.")
        
        result = self.rag_manager.search_documents(query, **kwargs)
        
        return {
            "query": result.query,
            "total_matches": result.total_matches,
            "search_time_ms": result.search_time_ms,
            "matches": [
                {
                    "chunk_id": match.chunk_id,
                    "document_id": match.document_id,
                    "filepath": match.filepath,
                    "content": match.content,
                    "similarity_score": match.similarity_score,
                    "content_type": match.content_type
                }
                for match in result.matches
            ]
        }

    @property
    def is_rag_enabled(self) -> bool:
        """
        Check if RAG capabilities are enabled for this conversation.

        Returns:
            bool: True if RAG is enabled, False otherwise
        """
        return self.rag_manager is not None

    def get_rag_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get RAG system statistics and configuration.

        Returns:
            Dict with RAG statistics or None if RAG is not enabled
        """
        if not self.rag_manager:
            return None
        
        return self.rag_manager.get_retrieval_stats()

# Convenience function for backward compatibility and easy service creation
def create_conversation_service(
    context_window_len: int = 5,
    conversation_id: Optional[int] = None,
    load_latest_system: bool = True
) -> ConversationService:
    """
    Create a ConversationService instance using dependency injection.
    
    This function provides backward compatibility with the original constructor
    while using the new dependency injection architecture under the hood.
    
    Args:
        context_window_len: Number of messages to maintain in context window
        conversation_id: Optional existing conversation ID
        load_latest_system: Whether to load only the most recent system message
        
    Returns:
        ConversationService: Fully configured service instance
    """
    from src.core.services.service_container import get_container
    
    container = get_container()
    
    # Create a new context window instance configured for this conversation
    context_window = container.create_context_window(
        conversation_id=conversation_id or 0,
        context_window_len=context_window_len
    )
    
    # Create LLM generator with the context window
    llm_generator = container.create_llm_generator(context_window=context_window)
    
    # Create conversation service with injected dependencies
    return ConversationService(
        conversation_id=conversation_id or 0,  # Default to 0 if None
        context_window=context_window,
        llm_generator=llm_generator,
        messages_controller=container.messages_controller
    )

