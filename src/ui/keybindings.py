"""
Keyboard bindings for the Alexandria UI.
"""
import asyncio
import os
import re
from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding import KeyBindings
from src.llm.conversation import ConversationHandler
from src.ui.state_manager import StateManager

def create_keybindings(
    msg_buffer,
    chat_formatted_text,
    thinking_formatted_text,
    chat_window,
    thinking_window,
    msg_window,
    handler,
    application=None
):
    """
    Create and return keyboard bindings for the Alexandria UI.
    
    Args:
        msg_buffer: Buffer for message input
        chat_formatted_text: FormattedTextControl for chat display
        thinking_formatted_text: FormattedTextControl for thinking display
        chat_window: ScrollablePane for chat
        thinking_window: ScrollablePane for thinking
        msg_window: Window for message input
        handler: ConversationHandler instance
        application: Optional Application instance for focus management
    
    Returns:
        KeyBindings object with all necessary bindings
    """
    kb = KeyBindings()
    
    # Initialize state manager
    state_manager = StateManager(chat_formatted_text, thinking_formatted_text, handler)

    @kb.add('c-q')
    def _(event):
        """Exit the application."""
        event.app.exit()

    @kb.add('c-up')
    def _(event):
        """Scroll chat window up by one line."""
        chat_window.vertical_scroll = max(0, chat_window.vertical_scroll - 1)
        event.app.invalidate()

    @kb.add('c-down')
    def _(event):
        """Scroll chat window down by one line."""
        # Count both spaces and newlines as line indicators
        chat_text = len(re.findall(r'[\s\n]', state_manager.get_chat_text()))
        # Use a conservative estimate
        max_scroll = chat_text/8 if chat_text else 0
        chat_window.vertical_scroll = min(chat_window.vertical_scroll + 1, int(max_scroll))
        event.app.invalidate()

    @kb.add('s-up')
    def _(event):
        """Scroll thinking window up by one line."""
        thinking_window.vertical_scroll = max(0, thinking_window.vertical_scroll - 1)
        event.app.invalidate()

    @kb.add('s-down')
    def _(event):
        """Scroll thinking window down by one line."""
        # Count both spaces and newlines as line indicators
        thinking_text = len(re.findall(r'[\s\n]', state_manager.get_thinking_text()))
        # Use a conservative estimate
        max_scroll = thinking_text/8 if thinking_text else 0
        thinking_window.vertical_scroll = min(thinking_window.vertical_scroll + 1, int(max_scroll))
        event.app.invalidate()

    @kb.add('c-o')
    def _(event):
        """Reset conversation handler and UI state."""
        state_manager.reset_state()
        get_app().invalidate()

    @kb.add('c-space')
    async def _(event):
        """Handle message sending."""
        user_input = msg_buffer.text

        if user_input.strip(): 
            app = application if application else get_app()
            app.layout.focus(chat_formatted_text)
            msg_buffer.text = "AI is busy."

            # Add user message to UI and context
            state_manager.append_user_message(user_input)
            app.invalidate()

            # Generate and add AI response
            ai_answer, ai_thinking = await asyncio.to_thread(handler.generate_chat_response)
            state_manager.append_assistant_message(ai_answer, ai_thinking)
            app.invalidate()
            
            msg_buffer.text = ""
            app.layout.focus(msg_window)

    return kb 