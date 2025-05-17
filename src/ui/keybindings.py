"""
Keyboard bindings for the Alexandria UI.
"""
import asyncio
from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding import KeyBindings

def create_keybindings(
    msg_buffer,
    chat_formatted_text,
    thinking_formatted_text,
    chat_window,
    thinking_window,
    msg_window,
    conversation_manager,
    state_manager,
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
        conversation_manager: ConversationManager instance
        application: Optional Application instance for focus management
    
    Returns:
        KeyBindings object with all necessary bindings
    """
    kb = KeyBindings()
 
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
        chat_window.vertical_scroll = chat_window.vertical_scroll + 1
        event.app.invalidate()

    @kb.add('s-up')
    def _(event):
        """Scroll thinking window up by one line."""
        thinking_window.vertical_scroll = max(0, thinking_window.vertical_scroll - 1)
        event.app.invalidate()

    @kb.add('s-down')
    def _(event):
        """Scroll thinking window down by one line."""
        thinking_window.vertical_scroll = thinking_window.vertical_scroll + 1
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
            ai_answer, ai_thinking = await asyncio.to_thread(conversation_manager.generate_chat_response)
            state_manager.append_assistant_message(ai_answer, ai_thinking)
            app.invalidate()
            
            msg_buffer.text = ""
            app.layout.focus(msg_window)

    return kb 