"""Manages the context window and message history for conversations.

This module provides functionality to maintain conversation history, handle message context,
and manage the flow of messages between users and assistants while respecting context window limits.
"""

from typing import List, Dict, Optional, Any
from src.core.memory.llm_db_msg import MessagesController
from src.core.memory.llm_db_cnvs import ConversationsController
from src.infrastructure.llm_controller import LLMController
from src.core.managers.prompt_manager import LLMPromptManager
from src.logger import get_module_logger

logger = get_module_logger(__name__) 

class ContextManager:
    def __init__(self, 
                 context_window_len: int = 5, 
                 conversation_id: Optional[int] = None, 
                 load_latest_system: bool = True,
                 messages_controller: Optional[MessagesController] = None,
                 conversations_controller: Optional[ConversationsController] = None,
                 llm_controller: Optional[LLMController] = None,
                 prompt_controller: Optional[LLMPromptManager] = None) -> None:
        """Initialize the ContextManager to handle conversation context and message history.

        The ContextManager maintains a sliding window of conversation context, handles message
        storage in the database, and manages the conversation flow while respecting context limits.
        It can be configured to either keep all system messages or only the most recent one.

        Args:
            context_window_len: The maximum number of messages to maintain in the context window,
                              including system messages.
            conversation_id: The unique identifier for the conversation. If None, a new conversation
                           will be created.
            load_latest_system: If True, only keeps the most recent system message in context.
                              If False, retains all system messages within the context window limit.
            messages_controller: Controller for message database operations. Will be initialized
                              if not provided.
            conversations_controller: Controller for conversation database operations. Will be
                                   initialized if not provided.
            llm_controller: Controller for LLM operations. Will be initialized if not provided.
            prompt_controller: Controller for managing system prompts. Will be initialized if
                            not provided.

        Returns:
            None
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
        self._context_window: List[Dict[str, str]] = self._load_context_window()
        self._inject_system_prompt()

        return None

    def _inject_system_prompt(self) -> None:
        """Inject the system prompt into the context window at the beginning.

        Retrieves the set system prompt from the prompt manager and adds it
        as the first message in the context window.

        Returns:
            None
        """
        self._context_window.insert(0, {
            'role': 'system',
            'content': self.prompt_controller.get_system_prompt()
        })

    def _load_context_window(self) -> List[Dict[str, Any]]:
        """Load and prepare the context window from the database.

        Retrieves messages from the database and processes them according to the
        context window settings. Handles system messages based on load_latest_system
        configuration and ensures messages are in chronological order.

        Returns:
            List[Dict[str, Any]]: List of message dictionaries containing at minimum
                                'role' and 'content' keys, ordered chronologically and
                                limited by context window length.
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

    def manage_context_window(self, role: str, message: str) -> None:
        """Manage the context window by storing messages and maintaining context size.

        Stores new messages in the database and updates the sliding context window.
        Handles different message roles differently:
        - User messages: May be processed through prompt injection
        - System/User/Assistant messages: Added to context window
        - Assistant-reasoning messages: Stored but not added to context window
        
        The context window maintains its size limit by removing older messages when
        necessary, while always preserving the most recent system message.

        Args:
            role: The role of the message sender. Must be one of:
                 'user', 'assistant', 'system', or 'assistant-reasoning'
            message: The content of the message to be stored and potentially added to context

        Returns:
            None
        """
        # Store the new message if it's a valid role
        logger.debug(f"Managing context window: 'role':{role}, 'content':{message}")
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

    @property
    def context_window(self) -> List[Dict[str, str]]:
        """Get the current context window.
        
        Returns:
            List[Dict[str, str]]: The current list of messages in the context window,
                                 where each message is a dictionary containing 'role'
                                 and 'content' keys.
        """
        return self._context_window

    @context_window.setter
    def context_window(self, value: List[Dict[str, str]]) -> None:
        """Update the context window with a new set of messages.
        
        Args:
            value: New list of messages to set as the context window. Each message
                  must be a dictionary containing 'role' and 'content' keys.

        Returns:
            None
        """
        self._context_window = value 