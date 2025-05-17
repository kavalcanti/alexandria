"""Manages conversation services and their dependencies."""
import os
from src.llm.context_manager import ContextManager
from src.llm.service_llm import LLMService
from src.llm.llm_controller import LLMController
from src.llm.llm_db_cnvs_controller import ConversationsController
from src.llm.llm_db_msg_controller import MessagesController
from src.logger import get_module_logger
from src.llm.db_connector import DatabaseStorage

logger = get_module_logger(__name__) 

class ConversationManager:
    def __init__(self, context_window_len: int = 5, conversation_id: int = None, load_latest_system: bool = True):
        """
        Creates and manages the conversation services and their shared dependencies.
        Acts as a facade for the conversation functionality.
        
        Args:
            context_window_len: Number of messages to keep in context window
            conversation_id: Optional ID of existing conversation
            load_latest_system: Whether to load only latest system message
        """
        logger.info("Initializing Conversation Manager")
        # Initialize shared dependencies
        self.db_storage = DatabaseStorage()
        self.conversations_controller = ConversationsController(self.db_storage)
        self.messages_controller = MessagesController(self.db_storage)
        self.llm_handler = LLMController()
        # 
        # self.prompt_controller = LLMPromptController()
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
            llm_handler=self.llm_handler
        )

        # Initialize LLM service with reference to context manager
        self.llm_service = LLMService(
            msg_service=self.context_manager,
            conversation_id=self.conversation_id,
            load_latest_system=load_latest_system,
            conversations_controller=self.conversations_controller,
            llm_handler=self.llm_handler
        )

        logger.info(f"Conversation Manager initialized with conversation ID: {self.conversation_id}")

    def manage_context_window(self, role: str, message: str) -> None:
        """Delegate to context manager to manage context window."""
        self.context_manager.manage_context_window(role, message)

    def generate_chat_response(self, thinking_model: bool = True, max_new_tokens: int = 8096):
        """Delegate to LLM service."""
        return self.llm_service.generate_chat_response(thinking_model, max_new_tokens)

    @property
    def context_window(self):
        """Access the context window from context manager."""
        return self.context_manager.context_window