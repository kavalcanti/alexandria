"""Database storage and logging operations for managing conversations."""
import logging
from typing import Optional, List
from sqlalchemy import update, select, text
from sqlalchemy.exc import SQLAlchemyError
from src.infrastructure.db_connector import DatabaseStorage
from src.logger import get_module_logger

logger = get_module_logger(__name__)

class ConversationsController:
    """Controller for managing conversation records in the database.
    
    This class handles CRUD operations for conversations, including message counting,
    title management, and conversation tracking.
    
    Attributes:
        db_storage (DatabaseStorage): Database connection and storage manager.
        validator: Validator instance for input validation.
        conversations_table: SQLAlchemy table reference for conversations.
        messages_table: SQLAlchemy table reference for messages.
    """

    def __init__(self, db_storage: Optional[DatabaseStorage] = None) -> None:
        """Initialize the conversations controller.

        Args:
            db_storage: Database storage instance. If None, creates a new instance.

        Raises:
            SQLAlchemyError: If database connection fails.
            ValueError: If validation setup fails.
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
        
        return None

    def conversation_exists(self, conversation_id: int) -> bool:
        """Check if a conversation exists in the database.

        Args:
            conversation_id: The ID of the conversation to check.

        Returns:
            True if the conversation exists, False otherwise.

        Raises:
            ValueError: If conversation_id validation fails.
        """
        try:
            validated_id = self.validator.validate_id(conversation_id)
            select_stmt = select(self.conversations_table).where(
                self.conversations_table.c.id == validated_id
            )

            with self.db_storage.get_connection() as conn:
                result = conn.execute(select_stmt)
                return result.first() is not None
        except ValueError as e:
            logger.error(f"Invalid conversation ID: {str(e)}")
            return False

    def insert_single_conversation(
        self, 
        conversation_id: int, 
        message_count: int = 0, 
        title: str = "", 
        title_embedding: Optional[List[float]] = None
    ) -> None:
        """Insert a single conversation record into the database.

        Args:
            conversation_id: The ID for the new conversation.
            message_count: Initial message count. Defaults to 0.
            title: The title of the conversation. Defaults to empty string.
            title_embedding: Vector embedding for the title. Defaults to None.
            
        Raises:
            ValueError: If any input validation fails.
            SQLAlchemyError: If database operation fails.
        """
        try:
            # Validate all inputs
            validated_id = self.validator.validate_id(conversation_id)
            validated_count = self.validator.validate_token_count(message_count)
            validated_title = self.validator.sanitize_string(title)
            validated_embedding = self.validator.validate_vector(title_embedding) if title_embedding else None

            insert_stmt = self.conversations_table.insert().values(
                id=validated_id,
                message_count=validated_count,
                title=validated_title,
                title_embedding=validated_embedding,
            )

            with self.db_storage.get_connection() as conn:
                conn.execute(insert_stmt)
                
        except (ValueError, SQLAlchemyError) as e:
            logger.error(f"Failed to insert conversation: {str(e)}")
            raise

    def update_message_count(self, conversation_id: int, new_messages: int = 1) -> None:
        """Update the message count for a conversation.

        Args:
            conversation_id: The ID of the conversation to update.
            new_messages: Number of new messages to add to count. Defaults to 1.
            
        Raises:
            ValueError: If any input validation fails.
            SQLAlchemyError: If database operation fails.
        """
        try:
            # Validate inputs
            validated_id = self.validator.validate_id(conversation_id)
            validated_count = self.validator.validate_token_count(new_messages)

            update_stmt = (
                update(self.conversations_table)
                .where(self.conversations_table.c.id == validated_id)
                .values(message_count=self.conversations_table.c.message_count + validated_count)
            )

            with self.db_storage.get_connection() as conn:
                conn.execute(update_stmt)
                
        except (ValueError, SQLAlchemyError) as e:
            logger.error(f"Failed to update message count: {str(e)}")
            raise

    def update_conversation_title(
        self, 
        conversation_id: int, 
        title: str, 
        title_embedding: Optional[List[float]] = None
    ) -> None:
        """Update the title and optionally the title embedding for a conversation.

        The title_embedding parameter enables future implementation of semantic search features.

        Args:
            conversation_id: The ID of the conversation to update.
            title: The new title for the conversation.
            title_embedding: Optional vector embedding for the title. Defaults to None.
            
        Raises:
            ValueError: If any input validation fails.
            SQLAlchemyError: If database operation fails.
        """
        try:
            # Validate inputs
            validated_id = self.validator.validate_id(conversation_id)
            validated_title = self.validator.sanitize_string(title)
            
            # Build update values
            update_values = {"title": validated_title}
            if title_embedding is not None:
                validated_embedding = self.validator.validate_vector(title_embedding)
                update_values["title_embedding"] = validated_embedding

            update_stmt = (
                update(self.conversations_table)
                .where(self.conversations_table.c.id == validated_id)
                .values(**update_values)
            )

            with self.db_storage.get_connection() as conn:
                conn.execute(update_stmt)
                
        except (ValueError, SQLAlchemyError) as e:
            logger.error(f"Failed to update conversation title: {str(e)}")
            raise

    def get_next_conversation_id(self) -> int:
        """Get the next available conversation ID from the sequence.
        
        Returns:
            Next available conversation ID.
            
        Raises:
            SQLAlchemyError: If database operation fails.
        """
        try:
            with self.db_storage.get_connection() as conn:
                result = conn.execute(text("SELECT nextval('conversations_id_seq')"))
                return result.scalar()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get next conversation ID: {str(e)}")
            raise