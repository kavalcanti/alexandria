"""
UI state management and context window integration.

This module handles the state management for the Alexandria UI, including chat history,
thinking process display, and conversation context management.
"""
from typing import Optional, List, Dict, Tuple, TypeAlias
from prompt_toolkit.layout.controls import FormattedTextControl
from src.llm.services.conversation_service import ConversationService
from src.llm.services.service_right_pane import RightPaneService
from src.ui.markdown_formatter import MarkdownFormatter
from src.logger import get_module_logger
from src.utils.file_utils import save_llm_output

logger = get_module_logger(__name__)

# Type alias for formatted text used in prompt_toolkit
FormattedText: TypeAlias = List[Tuple[str, str]]

class StateManager:
    def __init__(
        self,
        chat_control: FormattedTextControl,
        thinking_control: FormattedTextControl,
        conversation_service: ConversationService
    ) -> None:
        """
        Initialize the state manager.
        
        Args:
            chat_control: Control for displaying chat messages in the UI
            thinking_control: Control for displaying thinking/reasoning process in the UI
            conversation_service: Service handling conversation state and context
        
        Returns:
            None
        """
        self.chat_control = chat_control
        self.thinking_control = thinking_control
        self.conversation_service = conversation_service
        self.markdown_formatter = MarkdownFormatter()
        self.right_pane_service = RightPaneService(self.conversation_service.messages_controller)
        # Initialize empty state
        self.chat_control.text = []
        self.thinking_control.text = []
        
        # Load initial conversation state
        if conversation_service.conversation_id:
            self._load_right_pane_messages()
            self._load_initial_conversation()
        
    def _format_message(self, role: str, content: str) -> FormattedText:
        """
        Format a message for display in the UI with Markdown support.
        
        Args:
            role: Message role identifier ('user', 'assistant', 'system', 'assistant-reasoning')
            content: Raw message content to be formatted
            
        Returns:
            FormattedText: Formatted message with role header, Markdown rendering, and spacing
        """
        role_display = {
            'user': 'You',
            'assistant': 'LLM',
            'system': 'System',
            'assistant-reasoning': 'Thoughts'
        }
        
        display_role = role_display.get(role, role.title())
        header = [("class:role", f"{display_role}:\n\n")]
        
        # Convert content to formatted text with Markdown support
        formatted_content = self.markdown_formatter.convert_to_formatted_text(content)
        
        # Add spacing after message
        footer = [("", "\n")]
        
        return header + formatted_content + footer
    
    def _load_initial_conversation(self) -> None:
        """
        Load the current conversation from the context window into the UI.
        Formats and displays all messages in reverse chronological order.
        
        Returns:
            None
        """
        chat_text: FormattedText = []
        
        # Get messages from context window in reverse order
        for message in reversed(self.conversation_service.context_window):
            role = message.get('role')
            content = message.get('content', '')
            
            if role != 'system':
                formatted_msg = self._format_message(role, content)
                chat_text.extend(formatted_msg)
        
        # Update UI controls with messages in reverse chronological order
        self.chat_control.text = chat_text

    def _load_right_pane_messages(self) -> None:
        """
        Load the right pane messages for the conversation, displaying the AI's
        thinking process and reasoning.
        
        Returns:
            None
        """
        thinking_text: FormattedText = []
        for message in self.right_pane_service.get_thinking_messages(self.conversation_service.conversation_id):
            formatted_msg = self._format_message('assistant-reasoning', message)
            thinking_text.extend(formatted_msg)
        self.thinking_control.text = thinking_text
        logger.info(f"Right pane messages: {thinking_text}")
        
    def append_user_message(self, message: str) -> None:
        """
        Append a user message to both UI and context window.
        
        Args:
            message: The user's message content to be added
            
        Returns:
            None
        """
        formatted_message = self._format_message('user', message)
        self.chat_control.text = formatted_message + self.chat_control.text
        self.conversation_service.manage_context_window("user", message)
        
    def append_assistant_message(self, message: str, thinking: Optional[str] = None) -> None:
        """
        Append an assistant message to UI and optionally add thinking process.
        The message is already added to the context window by _parse_llm_response.
        
        Args:
            message: The assistant's response content
            thinking: Optional thinking/reasoning process to display in right pane
            
        Returns:
            None
        """
        if thinking:
            formatted_thinking = self._format_message('assistant-reasoning', thinking)
            self.thinking_control.text = formatted_thinking + self.thinking_control.text
            self.conversation_service.manage_context_window("assistant-reasoning", thinking)
            logger.info(f"Appending assistant reasoning message: {thinking}")

        formatted_message = self._format_message('assistant', message)
        self.chat_control.text = formatted_message + self.chat_control.text
        self.conversation_service.manage_context_window("assistant", message)
        logger.info(f"Appending assistant message: {message}")

        # Save the output to a markdown file
        saved_path = save_llm_output(message, thinking)
        logger.info(f"Saved LLM output to: {saved_path}")

    def reset_state(self) -> None:
        """
        Reset both UI controls and create a new conversation manager instance.
        
        Returns:
            None
        """
        self.chat_control.text = []
        self.thinking_control.text = []
        self.conversation_service = ConversationService()
        
    def get_chat_text(self) -> FormattedText:
        """
        Get current chat text.
        
        Returns:
            FormattedText: Current formatted chat text
        """
        return self.chat_control.text
        
    def get_thinking_text(self) -> FormattedText:
        """
        Get current thinking text.
        
        Returns:
            FormattedText: Current formatted thinking text
        """
        return self.thinking_control.text

    def save_current_output(self) -> Optional[str]:
        """
        Save the most recent LLM output to a markdown file.
        
        Returns:
            Optional[str]: Path to the saved file if there was output to save, None otherwise
        """
        # Get the most recent assistant message and thinking from the context window
        for message in self.conversation_service.context_window:
            if message.get('role') == 'assistant':
                content = message.get('content', '')
                # Get the most recent thinking message
                thinking_messages = self.right_pane_service.get_thinking_messages(self.conversation_service.conversation_id)
                thinking = thinking_messages[0] if thinking_messages else None
                
                # Save to file
                saved_path = save_llm_output(content, thinking)
                logger.info(f"Manually saved LLM output to: {saved_path}")
                return saved_path
        
        logger.info("No assistant message found to save")
        return None 