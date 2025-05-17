"""
Service for the right pane of the UI.

Handles the display of the thinking messages. Future features will include chained llm calls.
"""

from src.llm.controllers.llm_db_msg_controller import MessagesController

class RightPaneService:
    def __init__(self, messages_controller: MessagesController):
        self.messages_controller = messages_controller
        
    def get_thinking_messages(self, conversation_id: int) -> list[dict]:
        """
        Fetch the thinking messages for the conversation.
        """
        return self.messages_controller.get_thinking_messages(conversation_id)
    
    