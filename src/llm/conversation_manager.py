"""Manages conversation services and their dependencies."""
import os
from src.llm.service_msg import MSGService
from src.llm.service_llm import LLMService
from src.llm.llm_controller import LLMHandler
from src.llm.llm_db_controller import DatabaseStorage
import logging

logger = logging.getLogger(__name__)

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
        # Initialize shared dependencies
        self.db_storage = DatabaseStorage()
        self.llm_handler = LLMHandler()
        
        # Initialize conversation ID
        if conversation_id is None:
            self.conversation_id = self.db_storage.get_next_conversation_id()
            self.db_storage.insert_single_conversation(self.conversation_id)
        else:
            self.conversation_id = conversation_id
            if not self.db_storage.conversation_exists(self.conversation_id):
                self.db_storage.insert_single_conversation(self.conversation_id)

        # Initialize message service first as the source of truth for context window
        self.msg_service = MSGService(
            context_window_len=context_window_len,
            conversation_id=self.conversation_id,
            load_latest_system=load_latest_system,
            db_storage=self.db_storage,
            llm_handler=self.llm_handler
        )

        # Initialize LLM service with reference to message service
        self.llm_service = LLMService(
            msg_service=self.msg_service,
            conversation_id=self.conversation_id,
            load_latest_system=load_latest_system,
            db_storage=self.db_storage,
            llm_handler=self.llm_handler
        )

    def manage_context_window(self, role: str, message: str) -> None:
        """Delegate to message service to manage context window."""
        self.msg_service.manage_context_window(role, message)

    def generate_chat_response(self, thinking_model: bool = True, max_new_tokens: int = 8096):
        """Delegate to LLM service."""
        return self.llm_service.generate_chat_response(thinking_model, max_new_tokens)

    @property
    def context_window(self):
        """Access the context window from message service."""
        return self.msg_service.context_window