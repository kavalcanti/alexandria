"""Database storage and logging operations."""
import logging
from contextlib import contextmanager
from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError
from src.db.db_config import get_engine, metadata
from src.db.db_init import DatabaseInitializer
from src.db.db_models import conversations_table, messages_table

logger = logging.getLogger(__name__)

class DatabaseStorage:
    def __init__(self):
        """Initialize database storage with connection and schema validation."""
        try:
            self.engine = get_engine()
            self.metadata = metadata
            self.db_schema = self.metadata.schema

            # Initialize table references directly from imported models
            self.conversations_table = conversations_table
            self.messages_table = messages_table

            # Initialize and validate database schema
            self.db_initializer = DatabaseInitializer(self.engine, self.metadata)
            self._validate_schema()

        except (SQLAlchemyError, ValueError) as e:
            logger.error(f"Failed to initialize database storage: {str(e)}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = self.engine.connect()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _validate_schema(self):
        """Validate and initialize database schema if needed."""
        try:
            if not self.db_initializer.verify_connection():
                raise SQLAlchemyError("Could not establish database connection")
            
            self.db_initializer.initialize_database()
        except SQLAlchemyError as e:
            logger.error(f"Schema validation failed: {str(e)}")
            raise

    def conversation_exists(self, conversation_id: int) -> bool:
        """
        Check if a conversation exists in the database.

        Args:
            conversation_id: The ID of the conversation to check.

        Returns:
            bool: True if the conversation exists, False otherwise.
        """
        select_stmt = select(self.conversations_table).where(
            self.conversations_table.c.id == conversation_id
        )

        with self.get_connection() as conn:
            result = conn.execute(select_stmt)
            return result.first() is not None

    def insert_single_message(self, conversation_id: int, role: str, message: str, token_count: int):
        """
        Insert a single message record into the database.

        Args:
            conversation_id: The ID of the conversation this message belongs to
            role: The role of the message sender
            message: The message content
            token_count: The total token count for this message
        """
        insert_stmt = self.messages_table.insert().values(
            conversation_id=conversation_id,
            role=role,
            message=message,
            total_token_count=token_count,
        )

        with self.get_connection() as conn:
            conn.execute(insert_stmt)

    def insert_single_conversation(self, conversation_id: int, message_count: int = 0, title: str = "", title_embedding: list[float] = None):
        """
        Insert a single conversation record into the database.

        Args:
            conversation_id: The ID for the new conversation
            message_count: Initial message count
            title: The title of the conversation
            title_embedding: Vector embedding for the title
        """
        insert_stmt = self.conversations_table.insert().values(
            id=conversation_id,
            message_count=message_count,
            title=title,
            title_embedding=title_embedding,
        )

        with self.get_connection() as conn:
            conn.execute(insert_stmt)

    def update_message_count(self, conversation_id: int, new_messages: int = 1):
        """
        Update the message count for a conversation.

        Args:
            conversation_id: The ID of the conversation to update
        """
        update_stmt = (
            update(self.conversations_table)
            .where(self.conversations_table.c.id == conversation_id)
            .values(message_count=self.conversations_table.c.message_count + new_messages)
        )

        with self.get_connection() as conn:
            conn.execute(update_stmt)