"""
Main application module for Alexandria.
"""
import asyncio
import os
from dotenv import load_dotenv
from prompt_toolkit.application import Application
from prompt_toolkit.layout.layout import Layout
from src.core.services.conversation_service import create_conversation_service
from src.ui.layout import create_layout_components
from src.ui.keybindings import create_keybindings
from src.ui.state_manager import StateManager

load_dotenv()

def create_application(conversation_id=None, enable_rag=True, rag_config=None):
    """
    Create and configure the main application instance.
    
    Args:
        conversation_id: Optional ID of an existing conversation to continue
        enable_rag: Whether to enable RAG capabilities (default: True)
        rag_config: Optional RAG configuration settings
        
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
        msg_window,
        style
    ) = create_layout_components()


    conversation_service = create_conversation_service(
        conversation_id=conversation_id
    )

    state_manager = StateManager(
        chat_formatted_text,
        thinking_formatted_text,
        conversation_service,
        rag_config=rag_config
    )

    # Create application instance
    app = Application(
        layout=Layout(root_container, focused_element=msg_window),
        key_bindings=None,  # Will be set after creation
        mouse_support=True,
        full_screen=True,
        style=style,  # Add the style
    )

    # Create keybindings with application instance
    kb = create_keybindings(
        msg_buffer,
        chat_formatted_text,
        thinking_formatted_text,
        chat_window,
        thinking_window,
        msg_window,
        conversation_service,
        state_manager,
        application=app
    )

    # Set the keybindings
    app.key_bindings = kb

    return app

class Alexandria:
    def __init__(self):
        self._app = None
        self.enable_rag = True
        self.rag_config = None
        
    def configure_rag(self, enable_rag=True, rag_config=None):
        """Configure RAG settings for the application"""
        self.enable_rag = enable_rag
        self.rag_config = rag_config
        return self
        
    def create(self, conversation_id=None):
        """Create the application instance with the given conversation ID"""
        self._app = create_application(
            conversation_id, 
            enable_rag=self.enable_rag, 
            rag_config=self.rag_config
        )
        return self
        
    def run(self, conversation_id=None):
        """Run the application with an optional conversation ID"""
        if conversation_id or not self._app:
            self.create(conversation_id)
        self._app.run()

# Create the application instance
application = Alexandria()


