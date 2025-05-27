"""Database storage and logging operations for managing message records."""

from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from src.logger import get_module_logger
from src.infrastructure.db_connector import DatabaseStorage

logger = get_module_logger(__name__) 

class MessagesController:
    def __init__(self, db_storage: DatabaseStorage | None = None) -> None:
        """Initialize the MessagesController.

        Args:
            db_storage (DatabaseStorage | None): Database storage instance. If None, creates a new instance.

        Raises:
            SQLAlchemyError: If database connection fails.
            ValueError: If database validation fails.
        """
        try:
            self.db_storage = db_storage or DatabaseStorage()
            self.validator = self.db_storage.validator

            # Initialize table references directly from imported models
            self.conversations_table = self.db_storage.conversations_table
            self.messages_table = self.db_storage.messages_table

        except (SQLAlchemyError, ValueError) as e:
            logger.error(f"Failed to initialize the context manager: {str(e)}")
            raise

    def insert_single_message(self, conversation_id: int, role: str, message: str, token_count: int) -> None:
        """Insert a single message record into the database.

        Args:
            conversation_id (int): The ID of the conversation this message belongs to.
            role (str): The role of the message sender (e.g., 'user', 'assistant').
            message (str): The message content.
            token_count (int): The total token count for this message.
            
        Raises:
            ValueError: If any input validation fails.
            SQLAlchemyError: If database operation fails.
        """
        try:
            # Validate all inputs
            validated_id = self.validator.validate_id(conversation_id)
            validated_role = self.validator.validate_role(role)
            validated_message = self.validator.sanitize_string(message, max_length=8092)  # No limit for message content
            validated_count = self.validator.validate_token_count(token_count)

            logger.debug(f"Validation successful - Role: {validated_role}, ConvID: {validated_id}")

            insert_stmt = self.messages_table.insert().values(
                conversation_id=validated_id,
                role=validated_role,
                message=validated_message,
                total_token_count=validated_count,
            )

            with self.db_storage.get_connection() as conn:
                result = conn.execute(insert_stmt)
                
        except (ValueError, SQLAlchemyError) as e:
            logger.error(f"Failed to insert message: {str(e)}")
            logger.error(f"Message details - Role: {role}, ConvID: {conversation_id}")
            raise

        return None

    def get_context_window_messages(self, conversation_id: int, window_size: int) -> List[Dict[str, Any]]:
        """Fetch the most recent messages for the context window.

        Only includes messages with roles 'user', 'assistant', and 'system' for the LLM context.
        Messages are ordered by timestamp to maintain conversation sequence.

        Args:
            conversation_id (int): The ID of the conversation.
            window_size (int): Number of messages to fetch for context window.
            
        Returns:
            List[Dict[str, Any]]: List of messages with format:
                {
                    "role": str,
                    "content": str,
                    "timestamp": datetime
                }
            
        Raises:
            ValueError: If any input validation fails.
            SQLAlchemyError: If database operation fails.
        """
        try:
            validated_id = self.validator.validate_id(conversation_id)
            validated_size = self.validator.validate_token_count(window_size)

            # Query to get messages ordered by timestamp
            select_stmt = (
                select(
                    self.messages_table.c.role,
                    self.messages_table.c.message,
                    self.messages_table.c.timestamp
                )
                .where(
                    self.messages_table.c.conversation_id == validated_id,
                    self.messages_table.c.role.in_(['user', 'assistant'])
                )
                .order_by(self.messages_table.c.timestamp.desc())
                .limit(validated_size)
            )

            with self.db_storage.get_connection() as conn:
                result = conn.execute(select_stmt)
                messages = [
                    {
                        'role': row.role,
                        'content': row.message,
                        'timestamp': row.timestamp
                    }
                    for row in result
                ]

                # Reverse the list to get chronological order
                messages.reverse()
                return messages

        except (ValueError, SQLAlchemyError) as e:
            logger.error(f"Failed to fetch context window messages: {str(e)}")
            raise

    def get_reasoning_messages(self, conversation_id: int) -> List[str]:
        """Fetch the thinking messages for the conversation.

        Args:
            conversation_id (int): The ID of the conversation.

        Returns:
            List[str]: List of thinking messages.

        Raises:
            ValueError: If conversation_id validation fails.
            SQLAlchemyError: If database operation fails.
        """
        try:
            validated_id = self.validator.validate_id(conversation_id)
            select_stmt = select(self.messages_table.c.message).where(self.messages_table.c.conversation_id == validated_id, self.messages_table.c.role == 'assistant-reasoning')
            with self.db_storage.get_connection() as conn:
                result = conn.execute(select_stmt)
                return [row.message for row in result]
        except (ValueError, SQLAlchemyError) as e:
            logger.error(f"Failed to fetch thinking messages: {str(e)}")
            raise