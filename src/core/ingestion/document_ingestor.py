"""Main document ingestion service for RAG implementation."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import asyncio
import concurrent.futures
from contextlib import contextmanager

from sqlalchemy import select, insert, update, and_, or_
from sqlalchemy.exc import IntegrityError

from src.logger import get_module_logger
from src.infrastructure.db_connector import DatabaseStorage
from src.infrastructure.db.db_models import documents_table, document_chunks_table
from src.core.embedding.embedder import Embedder
from src.core.ingestion.document_processor import DocumentProcessor
from src.core.ingestion.text_chunker import TextChunker, ChunkConfig, TextChunk

logger = get_module_logger(__name__)


@dataclass
class IngestionConfig:
    """Configuration for document ingestion."""
    chunk_config: ChunkConfig = None
    batch_size: int = 50  # Number of chunks to process in batch
    max_workers: int = 4  # Number of worker threads for parallel processing
    skip_existing: bool = True  # Skip files that are already ingested
    update_existing: bool = False  # Update existing documents if they've changed
    
    def __post_init__(self):
        if self.chunk_config is None:
            self.chunk_config = ChunkConfig()


@dataclass
class IngestionResult:
    """Result of document ingestion process."""
    total_files: int = 0
    processed_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    total_chunks: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class DocumentIngestor:
    """Main service for ingesting documents into the RAG system."""
    
    def __init__(self, config: Optional[IngestionConfig] = None):
        """Initialize the document ingestor."""
        self.config = config or IngestionConfig()
        self.db_storage = DatabaseStorage()
        self.embedder = Embedder()
        self.document_processor = DocumentProcessor()
        self.text_chunker = TextChunker(self.config.chunk_config)
        
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
            
            # Process files in batches
            for i in range(0, len(supported_files), self.config.batch_size):
                batch = supported_files[i:i + self.config.batch_size]
                batch_results = self._process_file_batch(batch)
                
                # Aggregate results
                result.processed_files += batch_results.processed_files
                result.skipped_files += batch_results.skipped_files
                result.failed_files += batch_results.failed_files
                result.total_chunks += batch_results.total_chunks
                result.errors.extend(batch_results.errors)
            
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
            
            if not self.document_processor.is_supported_file(file_path):
                error_msg = f"File type not supported: {file_path}"
                logger.warning(error_msg)
                result.errors.append(error_msg)
                result.skipped_files = 1
                return result
            
            # Process the single file
            file_result = self._process_single_file(file_path)
            
            if file_result['success']:
                result.processed_files = 1
                result.total_chunks = file_result['chunk_count']
                logger.info(f"Successfully ingested {file_path} with {file_result['chunk_count']} chunks")
            else:
                result.failed_files = 1
                result.errors.append(file_result['error'])
                logger.error(f"Failed to ingest {file_path}: {file_result['error']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error ingesting file {file_path}: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.failed_files = 1
            return result
    
    def _process_file_batch(self, file_paths: List[Path]) -> IngestionResult:
        """Process a batch of files, potentially in parallel."""
        result = IngestionResult()
        
        if self.config.max_workers > 1:
            # Parallel processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_file = {
                    executor.submit(self._process_single_file, file_path): file_path 
                    for file_path in file_paths
                }
                
                for future in concurrent.futures.as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        file_result = future.result()
                        self._aggregate_file_result(result, file_result, file_path)
                    except Exception as e:
                        error_msg = f"Error processing {file_path}: {str(e)}"
                        logger.error(error_msg)
                        result.errors.append(error_msg)
                        result.failed_files += 1
        else:
            # Sequential processing
            for file_path in file_paths:
                try:
                    file_result = self._process_single_file(file_path)
                    self._aggregate_file_result(result, file_result, file_path)
                except Exception as e:
                    error_msg = f"Error processing {file_path}: {str(e)}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)
                    result.failed_files += 1
        
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
                    if not self.config.update_existing:
                        logger.debug(f"Skipping existing file: {file_path}")
                        return {'success': True, 'skipped': True, 'chunk_count': 0}
                    elif existing_doc['last_modified'] >= file_metadata['last_modified']:
                        logger.debug(f"Skipping unchanged file: {file_path}")
                        return {'success': True, 'skipped': True, 'chunk_count': 0}
            
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
            error_msg = f"Error processing {file_path}: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': str(e)}
    
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