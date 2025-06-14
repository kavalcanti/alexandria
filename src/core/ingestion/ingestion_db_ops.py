"""Database operations for the document ingestion pipeline."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy import select, insert, update, and_, or_, func
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
        try:
            with self.db_storage.get_connection() as conn:
                result = conn.execute(
                    select(documents_table).where(
                        documents_table.c.file_hash == file_hash
                    )
                ).first()
                
                return dict(result._mapping) if result else None
                
        except Exception as e:
            logger.error(f"Error checking existing document: {str(e)}")
            return None

    def get_document_chunk_count(self, doc_id: int) -> int:
        """Get the number of chunks for a document."""
        try:
            with self.db_storage.get_connection() as conn:
                result = conn.execute(
                    select(func.count(document_chunks_table.c.id))
                    .where(document_chunks_table.c.document_id == doc_id)
                ).scalar()
                return result or 0
        except Exception as e:
            logger.error(f"Error getting document chunk count: {str(e)}")
            return 0
    
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
                        metadata={'extension': file_metadata.get('extension', '')},
                        status='processing',
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                )
                doc_id = result.inserted_primary_key[0]
                conn.commit()
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
                            'embedding': embedding,
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
                        conn.commit()
                        logger.debug(f"Stored {len(chunk_records)} chunks for document {doc_id}")
                        return len(chunk_records)
                    except Exception as insert_e:
                        logger.error(f"Error inserting chunks: {str(insert_e)}")
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
                conn.commit()
                logger.debug(f"Updated document {doc_id} status to {status}")
                
        except Exception as e:
            logger.error(f"Error updating document status: {str(e)}")
            raise
    
    def delete_document_record(self, file_hash: str) -> bool:
        """
        Delete a document and its chunks from the database.
        
        Args:
            file_hash: SHA-256 hash of the file to delete
            
        Returns:
            True if document was deleted, False otherwise
        """
        try:
            with self.db_storage.get_connection() as conn:
                # Get document ID first
                doc = self.get_existing_document(file_hash)
                if not doc:
                    logger.warning(f"No document found with hash {file_hash}")
                    return False
                
                # Delete chunks first (should be handled by CASCADE, but be explicit)
                conn.execute(
                    document_chunks_table.delete().where(
                        document_chunks_table.c.document_id == doc['id']
                    )
                )
                
                # Delete document record
                result = conn.execute(
                    documents_table.delete().where(
                        documents_table.c.file_hash == file_hash
                    )
                )
                
                if result.rowcount > 0:
                    conn.commit()
                    logger.info(f"Deleted document with hash {file_hash}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document record: {str(e)}")
            return False

    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get statistics about ingested documents."""
        try:
            with self.db_storage.get_connection() as conn:
                # Count documents by status
                doc_stats_query = select(
                    documents_table.c.status,
                    func.count(documents_table.c.id).label('count')
                ).group_by(documents_table.c.status)
                
                doc_stats = conn.execute(doc_stats_query).fetchall()
                
                # Count total chunks
                chunk_count_query = select(func.count(document_chunks_table.c.id).label('total_chunks'))
                chunk_count = conn.execute(chunk_count_query).scalar()
                
                # Count documents by content type
                content_type_query = select(
                    documents_table.c.content_type,
                    func.count(documents_table.c.id).label('count')
                ).group_by(documents_table.c.content_type)
                
                content_type_stats = conn.execute(content_type_query).fetchall()
                
                return {
                    'document_stats': {row.status: row.count for row in doc_stats},
                    'total_chunks': chunk_count or 0,
                    'content_type_stats': {row.content_type: row.count for row in content_type_stats}
                }
                
        except Exception as e:
            logger.error(f"Error getting ingestion stats: {str(e)}")
            return {
                'document_stats': {},
                'total_chunks': 0,
                'content_type_stats': {},
                'error': str(e)
            } 