"""Database models and table definitions."""
import datetime
from sqlalchemy import (
    Table,
    Column,
    Text,
    Integer,
    ForeignKey,
    Sequence,
    Index
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, VARCHAR
from pgvector.sqlalchemy import Vector
from src.db.db_config import metadata

# Conversations definition
conversations_table = Table(
    "conversations",
    metadata,
    Column(
        "id",
        Integer,
        Sequence('conversations_id_seq'),
        primary_key=True,
        unique=True,
        nullable=False,
        index=True,
    ),
    Column("title", VARCHAR(256), nullable=True),
    Column(
        "created_at",
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.datetime.now,
        index=True,
    ),
    Column(
        "updated_at",
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
        index=True,
    ),
    Column("message_count", Integer, nullable=False, default=0),
    Column("title_embedding", Vector(384), nullable=True),
)

# Define the 'messages' table
messages_table = Table(
    "messages",
    metadata,
    Column(
        "id",
        Integer,
        Sequence('messages_id_seq'),
        primary_key=True,
        unique=True,
        nullable=False,
        index=True,
    ),
    Column(
        "conversation_id",
        Integer,
        ForeignKey(f"{metadata.schema}.conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "timestamp",
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.datetime.now,
        index=True,
    ),
    Column("role", VARCHAR(24), nullable=False),
    Column("message", Text, nullable=False),
    Column("total_token_count", Integer, nullable=False, default=0),
)

# Add composite index for common queries
Index('idx_conversation_timestamp', 
      messages_table.c.conversation_id, 
      messages_table.c.timestamp)