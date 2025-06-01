"""Main document ingestion service for RAG implementation."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select, insert, update, and_, or_
from sqlalchemy.exc import IntegrityError

from src.logger import get_module_logger
from src.configs import IngestionConfig
from src.infrastructure.db_connector import DatabaseStorage
from src.infrastructure.db.db_models import documents_table, document_chunks_table
from src.infrastructure.embedder import Embedder
from src.core.ingestion.document_processor import DocumentProcessor
from src.core.ingestion.text_chunker import TextChunker, TextChunk
from src.core.ingestion.file_chunker import FileChunker
from src.core.ingestion.models import IngestionResult

logger = get_module_logger(__name__)

class DocumentIngestor:
    """Main service for ingesting documents into the RAG system."""
    
    def __init__(self, config: Optional[IngestionConfig] = None):
        """Initialize the document ingestor."""
        self.config = config or IngestionConfig()
        self.db_storage = DatabaseStorage()
        self.embedder = Embedder()
        self.document_processor = DocumentProcessor()
        self.text_chunker = TextChunker(self.config.chunk_config)
        self.file_chunker = FileChunker(self.config.file_chunk_config) if self.config.enable_large_file_chunking else None
        
        logger.info("Document ingestor initialized")
    
    def ingest_directory(self, directory_path: Union[str, Path], recursive: bool = True) -> IngestionResult:
        """
        Ingest all supported documents from a directory.
        
        Args:
            directory_path: Path to directory containing documents
            recursive: Whether to search subdirectories recursively
            
        Returns:
            IngestionResult with processing statistics
        """
        directory_path = Path(directory_path)
        result = IngestionResult()
        
        try:
            logger.info(f"Starting ingestion of directory: {directory_path}")
            
            # Scan for supported files
            supported_files = self.document_processor.scan_directory(directory_path, recursive)
            result.total_files = len(supported_files)
            
            if not supported_files:
                logger.warning(f"No supported files found in {directory_path}")
                return result
            
            # Process files sequentially (simplified approach)
            for file_path in supported_files:
                try:
                    file_result = self._process_single_file(file_path)
                    self._aggregate_file_result(result, file_result, file_path)
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt received, stopping ingestion...")
                    result.errors.append("Ingestion interrupted by user")
                    break
                except Exception as e:
                    error_msg = f"Error processing {file_path}: {str(e)}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)
                    result.failed_files += 1
            
            logger.info(
                f"Ingestion completed: {result.processed_files} processed, "
                f"{result.skipped_files} skipped, {result.failed_files} failed, "
                f"{result.total_chunks} chunks created"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error during directory ingestion: {str(e)}")
            result.errors.append(f"Directory ingestion error: {str(e)}")
            return result
    
    def ingest_file(self, file_path: Union[str, Path]) -> IngestionResult:
        """
        Ingest a single document file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            IngestionResult with processing statistics
        """
        file_path = Path(file_path)
        result = IngestionResult(total_files=1)
        
        try:
            if not file_path.exists():
                error_msg = f"File does not exist: {file_path}"
                logger.error(error_msg)
                result.errors.append(error_msg)
                result.failed_files = 1
                return result
            
            # Process the file
            file_result = self._process_single_file(file_path)
            self._aggregate_file_result(result, file_result, file_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error ingesting file {file_path}: {str(e)}")
            result.errors.append(f"File ingestion error: {str(e)}")
            result.failed_files = 1
            return result
    
    def _aggregate_file_result(self, batch_result: IngestionResult, file_result: Dict[str, Any], file_path: Path):
        """Aggregate individual file result into batch result."""
        if file_result['success']:
            if file_result['skipped']:
                batch_result.skipped_files += 1
            else:
                batch_result.processed_files += 1
                batch_result.total_chunks += file_result['chunk_count']
        else:
            batch_result.failed_files += 1
            batch_result.errors.append(f"{file_path}: {file_result['error']}")
    
    def _process_single_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Process a single file through the entire ingestion pipeline.
        
        Returns:
            Dictionary with success status, chunk count, and error information
        """
        try:
            # Extract file metadata
            file_metadata = self.document_processor.get_file_metadata(file_path)
            
            # Check if file already exists and should be skipped
            if self.config.skip_existing:
                existing_doc = self._get_existing_document(file_metadata['file_hash'])
                if existing_doc:
                    # Check if the document has any chunk records
                    with self.db_storage.get_connection() as conn:
                        from src.infrastructure.db.db_models import document_chunks_table
                        chunk_count = conn.execute(
                            select(document_chunks_table.c.id).where(
                                document_chunks_table.c.document_id == existing_doc['id']
                            )
                        ).fetchone()
                    if chunk_count:
                        if not self.config.update_existing:
                            logger.debug(f"Skipping existing file: {file_path}")
                            return {'success': True, 'skipped': True, 'chunk_count': 0}
                        elif existing_doc['last_modified'] >= file_metadata['last_modified']:
                            logger.debug(f"Skipping unchanged file: {file_path}")
                            return {'success': True, 'skipped': True, 'chunk_count': 0}
            
            # Check if the file needs to be chunked at file level first
            if (self.file_chunker is not None and 
                self.file_chunker.should_chunk_file(file_path)):
                
                return self._process_large_file(file_path, file_metadata)
            else:
                return self._process_regular_file(file_path, file_metadata)
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': str(e)}
    
    def _process_regular_file(self, file_path: Path, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a regular-sized file."""
        try:
            # Extract text content
            text_content = self.document_processor.extract_text_content(file_path)
            
            if not text_content.strip():
                logger.warning(f"No text content extracted from {file_path}")
                return {'success': False, 'error': 'No text content extracted'}
            
            # Chunk the text
            chunks = self.text_chunker.chunk_text(text_content, file_metadata['content_type'])
            
            if not chunks:
                logger.warning(f"No chunks created from {file_path}")
                return {'success': False, 'error': 'No chunks created'}
            
            # Store document and chunks in database
            self._store_document_and_chunks(file_metadata, chunks)
            
            logger.debug(f"Successfully processed {file_path}: {len(chunks)} chunks")
            return {'success': True, 'skipped': False, 'chunk_count': len(chunks)}
            
        except Exception as e:
            logger.error(f"Error processing regular file {file_path}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _process_large_file(self, file_path: Path, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a large file by chunking it first."""
        total_chunks = 0
        doc_id = None
        
        try:
            # Create file chunks
            file_chunks = self.file_chunker.chunk_file(file_path)
            
            if not file_chunks:
                # Fall back to regular processing
                return self._process_regular_file(file_path, file_metadata)
            
            logger.info(f"Processing {len(file_chunks)} file chunks for {file_path}")
            
            # Create document record first
            doc_id = self._create_document_record(file_metadata)
            
            # Process each file chunk separately
            for chunk_idx, file_chunk in enumerate(file_chunks):
                try:
                    logger.info(f"Processing file chunk {chunk_idx + 1}/{len(file_chunks)} (ID: {file_chunk.chunk_id})")
                    
                    # Extract text content from the chunk file
                    chunk_text = self.document_processor.extract_text_content(file_chunk.temp_file_path)
                    
                    if chunk_text.strip():
                        # Create text chunks from this file chunk
                        text_chunks = self.text_chunker.chunk_text(chunk_text, file_metadata['content_type'])
                        
                        # Add metadata about the file chunk to each text chunk
                        for chunk in text_chunks:
                            chunk.metadata.update({
                                'file_chunk_id': file_chunk.chunk_id,
                                'file_chunk_index': file_chunk.chunk_index,
                                'original_file_size': file_metadata['file_size']
                            })
                            
                            # Add section metadata for markdown chunks
                            if file_chunk.metadata:
                                chunk.metadata.update(file_chunk.metadata)
                        
                        # Process and save this batch of chunks
                        batch_count = self._save_chunks_batch(doc_id, text_chunks, total_chunks)
                        total_chunks += batch_count
                        
                        logger.info(f"Saved {batch_count} chunks from file chunk {chunk_idx + 1}. Total: {total_chunks}")
                        
                except Exception as e:
                    logger.error(f"Error processing file chunk {file_chunk.chunk_id}: {str(e)}")
                    continue
            
            # Clean up temporary files
            if self.file_chunker:
                self.file_chunker.cleanup_temp_files()
            
            if total_chunks == 0:
                if doc_id:
                    self._delete_document_record(doc_id)
                return {'success': False, 'error': 'No chunks were created from large file'}
            
            # Update document status
            self._update_document_status(doc_id, 'completed', total_chunks)
            
            logger.info(f"Successfully processed large file {file_path}: {total_chunks} chunks")
            return {'success': True, 'skipped': False, 'chunk_count': total_chunks}
            
        except Exception as e:
            # Clean up on error
            if self.file_chunker:
                self.file_chunker.cleanup_temp_files()
            if doc_id:
                self._delete_document_record(doc_id)
            logger.error(f"Error processing large file {file_path}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _create_document_record(self, file_metadata: Dict[str, Any]) -> int:
        """Create a document record and return its ID."""
        try:
            with self.db_storage.get_connection() as conn:
                insert_query = insert(documents_table).values(
                    filename=file_metadata['filename'],
                    filepath=file_metadata['filepath'],
                    file_hash=file_metadata['file_hash'],
                    file_size=file_metadata['file_size'],
                    mime_type=file_metadata['mime_type'],
                    content_type=file_metadata['content_type'],
                    last_modified=file_metadata['last_modified'],
                    metadata={'extension': file_metadata['extension']},
                    status='processing',
                    chunk_count=0
                )
                
                result = conn.execute(insert_query)
                doc_id = result.inserted_primary_key[0]
                conn.commit()
                return doc_id
                
        except Exception as e:
            logger.error(f"Error creating document record: {str(e)}")
            raise
    
    def _save_chunks_batch(self, doc_id: int, chunks: List, start_index: int) -> int:
        """Save a batch of chunks to the database and return count saved."""
        try:
            with self.db_storage.get_connection() as conn:
                chunk_records = []
                
                for i, chunk in enumerate(chunks):
                    try:
                        # Generate embedding for the chunk
                        embedding = self.embedder.embed(chunk.content)
                        
                        # Estimate token count
                        token_count = self.text_chunker.estimate_token_count(chunk.content)
                        
                        chunk_record = {
                            'document_id': doc_id,
                            'chunk_index': start_index + i,
                            'content': chunk.content,
                            'content_hash': chunk.content_hash,
                            'token_count': token_count,
                            'char_count': chunk.char_count,
                            'embedding': embedding.tolist(),  # Convert numpy array to list
                            'metadata': chunk.metadata
                        }
                        
                        chunk_records.append(chunk_record)
                        
                    except Exception as e:
                        logger.error(f"Error processing chunk {start_index + i}: {str(e)}")
                        continue
                
                if chunk_records:
                    # Batch insert chunks
                    insert_chunks_query = insert(document_chunks_table)
                    conn.execute(insert_chunks_query, chunk_records)
                    conn.commit()
                    return len(chunk_records)
                
                return 0
                
        except Exception as e:
            logger.error(f"Error saving chunks batch: {str(e)}")
            raise
    
    def _update_document_status(self, doc_id: int, status: str, chunk_count: int):
        """Update document status and chunk count."""
        try:
            with self.db_storage.get_connection() as conn:
                update_query = update(documents_table).where(
                    documents_table.c.id == doc_id
                ).values(
                    status=status,
                    chunk_count=chunk_count,
                    updated_at=datetime.now()
                )
                conn.execute(update_query)
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating document status: {str(e)}")
            raise
    
    def _delete_document_record(self, doc_id: int):
        """Delete a document record and its chunks."""
        try:
            with self.db_storage.get_connection() as conn:
                # Delete chunks first (should be handled by CASCADE, but be explicit)
                delete_chunks_query = document_chunks_table.delete().where(
                    document_chunks_table.c.document_id == doc_id
                )
                conn.execute(delete_chunks_query)
                
                # Delete document
                delete_doc_query = documents_table.delete().where(
                    documents_table.c.id == doc_id
                )
                conn.execute(delete_doc_query)
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error deleting document record: {str(e)}")
            # Don't raise here as this is cleanup
    
    def _get_existing_document(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Check if a document with the given hash already exists."""
        try:
            with self.db_storage.get_connection() as conn:
                query = select(documents_table).where(documents_table.c.file_hash == file_hash)
                result = conn.execute(query).fetchone()
                
                if result:
                    return dict(result._mapping)
                return None
                
        except Exception as e:
            logger.error(f"Error checking existing document: {str(e)}")
            return None
    
    def _store_document_and_chunks(self, file_metadata: Dict[str, Any], chunks: List[TextChunk]):
        """Store document metadata and chunks in the database."""
        try:
            with self.db_storage.get_connection() as conn:
                # Check if document already exists
                existing_doc = self._get_existing_document(file_metadata['file_hash'])
                
                if existing_doc:
                    # Update existing document
                    doc_id = existing_doc['id']
                    
                    # Delete existing chunks
                    delete_chunks_query = document_chunks_table.delete().where(
                        document_chunks_table.c.document_id == doc_id
                    )
                    conn.execute(delete_chunks_query)
                    
                    # Update document metadata
                    update_query = update(documents_table).where(
                        documents_table.c.id == doc_id
                    ).values(
                        status='processing',
                        chunk_count=len(chunks),
                        updated_at=datetime.now(),
                        last_modified=file_metadata['last_modified']
                    )
                    conn.execute(update_query)
                    
                else:
                    # Insert new document
                    insert_query = insert(documents_table).values(
                        filename=file_metadata['filename'],
                        filepath=file_metadata['filepath'],
                        file_hash=file_metadata['file_hash'],
                        file_size=file_metadata['file_size'],
                        mime_type=file_metadata['mime_type'],
                        content_type=file_metadata['content_type'],
                        last_modified=file_metadata['last_modified'],
                        metadata={'extension': file_metadata['extension']},
                        status='processing',
                        chunk_count=len(chunks)
                    )
                    
                    result = conn.execute(insert_query)
                    doc_id = result.inserted_primary_key[0]
                
                # Generate embeddings and store chunks
                self._store_chunks_with_embeddings(conn, doc_id, chunks)
                
                # Update document status to processed
                update_status_query = update(documents_table).where(
                    documents_table.c.id == doc_id
                ).values(status='processed')
                conn.execute(update_status_query)
                
                conn.commit()
                logger.debug(f"Stored document {doc_id} with {len(chunks)} chunks")
                
        except Exception as e:
            logger.error(f"Error storing document and chunks: {str(e)}")
            raise
    
    def _store_chunks_with_embeddings(self, conn, doc_id: int, chunks: List[TextChunk]):
        """Store chunks with their embeddings in the database."""
        chunk_records = []
        
        for chunk in chunks:
            try:
                # Generate embedding for the chunk
                embedding = self.embedder.embed(chunk.content)
                
                # Estimate token count
                token_count = self.text_chunker.estimate_token_count(chunk.content)
                
                chunk_record = {
                    'document_id': doc_id,
                    'chunk_index': chunk.chunk_index,
                    'content': chunk.content,
                    'content_hash': chunk.content_hash,
                    'token_count': token_count,
                    'char_count': chunk.char_count,
                    'embedding': embedding.tolist(),  # Convert numpy array to list
                    'metadata': chunk.metadata
                }
                
                chunk_records.append(chunk_record)
                
            except Exception as e:
                logger.error(f"Error processing chunk {chunk.chunk_index}: {str(e)}")
                # Continue with other chunks even if one fails
                continue
        
        if chunk_records:
            # Batch insert chunks
            insert_chunks_query = insert(document_chunks_table)
            conn.execute(insert_chunks_query, chunk_records)
            logger.debug(f"Inserted {len(chunk_records)} chunks for document {doc_id}")
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get statistics about ingested documents."""
        try:
            with self.db_storage.get_connection() as conn:
                # Count documents by status
                from sqlalchemy import func
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
    
    def delete_document(self, file_hash: str) -> bool:
        """Delete a document and all its chunks."""
        try:
            with self.db_storage.get_connection() as conn:
                # Delete document (chunks will be deleted via CASCADE)
                delete_query = documents_table.delete().where(
                    documents_table.c.file_hash == file_hash
                )
                result = conn.execute(delete_query)
                
                if result.rowcount > 0:
                    conn.commit()
                    logger.info(f"Deleted document with hash {file_hash}")
                    return True
                else:
                    logger.warning(f"No document found with hash {file_hash}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
    
 