"""
Service for the right pane of the UI.

This service handles the management and retrieval of thinking messages displayed in the UI's right pane.
Future features will include support for chained LLM calls.
"""

from typing import List, Dict, Any
from src.llm.controllers.llm_db_msg_controller import MessagesController

class RightPaneService:
    def __init__(self, messages_controller: MessagesController) -> None:
        """
        Initialize the RightPaneService.

        Args:
            messages_controller (MessagesController): Controller for managing message operations.
        """
        self.messages_controller = messages_controller

        return None
        
    def get_thinking_messages(self, conversation_id: int) -> List[Dict[str, Any]]:
        """
        Fetch the thinking messages for a specific conversation.

        Args:
            conversation_id (int): The ID of the conversation to fetch thinking messages for.

        Returns:
            List[Dict[str, Any]]: A list of thinking messages with their associated metadata.
        """
        return self.messages_controller.get_thinking_messages(conversation_id)
    
    