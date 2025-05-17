import logging
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from src.db.db_config import get_engine, metadata
from src.db.db_init import DatabaseInitializer
from src.db.db_models import conversations_table, messages_table
from src.db.db_utils import DatabaseInputValidator

from src.logger import get_module_logger

logger = get_module_logger(__name__)

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

            logger.info("Database storage initialized successfully")

        except (SQLAlchemyError, ValueError) as e:
            logger.error(f"Failed to initialize database storage: {str(e)}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
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

    def _validate_schema(self):
        """Validate and initialize database schema if needed."""
        try:
            if not self.db_initializer.verify_connection():
                raise SQLAlchemyError("Could not establish database connection")
            
            self.db_initializer.initialize_database()
        except SQLAlchemyError as e:
            logger.error(f"Schema validation failed: {str(e)}")
            raise
