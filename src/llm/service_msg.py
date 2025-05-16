import os
from src.llm.llm_db_loggers import *
from src.llm.llm_handler import LLMHandler
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename='logs/msg.log', encoding='utf-8', level=logging.INFO)

class MSGService:
    def __init__(self, 
                 context_window_len: int = 5, 
                 conversation_id: int = None, 
                 load_latest_system: bool = True,
                 db_storage: DatabaseStorage = None,
                 llm_handler: LLMHandler = None):
        """
        Will handle the message service for the LLM. 
        Context window and history are handled here.
        UI content is handled here.

        Params:
            context_window_len: int number of messages to keep in context window, including system message.
            conversation_id: int id of the conversation. If None, creates a new conversation.
            load_latest_system: bool whether to load only the latest system message (True) or all system messages (False)
            db_storage: Optional DatabaseStorage instance for dependency injection
            llm_handler: Optional LLMHandler instance for dependency injection
        """
        # Load dependencies
        self.context_window_len = context_window_len
        self.db_storage = db_storage or DatabaseStorage()
        self.llm_handler = llm_handler or LLMHandler()
        self.conversation_id = conversation_id
        self.load_latest_system = load_latest_system

        # Load initial context window from database

        self._context_window = self._load_context_window()
        logger.info(f"Context window: {self._context_window}")

        return None

    def _load_context_window(self):
        """
        Load context window from database with proper message ordering and system message handling.
        Returns a list of message dictionaries in the correct sequence, according to max context window length.
        """
        # Get messages from database
        messages = self.db_storage.get_context_window_messages(
            self.conversation_id,
            self.context_window_len
        )

        # If we should only load the latest system message
        if self.load_latest_system:
            # Filter system messages
            system_messages = [msg for msg in messages if msg['role'] == 'system']
            non_system_messages = [msg for msg in messages if msg['role'] != 'system']
            
            # Only keep the latest system message if any exist
            if system_messages:
                latest_system = system_messages[-1]
                messages = [latest_system] + non_system_messages
            else:
                messages = non_system_messages

        # Ensure messages are in chronological order
        messages.sort(key=lambda x: x.get('timestamp', 0))
        
        return messages

    def manage_context_window(self, role: str, message: str):
        """
        Handles the context window by storing message in database and refreshing context.
        The context window is always loaded from the database to ensure consistency.
        Only user and assistant messages are included in the context window.
        Assistant reasoning messages are stored but not included in the context.
        """
        # Store the new message if it's a valid role
        if role in ['user', 'assistant', 'system', 'assistant-reasoning']:
            self.db_storage.insert_single_message(
                self.conversation_id,
                role,
                message,
                self.llm_handler.get_token_count(message)  # Get token count
            )
            # Only refresh context window for messages that should be in it
            if role in ['user', 'assistant', 'system']:
                self.db_storage.update_message_count(self.conversation_id)
                self._context_window = self._load_context_window()
        else:
            logger.warning(f"Invalid message role: {role}")

        return None

    @property
    def context_window(self):
        """Get the current context window."""
        return self._context_window

    @context_window.setter
    def context_window(self, value):
        """Update the context window."""
        self._context_window = value