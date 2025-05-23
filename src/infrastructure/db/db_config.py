"""Database configuration and connection management."""
import os
from typing import Optional
from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from src.logger import get_module_logger

logger = get_module_logger(__name__)

def get_db_url() -> str:
    """Get database URL from environment variables."""
    required_vars = {
        'DB_USER': os.getenv('DB_USER'),
        'DB_HOST': os.getenv('DB_HOST'),
        'DB_PASS': os.getenv('DB_PASS'),
        'DATABASE': os.getenv('DATABASE')
    }

    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    return f"postgresql+psycopg2://{required_vars['DB_USER']}:{required_vars['DB_PASS']}@{required_vars['DB_HOST']}/{required_vars['DATABASE']}"

def create_db_engine(pool_size: int = 5, max_overflow: int = 10, pool_timeout: int = 30) -> Engine:
    """
    Create a database engine with connection pooling.
    
    Args:
        pool_size: The number of connections to keep open in the pool
        max_overflow: How many connections above pool_size we can temporarily exceed
        pool_timeout: How many seconds to wait before giving up on getting a connection
    
    Returns:
        SQLAlchemy Engine instance
    """
    return create_engine(
        get_db_url(),
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_pre_ping=True  # Verify connections before using them
    )

# Create shared metadata instance
metadata = MetaData(schema='exp')

# Create shared engine instance
engine: Optional[Engine] = None

def get_engine() -> Engine:
    """Get or create the database engine singleton."""
    global engine
    if engine is None:
        engine = create_db_engine()
    return engine 