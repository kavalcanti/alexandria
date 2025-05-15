"""
UI state management and context window integration.
"""
from typing import Optional, List, Dict
from prompt_toolkit.layout.controls import FormattedTextControl
from src.llm.conversation import ConversationHandler

class StateManager:
    def __init__(
        self,
        chat_control: FormattedTextControl,
        thinking_control: FormattedTextControl,
        handler: ConversationHandler
    ):
        """
        Initialize the state manager.
        
        Args:
            chat_control: FormattedTextControl for chat display
            thinking_control: FormattedTextControl for thinking display
            handler: ConversationHandler instance
        """
        self.chat_control = chat_control
        self.thinking_control = thinking_control
        self.handler = handler
        
        # Initialize empty state
        self.chat_control.text = ""
        self.thinking_control.text = ""
        
        # Load initial conversation state
        self._load_initial_conversation()
        
    def _format_message(self, role: str, content: str) -> str:
        """
        Format a message for display in the UI.
        
        Args:
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            
        Returns:
            Formatted message string
        """
        role_display = {
            'user': 'You',
            'assistant': 'LLM',
            'system': 'System',
            'assistant-reasoning': 'Thoughts'
        }
        
        display_role = role_display.get(role, role.title())
        return f"{display_role}:\n{content}\n\n"
    
    def _load_initial_conversation(self) -> None:
        """
        Load the current conversation from the context window into the UI.
        Formats and displays all messages in reverse chronological order.
        """
        chat_text = []
        thinking_text = []
        
        # Get messages from context window in reverse order
        for message in reversed(self.handler.context_window):
            role = message.get('role')
            content = message.get('content', '')
            
            if role == 'assistant-reasoning':
                thinking_text.append(self._format_message(role, content))
            else:
                chat_text.append(self._format_message(role, content))
        
        # Update UI controls with messages in reverse chronological order
        self.chat_control.text = ''.join(chat_text)
        self.thinking_control.text = ''.join(thinking_text)
        
    def append_user_message(self, message: str) -> None:
        """
        Append a user message to both UI and context window.
        
        Args:
            message: The user's message
        """
        formatted_message = self._format_message('user', message)
        self.chat_control.text = formatted_message + self.chat_control.text
        self.handler.manage_context_window("user", message)
        
    def append_assistant_message(self, message: str, thinking: Optional[str] = None) -> None:
        """
        Append an assistant message to UI only.
        The message is already added to the context window by _parse_llm_response.
        
        Args:
            message: The assistant's response
            thinking: Optional thinking/reasoning process
        """
        formatted_message = self._format_message('assistant', message)
        self.chat_control.text = formatted_message + self.chat_control.text
        
        if thinking:
            formatted_thinking = self._format_message('assistant-reasoning', thinking)
            self.thinking_control.text = formatted_thinking + self.thinking_control.text
        
    def reset_state(self) -> None:
        """Reset both UI controls and create a new handler instance."""
        self.chat_control.text = ""
        self.thinking_control.text = ""
        self.handler = ConversationHandler()
        
    def get_chat_text(self) -> str:
        """Get current chat text."""
        return self.chat_control.text
        
    def get_thinking_text(self) -> str:
        """Get current thinking text."""
        return self.thinking_control.text 