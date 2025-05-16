"""
UI state management and context window integration.
"""
from typing import Optional, List, Dict, Tuple
from prompt_toolkit.layout.controls import FormattedTextControl
from src.llm.conversation_manager import ConversationManager
from src.ui.markdown_formatter import MarkdownFormatter

FormattedText = List[Tuple[str, str]]

class StateManager:
    def __init__(
        self,
        chat_control: FormattedTextControl,
        thinking_control: FormattedTextControl,
        conversation_manager: ConversationManager
    ):
        """
        Initialize the state manager.
        
        Args:
            chat_control: FormattedTextControl for chat display
            thinking_control: FormattedTextControl for thinking display
            conversation_manager: ConversationManager instance
        """
        self.chat_control = chat_control
        self.thinking_control = thinking_control
        self.conversation_manager = conversation_manager
        self.markdown_formatter = MarkdownFormatter()
        
        # Initialize empty state
        self.chat_control.text = []
        self.thinking_control.text = []
        
        # Load initial conversation state
        self._load_initial_conversation()
        
    def _format_message(self, role: str, content: str) -> FormattedText:
        """
        Format a message for display in the UI with Markdown support.
        
        Args:
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            
        Returns:
            Formatted message with Markdown rendering
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
        """
        chat_text: FormattedText = []
        thinking_text: FormattedText = []
        
        # Get messages from context window in reverse order
        for message in reversed(self.conversation_manager.context_window):
            role = message.get('role')
            content = message.get('content', '')
            
            formatted_msg = self._format_message(role, content)
            if role == 'assistant-reasoning':
                thinking_text.extend(formatted_msg)
            else:
                chat_text.extend(formatted_msg)
        
        # Update UI controls with messages in reverse chronological order
        self.chat_control.text = chat_text
        self.thinking_control.text = thinking_text
        
    def append_user_message(self, message: str) -> None:
        """
        Append a user message to both UI and context window.
        
        Args:
            message: The user's message
        """
        formatted_message = self._format_message('user', message)
        self.chat_control.text = formatted_message + self.chat_control.text
        self.conversation_manager.manage_context_window("user", message)
        
    def append_assistant_message(self, message: str, thinking: Optional[str] = None) -> None:
        """
        Append an assistant message to UI only.
        The message is already added to the context window by _parse_llm_response.
        
        Args:
            message: The assistant's response
            thinking: Optional thinking/reasoning process
        """
        if thinking:
            formatted_thinking = self._format_message('assistant-reasoning', thinking)
            self.thinking_control.text = formatted_thinking + self.thinking_control.text
            self.conversation_manager.manage_context_window("assistant-reasoning", thinking)

        formatted_message = self._format_message('assistant', message)
        self.chat_control.text = formatted_message + self.chat_control.text
        self.conversation_manager.manage_context_window("assistant", message)


    def reset_state(self) -> None:
        """Reset both UI controls and create a new conversation manager instance."""
        self.chat_control.text = []
        self.thinking_control.text = []
        self.conversation_manager = ConversationManager()
        
    def get_chat_text(self) -> FormattedText:
        """Get current chat text."""
        return self.chat_control.text
        
    def get_thinking_text(self) -> FormattedText:
        """Get current thinking text."""
        return self.thinking_control.text 