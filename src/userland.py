"""
Main application module for Alexandria.
"""
import asyncio
import os
from dotenv import load_dotenv
from prompt_toolkit.application import Application
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.patch_stdout import patch_stdout

from src.llm.conversation import ConversationHandler
from src.ui.layout import create_layout_components
from src.ui.keybindings import create_keybindings
from src.ui.state_manager import StateManager

load_dotenv()

def create_application(conversation_id=None):
    """
    Create and configure the main application instance.
    
    Args:
        conversation_id: Optional ID of an existing conversation to continue
        
    Returns:
        Application: Configured prompt_toolkit application
    """
    # Create layout components
    (
        root_container,
        msg_buffer,
        chat_formatted_text,
        thinking_formatted_text,
        chat_window,
        thinking_window,
        msg_window
    ) = create_layout_components()

    # Create conversation handler with specified ID or default
    handler = ConversationHandler(
        os.getenv('HF_MODEL'),
        conversation_id=conversation_id  # None by default, which will create a new conversation
    )

    # Create application instance
    app = Application(
        layout=Layout(root_container, focused_element=msg_window),
        key_bindings=None,  # Will be set after creation
        mouse_support=True,
        full_screen=True,
    )

    # Create keybindings with application instance
    kb = create_keybindings(
        msg_buffer,
        chat_formatted_text,
        thinking_formatted_text,
        chat_window,
        thinking_window,
        msg_window,
        handler,
        application=app
    )

    # Set the keybindings
    app.key_bindings = kb

    return app

class Alexandria:
    def __init__(self):
        self._app = None
        
    def create(self, conversation_id=None):
        """Create the application instance with the given conversation ID"""
        self._app = create_application(conversation_id)
        return self
        
    def run(self, conversation_id=None):
        """Run the application with an optional conversation ID"""
        if conversation_id or not self._app:
            self.create(conversation_id)
        self._app.run()

# Create the application instance
application = Alexandria()


