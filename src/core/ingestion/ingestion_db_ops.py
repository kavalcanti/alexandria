"""Database operations for the document ingestion pipeline."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy import select, insert, update, and_, or_
from sqlalchemy.exc import IntegrityError
from pgvector import Vector

from src.logger import get_module_logger
from src.infrastructure.db_connector import DatabaseStorage
from src.infrastructure.db.db_models import documents_table, document_chunks_table
from src.infrastructure.embedder import Embedder
from src.core.ingestion.models import TextChunk

logger = get_module_logger(__name__)

class IngestionDatabaseOps:
    """Handles all database operations for the document ingestion pipeline."""
    
    def __init__(self):
        """Initialize database connection and embedder."""
        self.db_storage = DatabaseStorage()
        self.embedder = Embedder()
    
    def get_existing_document(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Check if a document with the given hash already exists.
        
        Args:
            file_hash: SHA-256 hash of the file content
            
        Returns:
            Document record if exists, None otherwise
        """
        with self.db_storage.get_connection() as conn:
            result = conn.execute(
                select(documents_table).where(
                    documents_table.c.file_hash == file_hash
                )
            ).first()
            
            return dict(result) if result else None
    
    def create_document_record(self, file_metadata: Dict[str, Any]) -> int:
        """
        Create a new document record in the database.
        
        Args:
            file_metadata: Dictionary containing document metadata
            
        Returns:
            ID of the created document record
        """
        try:
            with self.db_storage.get_connection() as conn:
                result = conn.execute(
                    insert(documents_table).values(
                        filename=file_metadata['filename'],
                        filepath=file_metadata['filepath'],
                        file_hash=file_metadata['file_hash'],
                        file_size=file_metadata['file_size'],
                        mime_type=file_metadata['mime_type'],
                        content_type=file_metadata['content_type'],
                        last_modified=file_metadata['last_modified'],
                        status='processing',
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                )
                doc_id = result.inserted_primary_key[0]
                logger.debug(f"Created document record with ID: {doc_id}")
                return doc_id
                
        except IntegrityError as e:
            logger.error(f"Database integrity error creating document record: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating document record: {str(e)}")
            raise
    
    def store_chunks_with_embeddings(
        self, 
        doc_id: int, 
        chunks: List[TextChunk], 
        start_index: int = 0
    ) -> int:
        """
        Store text chunks with their embeddings in the database.
        
        Args:
            doc_id: ID of the parent document
            chunks: List of TextChunk objects to store
            start_index: Starting index for chunk numbering
            
        Returns:
            Number of chunks stored
        """
        try:
            with self.db_storage.get_connection() as conn:
                chunk_records = []
                for idx, chunk in enumerate(chunks, start=start_index):
                    try:
                        # Generate embedding for the chunk
                        embedding = self.embedder.embed(chunk.content)
                        
                        # Validate metadata
                        metadata = chunk.metadata if chunk.metadata is not None else {}
                        if not isinstance(metadata, dict):
                            logger.warning(f"Invalid metadata type: {type(metadata)}, using empty dict")
                            metadata = {}
                        
                        chunk_record = {
                            'document_id': doc_id,
                            'chunk_index': idx,
                            'content': chunk.content,
                            'content_hash': chunk.content_hash,
                            'char_count': chunk.char_count,
                            'token_count': chunk.token_count,
                            'embedding': embedding,  # pgvector.Vector object is used directly
                            'metadata': metadata,
                            'created_at': datetime.now()
                        }
                        chunk_records.append(chunk_record)
                        
                    except Exception as chunk_e:
                        logger.error(f"Error processing chunk {idx}: {str(chunk_e)}")
                        continue
                
                if chunk_records:
                    try:
                        conn.execute(
                            insert(document_chunks_table),
                            chunk_records
                        )
                        logger.debug(f"Stored {len(chunk_records)} chunks for document {doc_id}")
                        return len(chunk_records)
                    except Exception as insert_e:
                        logger.error(f"Error inserting chunks: {str(insert_e)}")
                        # Log the first chunk record for debugging
                        if chunk_records:
                            first_record = dict(chunk_records[0])
                            first_record['embedding'] = f"<Vector({len(first_record['embedding'])} dimensions)>"
                            logger.error(f"First chunk record: {first_record}")
                        raise
                return 0
                
        except Exception as e:
            logger.error(f"Error storing chunks with embeddings: {str(e)}")
            raise
    
    def update_document_status(self, doc_id: int, status: str, chunk_count: int = None):
        """
        Update the status and chunk count of a document.
        
        Args:
            doc_id: ID of the document to update
            status: New status value
            chunk_count: Optional number of chunks processed
        """
        try:
            with self.db_storage.get_connection() as conn:
                update_values = {
                    'status': status,
                    'updated_at': datetime.now()
                }
                if chunk_count is not None:
                    update_values['chunk_count'] = chunk_count
                
                conn.execute(
                    update(documents_table)
                    .where(documents_table.c.id == doc_id)
                    .values(**update_values)
                )
                logger.debug(f"Updated document {doc_id} status to {status}")
                
        except Exception as e:
            logger.error(f"Error updating document status: {str(e)}")
            raise
    
    def delete_document_record(self, doc_id: int):
        """
        Delete a document and its chunks from the database.
        
        Args:
            doc_id: ID of the document to delete
        """
        try:
            with self.db_storage.get_connection() as conn:
                # Delete chunks first due to foreign key constraint
                conn.execute(
                    document_chunks_table.delete().where(
                        document_chunks_table.c.document_id == doc_id
                    )
                )
                
                # Delete document record
                conn.execute(
                    documents_table.delete().where(
                        documents_table.c.id == doc_id
                    )
                )
                logger.debug(f"Deleted document {doc_id} and its chunks")
                
        except Exception as e:
            logger.error(f"Error deleting document record: {str(e)}")
            raise
    
    def get_document_chunk_count(self, doc_id: int) -> int:
        """
        Get the number of chunks for a document.
        
        Args:
            doc_id: ID of the document
            
        Returns:
            Number of chunks
        """
        with self.db_storage.get_connection() as conn:
            result = conn.execute(
                select([document_chunks_table])
                .where(document_chunks_table.c.document_id == doc_id)
                .count()
            ).scalar()
            return result or 0 