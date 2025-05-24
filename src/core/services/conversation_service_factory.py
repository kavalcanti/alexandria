"""
Factory for creating ConversationService instances.

This factory handles the complex creation logic for conversation services,
including conversation ID management and dependency injection.
"""

from typing import Optional
from src.core.services.service_container import get_container
from src.core.managers.context_manager import ContextManager
from src.core.managers.llm_manager import LLMManager
from src.logger import get_module_logger

logger = get_module_logger(__name__)


class ConversationServiceFactory:
    """
    Factory for creating properly configured ConversationService instances.
    
    This factory encapsulates the complex creation logic that was previously
    embedded in the ConversationService constructor, following the Factory pattern
    to separate object creation from business logic.
    """
    
    def __init__(self, container=None):
        """
        Initialize the factory with a service container.
        
        Args:
            container: Optional service container. If None, uses the global container.
        """
        self.container = container or get_container()
    
    def create_conversation_service(
        self, 
        context_window_len: int = 5, 
        conversation_id: Optional[int] = None, 
        load_latest_system: bool = True
    ) -> 'ConversationService':
        """
        Create a fully configured ConversationService instance.
        
        This method handles all the complex initialization logic including:
        - Conversation ID management and creation
        - Dependency injection and wiring
        - Context manager and LLM manager creation
        
        Args:
            context_window_len: Number of messages to maintain in context window
            conversation_id: Optional existing conversation ID
            load_latest_system: Whether to load only the most recent system message
            
        Returns:
            ConversationService: Fully configured service instance
        """
        # Handle conversation ID logic
        conversation_id = self._handle_conversation_id(conversation_id)
        
        # Create context manager with all dependencies
        context_manager = self._create_context_manager(
            context_window_len, conversation_id, load_latest_system
        )
        
        # Create LLM manager with dependencies
        llm_manager = self._create_llm_manager(
            context_manager, conversation_id, load_latest_system
        )
        
        # Import here to avoid circular imports
        from src.core.services.conversation_service import ConversationService
        
        # Create and return the service with injected dependencies
        return ConversationService(
            conversation_id=conversation_id,
            context_manager=context_manager,
            llm_manager=llm_manager,
            messages_controller=self.container.messages_controller
        )
    
    def _handle_conversation_id(self, conversation_id: Optional[int]) -> int:
        """
        Handle conversation ID creation and validation logic.
        
        Args:
            conversation_id: Optional existing conversation ID
            
        Returns:
            int: Valid conversation ID (existing or newly created)
        """
        if conversation_id is None:
            conversation_id = self.container.conversations_controller.get_next_conversation_id()
            self.container.conversations_controller.insert_single_conversation(conversation_id)
            logger.info(f"Created new conversation with ID: {conversation_id}")
        else:
            if not self.container.conversations_controller.conversation_exists(conversation_id):
                self.container.conversations_controller.insert_single_conversation(conversation_id)
                logger.info(f"Created conversation record for existing ID: {conversation_id}")
        
        return conversation_id
    
    def _create_context_manager(
        self, 
        context_window_len: int, 
        conversation_id: int, 
        load_latest_system: bool
    ) -> ContextManager:
        """
        Create a properly configured ContextManager instance.
        
        Args:
            context_window_len: Size of the context window
            conversation_id: ID of the conversation
            load_latest_system: Whether to load only latest system message
            
        Returns:
            ContextManager: Configured context manager instance
        """
        return ContextManager(
            context_window_len=context_window_len,
            conversation_id=conversation_id,
            load_latest_system=load_latest_system,
            messages_controller=self.container.messages_controller,
            conversations_controller=self.container.conversations_controller,
            llm_controller=self.container.llm_controller,
            prompt_controller=self.container.prompt_controller
        )
    
    def _create_llm_manager(
        self, 
        context_manager: ContextManager, 
        conversation_id: int, 
        load_latest_system: bool
    ) -> LLMManager:
        """
        Create a properly configured LLMManager instance.
        
        Args:
            context_manager: The context manager to use
            conversation_id: ID of the conversation
            load_latest_system: Whether to load only latest system message
            
        Returns:
            LLMManager: Configured LLM manager instance
        """
        return LLMManager(
            msg_service=context_manager,
            conversation_id=conversation_id,
            load_latest_system=load_latest_system,
            conversations_controller=self.container.conversations_controller,
            llm_controller=self.container.llm_controller,
            embedder=self.container.embedder
        ) 