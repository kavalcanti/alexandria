"""
Keyboard bindings for the Alexandria UI.

This module defines keyboard shortcuts and their associated actions for the Alexandria
terminal interface, including navigation, message sending, and application control.
"""
import asyncio
from typing import Optional
from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import ScrollablePane
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.application import Application
from src.logger import get_module_logger

logger = get_module_logger(__name__)

def create_keybindings(
    msg_buffer: Buffer,
    chat_formatted_text: FormattedTextControl,
    thinking_formatted_text: FormattedTextControl,
    chat_window: ScrollablePane,
    thinking_window: ScrollablePane,
    msg_window: Window,
    conversation_manager,
    state_manager,
    application: Optional[Application] = None
    ) -> KeyBindings:
    """
    Create and return keyboard bindings for the Alexandria UI.
    
    Defines the following key bindings:
    - Ctrl+Q: Exit application
    - Ctrl+Up/Down: Scroll chat window
    - Shift+Up/Down: Scroll thinking window
    - Ctrl+O: Reset conversation
    - Ctrl+Space: Send message (with RAG support)
    - Ctrl+S: Save current LLM output
    
    Args:
        msg_buffer: Buffer for message input
        chat_formatted_text: Control for chat display
        thinking_formatted_text: Control for thinking display
        chat_window: Scrollable pane for chat
        thinking_window: Scrollable pane for thinking
        msg_window: Window for message input
        conversation_manager: Manager for conversation state and generation
        state_manager: Manager for UI state
        application: Optional Application instance for focus management
    
    Returns:
        KeyBindings: Object containing all keyboard bindings
    """
    kb = KeyBindings()
 
    @kb.add('c-q')
    def _(event) -> None:
        """
        Exit the application.
        
        Args:
            event: Key press event
            
        Returns:
            None
        """
        event.app.exit()

    @kb.add('c-up')
    def _(event) -> None:
        """
        Scroll chat window up by one line.
        
        Args:
            event: Key press event
            
        Returns:
            None
        """
        chat_window.vertical_scroll = max(0, chat_window.vertical_scroll - 1)
        event.app.invalidate()

    @kb.add('c-down')
    def _(event) -> None:
        """
        Scroll chat window down by one line.
        
        Args:
            event: Key press event
            
        Returns:
            None
        """
        chat_window.vertical_scroll = chat_window.vertical_scroll + 1
        event.app.invalidate()

    @kb.add('s-up')
    def _(event) -> None:
        """
        Scroll thinking window up by one line.
        
        Args:
            event: Key press event
            
        Returns:
            None
        """
        thinking_window.vertical_scroll = max(0, thinking_window.vertical_scroll - 1)
        event.app.invalidate()

    @kb.add('s-down')
    def _(event) -> None:
        """
        Scroll thinking window down by one line.
        
        Args:
            event: Key press event
            
        Returns:
            None
        """
        thinking_window.vertical_scroll = thinking_window.vertical_scroll + 1
        event.app.invalidate()

    @kb.add('c-o')
    def _(event) -> None:
        """
        Reset conversation handler and UI state.
        
        Args:
            event: Key press event
            
        Returns:
            None
        """
        state_manager.reset_state()
        get_app().invalidate()

    @kb.add('c-space')
    async def _(event) -> None:
        """
        Handle message sending and AI response generation with RAG support.
        
        This function:
        1. Gets user input from the message buffer
        2. Updates UI to show AI is processing
        3. Adds user message to conversation
        4. Generates AI response (using RAG if available)
        5. Updates UI with AI response and retrieval info
        6. Resets message buffer and focus
        
        Args:
            event: Key press event
            
        Returns:
            None
        """
        user_input = msg_buffer.text

        if user_input.strip(): 
            app = application if application else get_app()
            app.layout.focus(chat_formatted_text)
            msg_buffer.text = "AI is busy."

            # Add user message to UI and context
            state_manager.append_user_message(user_input)
            app.invalidate()

            # Check if RAG is enabled and use appropriate generation method
            if (hasattr(conversation_manager, 'is_rag_enabled') and 
                conversation_manager.is_rag_enabled and 
                hasattr(conversation_manager, 'generate_rag_response')):
                
                logger.info("Using RAG-enabled response generation")
                # Generate RAG response
                ai_answer, ai_thinking, retrieval_info = await asyncio.to_thread(
                    conversation_manager.generate_rag_response, user_input
                )
                state_manager.append_assistant_message(ai_answer, ai_thinking, retrieval_info)
                
                # Log retrieval info
                if retrieval_info:
                    logger.info(f"RAG retrieved {retrieval_info.get('total_matches', 0)} documents")
                else:
                    logger.info("No documents retrieved for RAG response")
            else:
                logger.info("Using standard response generation")
                # Generate standard response
                ai_answer, ai_thinking = await asyncio.to_thread(conversation_manager.generate_chat_response)
                state_manager.append_assistant_message(ai_answer, ai_thinking)
            
            app.invalidate()
            
            msg_buffer.text = ""
            app.layout.focus(msg_window)

    @kb.add('c-s')
    def _(event) -> None:
        """
        Save the current LLM output to a markdown file.
        
        Args:
            event: Key press event
            
        Returns:
            None
        """
        saved_path = state_manager.save_current_output()
        if saved_path:
            state_manager.save_current_output()
            logger.info(f"Output saved to: {saved_path}")
        else:
            msg_buffer.text = "No LLM output to save"
        event.app.invalidate()

    return kb 