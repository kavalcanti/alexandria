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
from src.core.memory.llm_db_cnvs import ConversationsController

logger = get_module_logger(__name__) 

class ConversationService:
    def __init__(
        self,
        conversation_id: Optional[int],
        context_window: ContextWindow,
        llm_generator: LLMGenerator,
        messages_controller: MessagesController,
        conversations_controller: ConversationsController
    ) -> None:
        """
        Initialize the conversation service with injected dependencies.

        This constructor follows dependency injection principles, receiving
        all required components as parameters rather than creating them internally.
        This makes the service more testable and follows the Single Responsibility Principle.

        Args:
            conversation_id: ID of the conversation this service manages (None for new conversation)
            context_window: Manager for handling conversation context and history
            llm_generator: Manager for LLM interactions and response generation
            messages_controller: Controller for message database operations
            conversations_controller: Controller for conversation database operations

        Returns:
            None
        """
        self.conversations_controller = conversations_controller
        self.messages_controller = messages_controller
        self.llm_generator = llm_generator
        self.context_window = context_window
        
        if conversation_id:
            self.conversation_id = conversation_id
            # Load existing conversation context
            existing_messages = self.messages_controller.get_context_window_messages(conversation_id, context_window.context_window_len)
            if existing_messages:
                # Convert to context format
                context_messages = [{'role': msg['role'], 'content': msg['content']} for msg in existing_messages]
                self.context_window.context_window = context_messages
        else:
            # Create new conversation
            self.conversation_id = self.conversations_controller.get_next_conversation_id()
            self.conversations_controller.insert_single_conversation(self.conversation_id, 0, "", None)
            # Store the system prompt in database
            system_content = self.context_window.context_window[0]['content']
            self.messages_controller.insert_single_message(self.conversation_id, 'system', system_content, 0)

        logger.info(f"Conversation Service initialized with conversation ID: {self.conversation_id}")

    def add_conversation_message(self, role: str, message: str, token_count: int = 0) -> None:
        """
        Add a message to both context and database.

        Args:
            role: The role of the message sender (e.g., 'user', 'assistant', 'system')
            message: The content of the message to add to context
            token_count: The number of tokens in the message

        Returns:
            None
        """
        # Add to context (in-memory)
        if role != 'assistant-reasoning':
            self.context_window.add_message(role, message)
        # Store in database
        self.messages_controller.insert_single_message(self.conversation_id, role, message, token_count)
        self.conversations_controller.update_message_count(self.conversation_id, 1)

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
        logger.info(f"Context window length: {len(self.context_window.context_window)}")
        logger.info(f"Context window: {self.context_window.context_window}")
        if len(self.context_window.context_window) == 4:
            title, title_embedding = self.llm_generator.generate_conversation_title()
            self.conversations_controller.update_conversation_title(self.conversation_id, title, title_embedding)

        # Get the last user message
        user_message = ""
        for message in reversed(self.context_window.context_window):
            if message['role'] == 'user':
                user_message = message['content']
                break
        
        # Generate response using LLM generator (it doesn't modify context)
        response, thinking, retrieval_result = self.llm_generator.process_generation_by_type(
            user_message, thinking_model, max_new_tokens, rag_enabled=rag_enabled
        )

        return response, thinking, retrieval_result

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
        if not self.llm_generator.retrieval_interface:
            raise RuntimeError("Retrieval interface not configured. Document search not available.")
        
        result = self.llm_generator.retrieval_interface.search_documents(query, **kwargs)
        
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
        return self.llm_generator.retrieval_interface is not None

    def get_rag_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get RAG system statistics and configuration.

        Returns:
            Dict with RAG statistics or None if RAG is not enabled
        """
        if not self.llm_generator.retrieval_interface:
            return None
        
        # Return basic stats - extend as needed
        return {"retrieval_enabled": True}

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
        conversation_id=conversation_id,
        context_window_len=context_window_len
    )
    
    # Create LLM generator with the context window
    llm_generator = container.create_llm_generator(context_window=context_window)
    
    # Create conversation service with injected dependencies
    return ConversationService(
        conversation_id=conversation_id,
        context_window=context_window,
        llm_generator=llm_generator,
        messages_controller=container.messages_controller,
        conversations_controller=container.conversations_controller
    )

