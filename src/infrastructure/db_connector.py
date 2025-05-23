import logging
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import MetaData
from src.db.db_config import get_engine, metadata
from src.db.db_init import DatabaseInitializer
from src.db.db_models import conversations_table, messages_table
from src.db.db_utils import DatabaseInputValidator

from src.logger import get_module_logger

logger = get_module_logger(__name__)

class DatabaseStorage:
    """
    A class to handle database storage operations with connection management and schema validation.
    
    Attributes:
        engine (Engine): SQLAlchemy engine instance for database connections
        metadata (MetaData): Database metadata containing schema information
        db_schema (Optional[str]): Name of the database schema
        validator (DatabaseInputValidator): Validator instance for database inputs
        conversations_table: SQLAlchemy table for conversations
        messages_table: SQLAlchemy table for messages
        db_initializer (DatabaseInitializer): Initializer for database schema
    """
    
    def __init__(self) -> None:
        """
        Initialize database storage with connection and schema validation.
        
        Raises:
            SQLAlchemyError: If database connection or initialization fails
            ValueError: If database configuration is invalid
            
        Returns:
            None
        """
        try:
            self.engine: Engine = get_engine()
            self.metadata: MetaData = metadata
            self.db_schema: Optional[str] = self.metadata.schema
            self.validator: DatabaseInputValidator = DatabaseInputValidator()

            # Initialize table references directly from imported models
            self.conversations_table = conversations_table
            self.messages_table = messages_table

            # Initialize and validate database schema
            self.db_initializer = DatabaseInitializer(self.engine, self.metadata)
            self._validate_schema()

            logger.info("Database storage initialized successfully")

        except (SQLAlchemyError, ValueError) as e:
            logger.error(f"Failed to initialize database storage: {str(e)}")
            raise

    @contextmanager
    def get_connection(self) -> Generator[Connection, None, None]:
        """
        Context manager for handling database connections.
        
        Yields:
            Connection: An active SQLAlchemy database connection
            
        Raises:
            Exception: If any database operation fails
        """
        conn = None
        try:
            logger.debug("Attempting to establish database connection")
            conn = self.engine.connect()
            yield conn
            conn.commit()
        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            if conn:
                logger.info("Rolling back transaction")
                conn.rollback()
            raise
        finally:
            if conn:
                logger.debug("Closing database connection")
                conn.close()

    def _validate_schema(self) -> None:
        """
        Validate and initialize database schema if needed.
        
        Raises:
            SQLAlchemyError: If schema validation or initialization fails
            
        Returns:
            None
        """
        try:
            if not self.db_initializer.verify_connection():
                raise SQLAlchemyError("Could not establish database connection")
            
            self.db_initializer.initialize_database()
        except SQLAlchemyError as e:
            logger.error(f"Schema validation failed: {str(e)}")
            raise
