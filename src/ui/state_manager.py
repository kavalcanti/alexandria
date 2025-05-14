"""
UI state management and context window integration.
"""
from typing import Optional
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
        
    def append_user_message(self, message: str) -> None:
        """
        Append a user message to both UI and context window.
        
        Args:
            message: The user's message
        """
        self.chat_control.text = self.chat_control.text + f"You:\n{message}\n"
        self.handler.manage_context_window("user", message)
        
    def append_assistant_message(self, message: str, thinking: Optional[str] = None) -> None:
        """
        Append an assistant message to UI only.
        The message is already added to the context window by _parse_llm_response.
        
        Args:
            message: The assistant's response
            thinking: Optional thinking/reasoning process
        """
        self.chat_control.text = self.chat_control.text + f"LLM:\n{message}\n"
        if thinking:
            self.thinking_control.text = self.thinking_control.text + f"Thoughts:\n{thinking}\n"
        
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