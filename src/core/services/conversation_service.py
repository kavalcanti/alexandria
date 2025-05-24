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
from src.core.managers.context_manager import ContextManager
from src.core.managers.llm_manager import LLMManager
from src.core.memory.llm_db_msg import MessagesController

logger = get_module_logger(__name__) 

class ConversationService:
    def __init__(
        self,
        conversation_id: int,
        context_manager: ContextManager,
        llm_manager: LLMManager,
        messages_controller: MessagesController,
        rag_manager: Optional['RAGManager'] = None
    ) -> None:
        """
        Initialize the conversation service with injected dependencies.

        This constructor follows dependency injection principles, receiving
        all required components as parameters rather than creating them internally.
        This makes the service more testable and follows the Single Responsibility Principle.

        Args:
            conversation_id: ID of the conversation this service manages
            context_manager: Manager for handling conversation context and history
            llm_manager: Manager for LLM interactions and response generation
            messages_controller: Controller for message database operations
            rag_manager: Optional manager for retrieval-augmented generation

        Returns:
            None
        """
        self.conversation_id = conversation_id
        self.context_manager = context_manager
        self.llm_manager = llm_manager
        self.messages_controller = messages_controller
        self.rag_manager = rag_manager

        logger.info(f"Conversation Service initialized with conversation ID: {self.conversation_id}")
        if self.rag_manager:
            logger.info("RAG capabilities enabled")

    def manage_context_window(self, role: str, message: str) -> None:
        """
        Update the context window with a new message.

        Delegates context window management to the context manager component.

        Args:
            role: The role of the message sender (e.g., 'user', 'assistant', 'system')
            message: The content of the message to add to context

        Returns:
            None
        """
        self.context_manager.manage_context_window(role, message)

    def generate_chat_response(self, thinking_model: bool = True, max_new_tokens: int = 8096) -> str:
        """
        Generate a response using the LLM based on current context.

        This method uses the standard LLM generation without retrieval augmentation.
        For RAG-enabled responses, use generate_rag_response instead.

        Args:
            thinking_model: Whether to use the thinking model for response generation.
                Defaults to True.
            max_new_tokens: Maximum number of tokens to generate in the response.
                Defaults to 8096.

        Returns:
            str: The generated response from the LLM
        """
        return self.llm_manager.generate_chat_response(thinking_model, max_new_tokens)

    def generate_rag_response(
        self, 
        user_query: str, 
        thinking_model: bool = True, 
        max_new_tokens: int = 8096
    ) -> Tuple[str, str, Optional[Dict[str, Any]]]:
        """
        Generate a response using retrieval-augmented generation.

        This method performs document retrieval and uses the retrieved context
        to generate more informed responses. Only available when RAG manager is configured.

        Args:
            user_query: The user's question or prompt
            thinking_model: Whether to use the thinking model for response generation
            max_new_tokens: Maximum number of tokens to generate in the response

        Returns:
            Tuple[str, str, Optional[Dict]]: (response, thinking, retrieval_info)
            - response: The generated response
            - thinking: The reasoning process (if thinking_model=True)
            - retrieval_info: Information about retrieved documents
        """
        if not self.rag_manager:
            raise RuntimeError("RAG manager not configured. Use generate_chat_response for standard generation.")
        
        response, thinking, retrieval_result = self.rag_manager.generate_rag_response(
            user_query=user_query,
            thinking_model=thinking_model,
            max_new_tokens=max_new_tokens
        )
        
        # Format retrieval info for return
        retrieval_info = None
        if retrieval_result:
            retrieval_info = {
                "query": retrieval_result.query,
                "total_matches": retrieval_result.total_matches,
                "search_time_ms": retrieval_result.search_time_ms,
                "matches": [
                    {
                        "filepath": match.filepath,
                        "content_preview": match.content[:200] + "..." if len(match.content) > 200 else match.content,
                        "similarity_score": match.similarity_score,
                        "content_type": match.content_type
                    }
                    for match in retrieval_result.matches
                ]
            }
        
        return response, thinking, retrieval_info

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
    def context_window(self) -> List[Dict[str, Any]]:
        """
        Get the current context window contents.

        Returns:
            List[Dict[str, Any]]: A list of message dictionaries in the current context window
        """
        return self.context_manager.context_window

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
    Create a ConversationService instance using the factory pattern.
    
    This function provides backward compatibility with the original constructor
    while using the new dependency injection architecture under the hood.
    
    Args:
        context_window_len: Number of messages to maintain in context window
        conversation_id: Optional existing conversation ID
        load_latest_system: Whether to load only the most recent system message
        
    Returns:
        ConversationService: Fully configured service instance
    """
    from src.core.services.conversation_service_factory import ConversationServiceFactory
    factory = ConversationServiceFactory()
    return factory.create_conversation_service(
        context_window_len=context_window_len,
        conversation_id=conversation_id,
        load_latest_system=load_latest_system
    )

# Convenience function for creating RAG-enabled conversations
def create_rag_conversation_service(
    context_window_len: int = 5,
    conversation_id: Optional[int] = None,
    load_latest_system: bool = True,
    rag_config: Optional['RAGConfig'] = None
) -> ConversationService:
    """
    Create a RAG-enabled ConversationService instance.
    
    Args:
        context_window_len: Number of messages to maintain in context window
        conversation_id: Optional existing conversation ID
        load_latest_system: Whether to load only the most recent system message
        rag_config: Optional RAG configuration settings
        
    Returns:
        ConversationService: RAG-enabled conversation service
    """
    from src.core.services.conversation_service_factory import ConversationServiceFactory
    factory = ConversationServiceFactory()
    return factory.create_rag_conversation_service(
        context_window_len=context_window_len,
        conversation_id=conversation_id,
        load_latest_system=load_latest_system,
        rag_config=rag_config
    ) 