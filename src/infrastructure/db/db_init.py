import logging
from typing import List, Optional
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import MetaData
from src.logger import get_module_logger

logger = get_module_logger(__name__)

class DatabaseInitializer:
    def __init__(self, engine: Engine, metadata: MetaData):
        """
        Initialize the database manager.
        
        Args:
            engine: SQLAlchemy engine instance
            metadata: SQLAlchemy metadata instance
        """
        self.engine = engine
        self.metadata = metadata
        self.schema = metadata.schema or 'public'
        self.inspector = inspect(engine)

    def ensure_extensions(self) -> None:
        """Ensure required PostgreSQL extensions are installed."""
        required_extensions = ['vector']
        
        try:
            with self.engine.connect() as conn:
                for ext in required_extensions:
                    conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS {ext}"))
                conn.commit()
        except SQLAlchemyError as e:
            logger.error(f"Failed to create extensions: {str(e)}")
            raise

    def ensure_schema(self) -> None:
        """Ensure the database schema exists."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self.schema}"))
                conn.commit()
        except SQLAlchemyError as e:
            logger.error(f"Failed to create schema: {str(e)}")
            raise

    def get_existing_tables(self) -> List[str]:
        """Get list of existing tables in the schema."""
        return self.inspector.get_table_names(schema=self.schema)

    def validate_schema(self, existing_tables: Optional[List[str]] = None) -> bool:
        """
        Validate if all required tables exist with correct structure.
        
        Args:
            existing_tables: Optional list of existing tables (for testing)
            
        Returns:
            bool: True if schema is valid, False if needs initialization
        """
        if existing_tables is None:
            existing_tables = self.get_existing_tables()

        required_tables = {t.name for t in self.metadata.tables.values()}
        existing_table_set = set(existing_tables)

        # Check if all required tables exist
        if not required_tables.issubset(existing_table_set):
            return False

        # For each existing table, validate columns
        for table in self.metadata.tables.values():
            if table.name not in existing_tables:
                continue

            existing_columns = {
                c['name']: c for c in self.inspector.get_columns(table.name, schema=self.schema)
            }
            required_columns = {c.name: c for c in table.columns}

            # Check if all required columns exist
            if not set(required_columns.keys()).issubset(set(existing_columns.keys())):
                return False

        return True

    def initialize_database(self, force: bool = False) -> None:
        """
        Initialize the database schema.
        
        Args:
            force: If True, will drop and recreate all tables
        """
        try:
            # Ensure extensions and schema exist
            self.ensure_extensions()
            self.ensure_schema()

            existing_tables = self.get_existing_tables()
            schema_valid = self.validate_schema(existing_tables)

            if force or not schema_valid:
                logger.warning("Initializing database schema...")
                if force:
                    logger.warning("Force flag set - dropping all tables")
                    self.metadata.drop_all(self.engine)
                self.metadata.create_all(self.engine)
                logger.info("Database schema initialized successfully")
            else:
                logger.info("Database schema is valid")

        except SQLAlchemyError as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise

    def verify_connection(self) -> bool:
        """Verify database connection is working."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection failed: {str(e)}")
            return False 