"""Main document ingestion service for RAG implementation."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from src.logger import get_module_logger
from src.configs import IngestionConfig
from src.infrastructure.embedder import Embedder
from src.core.ingestion.document_processor import DocumentProcessor
from src.core.ingestion.text_chunker import TextChunker
from src.core.ingestion.file_chunker import FileChunker
from src.core.ingestion.models import IngestionResult
from src.core.ingestion.ingestion_db_ops import IngestionDatabaseOps

logger = get_module_logger(__name__)

class DocumentIngestor:
    """Main service for ingesting documents into the RAG system."""
    
    def __init__(self, config: Optional[IngestionConfig] = None):
        """Initialize the document ingestor."""
        self.config = config or IngestionConfig()
        self.db_ops = IngestionDatabaseOps()
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
                    logger.info(f"File result: {file_result}")
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
                existing_doc = self.db_ops.get_existing_document(file_metadata['file_hash'])
                if existing_doc:
                    # Check if the document has any chunks
                    chunk_count = self.db_ops.get_document_chunk_count(existing_doc['id'])
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
            doc_id = self.db_ops.create_document_record(file_metadata)
            chunk_count = self.db_ops.store_chunks_with_embeddings(doc_id, chunks)
            self.db_ops.update_document_status(doc_id, 'processed', chunk_count)
            
            return {
                'success': True,
                'skipped': False,
                'chunk_count': chunk_count
            }
            
        except Exception as e:
            logger.error(f"Error processing regular file {file_path}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _process_large_file(self, file_path: Path, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a large file by chunking it first."""
        try:
            # Create document record first
            doc_id = self.db_ops.create_document_record(file_metadata)
            total_chunks = 0
            
            # Process file chunks
            for file_chunk in self.file_chunker.chunk_file(file_path):
                # Extract text from the file chunk
                text_content = self.document_processor.extract_text_content(file_chunk.path)
                
                if text_content.strip():
                    # Create text chunks from the file chunk
                    text_chunks = self.text_chunker.chunk_text(
                        text_content, 
                        file_metadata['content_type'],
                        start_index=total_chunks
                    )
                    
                    # Store chunks
                    chunk_count = self.db_ops.store_chunks_with_embeddings(doc_id, text_chunks)
                    total_chunks += chunk_count
            
            if total_chunks > 0:
                self.db_ops.update_document_status(doc_id, 'processed', total_chunks)
                return {
                    'success': True,
                    'skipped': False,
                    'chunk_count': total_chunks
                }
            else:
                self.db_ops.update_document_status(doc_id, 'failed')
                return {'success': False, 'error': 'No chunks created from large file'}
                
        except Exception as e:
            logger.error(f"Error processing large file {file_path}: {str(e)}")
            if doc_id:
                self.db_ops.update_document_status(doc_id, 'failed')
            return {'success': False, 'error': str(e)}
    
    def delete_document(self, file_hash: str) -> bool:
        """Delete a document and all its chunks."""
        return self.db_ops.delete_document_record(file_hash)
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get statistics about ingested documents."""
        try:
            return self.db_ops.get_ingestion_stats()
        except Exception as e:
            logger.error(f"Error getting ingestion stats: {str(e)}")
            return {
                'document_stats': {},
                'total_chunks': 0,
                'content_type_stats': {},
                'error': str(e)
            }
    
 