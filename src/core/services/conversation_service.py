"""
Main conversation service that acts as a facade for conversation management.

This service bootstraps the backend and manages conversation managers and controllers.
It provides a unified interface for all conversation-related functionality and serves
as the main entry point for the UI layer.

The service coordinates:
- Context management for conversation history
- LLM interactions and response generation
- Database operations for conversations and messages
- Prompt management
"""

from typing import List, Optional, Dict, Any
from src.logger import get_module_logger
from src.infrastructure.llm_controller import LLMController
from src.infrastructure.db_connector import DatabaseStorage
from src.core.managers.context_manager import ContextManager
from src.core.managers.llm_manager import LLMManager
from src.core.memory.llm_db_cnvs import ConversationsController
from src.core.memory.llm_db_msg import MessagesController
from src.core.managers.prompt_manager import LLMPromptManager
from src.core.embedding.embedder import Embedder

logger = get_module_logger(__name__) 

class ConversationService:
    def __init__(
        self, 
        context_window_len: int = 5, 
        conversation_id: Optional[int] = None, 
        load_latest_system: bool = True
    ) -> None:
        """
        Initialize the conversation service with all required components.

        This constructor sets up all necessary controllers and managers for handling
        conversations, including database storage, context management, and LLM interactions.

        Args:
            context_window_len: Number of messages to maintain in the context window.
                Defaults to 5.
            conversation_id: Optional ID of an existing conversation to load.
                If None, creates a new conversation. Defaults to None.
            load_latest_system: Whether to load only the most recent system message.
                Defaults to True.

        Returns:
            None
        """
        # Initialize shared dependencies
        self.db_storage = DatabaseStorage()
        self.embedder = Embedder()
        self.conversations_controller = ConversationsController(self.db_storage)
        self.messages_controller = MessagesController(self.db_storage)
        self.llm_controller = LLMController()
        self.prompt_controller = LLMPromptManager()
        
        # Initialize conversation ID
        if conversation_id is None:
            self.conversation_id = self.conversations_controller.get_next_conversation_id()
            self.conversations_controller.insert_single_conversation(self.conversation_id)
        else:
            self.conversation_id = conversation_id
            if not self.conversations_controller.conversation_exists(self.conversation_id):
                self.conversations_controller.insert_single_conversation(self.conversation_id)

        # Initialize context manager first as the source of truth for context window
        self.context_manager = ContextManager(
            context_window_len=context_window_len,
            conversation_id=self.conversation_id,
            load_latest_system=load_latest_system,
            messages_controller=self.messages_controller,
            conversations_controller=self.conversations_controller,
            llm_controller=self.llm_controller,
            prompt_controller=self.prompt_controller
        )

        # Initialize LLM service with reference to context manager
        self.llm_manager = LLMManager(
            msg_service=self.context_manager,
            conversation_id=self.conversation_id,
            load_latest_system=load_latest_system,
            conversations_controller=self.conversations_controller,
            llm_controller=self.llm_controller
        )

        logger.info(f"Conversation Service initialized with conversation ID: {self.conversation_id}")

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

        Delegates the response generation to the LLM manager component.

        Args:
            thinking_model: Whether to use the thinking model for response generation.
                Defaults to True.
            max_new_tokens: Maximum number of tokens to generate in the response.
                Defaults to 8096.

        Returns:
            str: The generated response from the LLM
        """
        return self.llm_manager.generate_chat_response(thinking_model, max_new_tokens)

    @property
    def context_window(self) -> List[Dict[str, Any]]:
        """
        Get the current context window contents.

        Returns:
            List[Dict[str, Any]]: A list of message dictionaries in the current context window
        """
        return self.context_manager.context_window 