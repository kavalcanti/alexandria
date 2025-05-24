"""Database models and table definitions."""
import datetime
from sqlalchemy import (
    Table,
    Column,
    Text,
    Integer,
    ForeignKey,
    Sequence,
    Index,
    DateTime,
    String,
    Float
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, VARCHAR, JSONB
from pgvector.sqlalchemy import Vector
from src.infrastructure.db.db_config import metadata

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

# Documents table for storing document metadata
documents_table = Table(
    "documents",
    metadata,
    Column(
        "id",
        Integer,
        Sequence('documents_id_seq'),
        primary_key=True,
        unique=True,
        nullable=False,
        index=True,
    ),
    Column("filename", VARCHAR(512), nullable=False),
    Column("filepath", Text, nullable=False),
    Column("file_hash", VARCHAR(64), nullable=False, unique=True, index=True),
    Column("file_size", Integer, nullable=False),
    Column("mime_type", VARCHAR(128), nullable=True),
    Column("content_type", VARCHAR(64), nullable=True),  # text, pdf, markdown, etc.
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
    Column(
        "last_modified",
        TIMESTAMP(timezone=True),
        nullable=True,
        index=True,
    ),
    Column("metadata", JSONB, nullable=True),  # Store additional file metadata
    Column("status", VARCHAR(32), nullable=False, default="pending"),  # pending, processed, failed
    Column("chunk_count", Integer, nullable=False, default=0),
)

# Document chunks table for storing processed text chunks with embeddings
document_chunks_table = Table(
    "document_chunks",
    metadata,
    Column(
        "id",
        Integer,
        Sequence('document_chunks_id_seq'),
        primary_key=True,
        unique=True,
        nullable=False,
        index=True,
    ),
    Column(
        "document_id",
        Integer,
        ForeignKey(f"{metadata.schema}.documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("chunk_index", Integer, nullable=False),  # Order within document
    Column("content", Text, nullable=False),
    Column("content_hash", VARCHAR(64), nullable=False, index=True),
    Column("token_count", Integer, nullable=True),
    Column("char_count", Integer, nullable=False),
    Column("embedding", Vector(384), nullable=True, index=True),  # Vector index for similarity search
    Column(
        "created_at",
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.datetime.now,
        index=True,
    ),
    Column("metadata", JSONB, nullable=True),  # Store chunk-specific metadata (page numbers, headers, etc.)
)

# Add composite index for common queries
Index('idx_conversation_timestamp', 
      messages_table.c.conversation_id, 
      messages_table.c.timestamp)

# Add indices for document queries
Index('idx_documents_status_created', 
      documents_table.c.status, 
      documents_table.c.created_at)

Index('idx_chunks_document_index', 
      document_chunks_table.c.document_id, 
      document_chunks_table.c.chunk_index)

# Create a unique constraint on document_id + chunk_index
Index('idx_unique_document_chunk', 
      document_chunks_table.c.document_id, 
      document_chunks_table.c.chunk_index, 
      unique=True)