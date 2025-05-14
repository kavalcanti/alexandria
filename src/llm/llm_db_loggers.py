"""Database storage and logging operations."""
import logging
from contextlib import contextmanager
from sqlalchemy import update, select, text
from sqlalchemy.exc import SQLAlchemyError
from src.db.db_config import get_engine, metadata
from src.db.db_init import DatabaseInitializer
from src.db.db_models import conversations_table, messages_table
from src.db.db_utils import DatabaseInputValidator

logger = logging.getLogger(__name__)

class DatabaseStorage:
    def __init__(self):
        """Initialize database storage with connection and schema validation."""
        try:
            self.engine = get_engine()
            self.metadata = metadata
            self.db_schema = self.metadata.schema
            self.validator = DatabaseInputValidator()

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
        try:
            validated_id = self.validator.validate_id(conversation_id)
            select_stmt = select(self.conversations_table).where(
                self.conversations_table.c.id == validated_id
            )

            with self.get_connection() as conn:
                result = conn.execute(select_stmt)
                return result.first() is not None
        except ValueError as e:
            logger.error(f"Invalid conversation ID: {str(e)}")
            return False

    def insert_single_message(self, conversation_id: int, role: str, message: str, token_count: int):
        """
        Insert a single message record into the database.

        Args:
            conversation_id: The ID of the conversation this message belongs to
            role: The role of the message sender
            message: The message content
            token_count: The total token count for this message
            
        Raises:
            ValueError: If any input validation fails
            SQLAlchemyError: If database operation fails
        """
        try:
            # Validate all inputs
            validated_id = self.validator.validate_id(conversation_id)
            validated_role = self.validator.validate_role(role)
            validated_message = self.validator.sanitize_string(message, max_length=8092)  # No limit for message content
            validated_count = self.validator.validate_token_count(token_count)

            insert_stmt = self.messages_table.insert().values(
                conversation_id=validated_id,
                role=validated_role,
                message=validated_message,
                total_token_count=validated_count,
            )

            with self.get_connection() as conn:
                conn.execute(insert_stmt)
                
        except (ValueError, SQLAlchemyError) as e:
            logger.error(f"Failed to insert message: {str(e)}")
            raise

    def insert_single_conversation(self, conversation_id: int, message_count: int = 0, title: str = "", title_embedding: list[float] = None):
        """
        Insert a single conversation record into the database.

        Args:
            conversation_id: The ID for the new conversation
            message_count: Initial message count
            title: The title of the conversation
            title_embedding: Vector embedding for the title
            
        Raises:
            ValueError: If any input validation fails
            SQLAlchemyError: If database operation fails
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

            with self.get_connection() as conn:
                conn.execute(insert_stmt)
                
        except (ValueError, SQLAlchemyError) as e:
            logger.error(f"Failed to insert conversation: {str(e)}")
            raise

    def update_message_count(self, conversation_id: int, new_messages: int = 1):
        """
        Update the message count for a conversation.

        Args:
            conversation_id: The ID of the conversation to update
            new_messages: Number of new messages to add to count
            
        Raises:
            ValueError: If any input validation fails
            SQLAlchemyError: If database operation fails
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

            with self.get_connection() as conn:
                conn.execute(update_stmt)
                
        except (ValueError, SQLAlchemyError) as e:
            logger.error(f"Failed to update message count: {str(e)}")
            raise

    def update_conversation_title(self, conversation_id: int, title: str, title_embedding: list[float] = None):
        """
        Update the title and optionally the title embedding for a conversation.
        The title_embedding parameter is reserved for future implementation of semantic search features.

        Args:
            conversation_id: The ID of the conversation to update
            title: The new title for the conversation
            title_embedding: Optional vector embedding for the title (default: None)
            
        Raises:
            ValueError: If any input validation fails
            SQLAlchemyError: If database operation fails
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

            with self.get_connection() as conn:
                conn.execute(update_stmt)
                
        except (ValueError, SQLAlchemyError) as e:
            logger.error(f"Failed to update conversation title: {str(e)}")
            raise

    def get_context_window_messages(self, conversation_id: int, window_size: int) -> list[dict]:
        """
        Fetch the most recent messages for the context window.
        Only includes messages with roles 'user', 'assistant', and 'system' for the LLM context.
        Messages are ordered by timestamp to maintain conversation sequence.

        Args:
            conversation_id: The ID of the conversation
            window_size: Number of messages to fetch for context window
            
        Returns:
            list[dict]: List of messages in the format {"role": str, "content": str, "timestamp": datetime}
            
        Raises:
            ValueError: If any input validation fails
            SQLAlchemyError: If database operation fails
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
                    self.messages_table.c.role.in_(['user', 'assistant', 'system', 'assistant-reasoning'])
                )
                .order_by(self.messages_table.c.timestamp.desc())
                .limit(validated_size)
            )

            with self.get_connection() as conn:
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

    def get_next_conversation_id(self) -> int:
        """
        Get the next available conversation ID from the sequence.
        
        Returns:
            int: Next available conversation ID
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            with self.get_connection() as conn:
                result = conn.execute(text("SELECT nextval('conversations_id_seq')"))
                return result.scalar()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get next conversation ID: {str(e)}")
            raise