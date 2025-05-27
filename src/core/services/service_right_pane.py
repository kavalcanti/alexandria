"""
Service for the right pane of the UI.

This service handles the management and retrieval of thinking messages displayed in the UI's right pane.
Future features will include support for chained LLM calls.
"""

from typing import List, Dict, Any
from src.core.memory.llm_db_msg import MessagesController

class RightPaneService:
    def __init__(self, messages_controller: MessagesController, conversation_id: int) -> None:
        """
        Initialize the RightPaneService.

        Args:
            messages_controller (MessagesController): Controller for managing message operations.
            conversation_id (int): The ID of the conversation to fetch reasoning messages for.
        """
        self.messages_controller = messages_controller or MessagesController()

        if conversation_id:
            self.content = self.messages_controller.get_reasoning_messages(conversation_id)
        else:
            self.content = []

        return None
        
    def get_right_pane_content(self) -> List[Dict[str, Any]]:
        """
        Fetch the reasoning messages for a specific conversation.

        Args:
            conversation_id (int): The ID of the conversation to fetch reasoning messages for.

        Returns:
            List[Dict[str, Any]]: A list of reasoning messages with their associated metadata.
        """
        return self.content
    
    def add_content(self, content):
        self.content.append(content)
    
    def get_content(self):
        return self.content
    
    def get_content_length(self):
        return len(self.content)