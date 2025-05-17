"""Manages the context window and message history for conversations."""

from src.llm.controllers.llm_db_msg_controller import MessagesController
from src.llm.controllers.llm_db_cnvs_controller import ConversationsController
from src.llm.controllers.llm_controller import LLMController
from src.llm.managers.prompt_manager import LLMPromptManager
from src.logger import get_module_logger

logger = get_module_logger(__name__) 

class ContextManager:
    def __init__(self, 
                 context_window_len: int = 5, 
                 conversation_id: int = None, 
                 load_latest_system: bool = True,
                 messages_controller: MessagesController = None,
                 conversations_controller: ConversationsController = None,
                 llm_controller: LLMController = None,
                 prompt_controller: LLMPromptManager = None):
        """
        Manages the context window and message history for conversations.
        Handles loading, updating, and maintaining the conversation context.

        Params:
            context_window_len: int number of messages to keep in context window, including system message.
            conversation_id: int id of the conversation. If None, creates a new conversation.
            load_latest_system: bool whether to load only the latest system message (True) or all system messages (False)
            conversations_controller: Optional ConversationsController instance for dependency injection
            llm_handler: Optional LLMHandler instance for dependency injection
        """
        # Load dependencies
        self.context_window_len = context_window_len
        self.messages_controller = messages_controller
        self.conversations_controller = conversations_controller
        self.llm_controller = llm_controller
        self.conversation_id = conversation_id
        self.load_latest_system = load_latest_system
        self.prompt_controller = prompt_controller
        # Load initial context window from database
        self._context_window = self._load_context_window()
        self._inject_system_prompt()

        return None

    def _inject_system_prompt(self):
        """
        Inject system prompt into context window.
        """
        self._context_window.insert(0, {
            'role': 'system',
            'content': self.prompt_controller.get_system_prompt()
        })

    def _load_context_window(self):
        """
        Load context window from database with proper message ordering and system message handling on initialisation.
        Returns a list of message dictionaries in the correct sequence, according to max context window length.
        """
        # Get messages from database
        messages = self.messages_controller.get_context_window_messages(
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
        The context window is initially loaded from the database to allow for the chat history to be loaded.
        The context window is then managed as a list of message dictionaries.
        Only user and assistant messages are included in the context window.
        Assistant reasoning messages are stored but not included in the context.
        """
        # Store the new message if it's a valid role
        logger.debug(f"Managing context window: {role} {message}")
        if role == 'user':
                message = self.prompt_controller.user_prompt_injector(message)

        logger.debug(f"Context window: {self._context_window}")
        if role in ['user', 'assistant', 'system', 'assistant-reasoning']:
            self.messages_controller.insert_single_message(
                self.conversation_id,
                role,
                message,
                self.llm_controller.get_token_count(message)  # Get token count
            )
            # Only refresh context window for messages that should be in it
            
            if role in ['user', 'assistant', 'system']:
                self.conversations_controller.update_message_count(self.conversation_id)
                # self._context_window = self._load_context_window()

                if len(self._context_window) > self.context_window_len and self._context_window[0]['role'] == 'system':
                    self._context_window.pop(1)
                    self._context_window.append(
                        {
                            'role': role,
                            'content': message,
                        }
                    )
                elif len(self._context_window) > self.context_window_len:
                    self._context_window.pop(0)
                    self._context_window.append(
                            {
                                'role': role,
                                'content': message
                            }
                        )
                else:
                    self._context_window.append(
                        {
                            'role': role,
                            'content': message,
                        }
                    )

            logger.debug(f"Context window: {self._context_window}")
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