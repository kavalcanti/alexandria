"""Document processing utilities for file ingestion."""

import os
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

from src.logger import get_module_logger

logger = get_module_logger(__name__)


class DocumentProcessor:
    """Handles processing of various document types for RAG ingestion."""
    
    SUPPORTED_TEXT_EXTENSIONS = {
        '.txt', '.md', '.markdown', '.rst', '.py', '.js', '.ts', '.java', 
        '.cpp', '.c', '.h', '.hpp', '.css', '.html', '.xml', '.json', 
        '.yaml', '.yml', '.ini', '.cfg', '.conf', '.log', '.csv'
    }
    
    SUPPORTED_DOCUMENT_EXTENSIONS = {
        '.pdf', '.docx', '.doc', '.rtf', '.odt'
    }
    
    def __init__(self):
        """Initialize the document processor."""
        self.supported_extensions = (
            self.SUPPORTED_TEXT_EXTENSIONS | 
            self.SUPPORTED_DOCUMENT_EXTENSIONS
        )
    
    def is_supported_file(self, filepath: Path) -> bool:
        """Check if the file type is supported for processing."""
        return filepath.suffix.lower() in self.supported_extensions
    
    def get_file_metadata(self, filepath: Path) -> Dict[str, Any]:
        """Extract metadata from a file."""
        try:
            stat = filepath.stat()
            mime_type, _ = mimetypes.guess_type(str(filepath))
            
            metadata = {
                'filename': filepath.name,
                'filepath': str(filepath.absolute()),
                'file_size': stat.st_size,
                'mime_type': mime_type,
                'last_modified': datetime.fromtimestamp(stat.st_mtime),
                'content_type': self._determine_content_type(filepath),
                'extension': filepath.suffix.lower()
            }
            
            # Calculate file hash for deduplication
            metadata['file_hash'] = self._calculate_file_hash(filepath)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {filepath}: {str(e)}")
            raise
    
    def _determine_content_type(self, filepath: Path) -> str:
        """Determine the content type based on file extension."""
        extension = filepath.suffix.lower()
        
        if extension in {'.md', '.markdown'}:
            return 'markdown'
        elif extension in {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp'}:
            return 'code'
        elif extension in {'.html', '.xml'}:
            return 'markup'
        elif extension in {'.json', '.yaml', '.yml'}:
            return 'structured_data'
        elif extension in {'.pdf'}:
            return 'pdf'
        elif extension in {'.docx', '.doc', '.rtf', '.odt'}:
            return 'document'
        elif extension in {'.csv'}:
            return 'csv'
        else:
            return 'text'
    
    def _calculate_file_hash(self, filepath: Path) -> str:
        """Calculate SHA-256 hash of file content for deduplication."""
        hash_sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {filepath}: {str(e)}")
            raise
    
    def extract_text_content(self, filepath: Path) -> str:
        """Extract text content from supported file types."""
        try:
            content_type = self._determine_content_type(filepath)
            
            if content_type == 'pdf':
                return self._extract_pdf_text(filepath)
            elif content_type == 'document':
                return self._extract_document_text(filepath)
            else:
                # Handle text-based files
                return self._extract_text_file(filepath)
                
        except Exception as e:
            logger.error(f"Error extracting text from {filepath}: {str(e)}")
            raise
    
    def _extract_text_file(self, filepath: Path) -> str:
        """Extract text from plain text files."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        content = f.read()
                    logger.debug(f"Successfully read {filepath} with {encoding} encoding")
                    return content
                except UnicodeDecodeError:
                    continue
            
            raise ValueError(f"Could not decode file {filepath} with any supported encoding")
            
        except Exception as e:
            logger.error(f"Error reading text file {filepath}: {str(e)}")
            raise
    
    def _extract_pdf_text(self, filepath: Path) -> str:
        """Extract text from PDF files."""
        try:
            # Try to import PDF processing libraries
            try:
                import PyPDF2
                return self._extract_pdf_pypdf2(filepath)
            except ImportError:
                try:
                    import pdfplumber
                    return self._extract_pdf_pdfplumber(filepath)
                except ImportError:
                    logger.warning(
                        f"No PDF processing library available. "
                        f"Install PyPDF2 or pdfplumber to process {filepath}"
                    )
                    return f"[PDF content from {filepath.name} - PDF processing library not available]"
                    
        except Exception as e:
            logger.error(f"Error extracting PDF text from {filepath}: {str(e)}")
            return f"[Error extracting PDF content from {filepath.name}: {str(e)}]"
    
    def _extract_pdf_pypdf2(self, filepath: Path) -> str:
        """Extract text using PyPDF2."""
        import PyPDF2
        
        text_content = []
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(f"[Page {page_num + 1}]\n{text}")
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num + 1} from {filepath}: {str(e)}")
                    continue
        
        return '\n\n'.join(text_content)
    
    def _extract_pdf_pdfplumber(self, filepath: Path) -> str:
        """Extract text using pdfplumber."""
        import pdfplumber
        
        text_content = []
        with pdfplumber.open(filepath) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text()
                    if text and text.strip():
                        text_content.append(f"[Page {page_num + 1}]\n{text}")
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num + 1} from {filepath}: {str(e)}")
                    continue
        
        return '\n\n'.join(text_content)
    
    def _extract_document_text(self, filepath: Path) -> str:
        """Extract text from document files (docx, doc, etc.)."""
        extension = filepath.suffix.lower()
        
        try:
            if extension == '.docx':
                return self._extract_docx_text(filepath)
            else:
                logger.warning(
                    f"Document type {extension} not fully supported. "
                    f"Consider converting {filepath.name} to a supported format."
                )
                return f"[Document content from {filepath.name} - format not fully supported]"
                
        except Exception as e:
            logger.error(f"Error extracting document text from {filepath}: {str(e)}")
            return f"[Error extracting document content from {filepath.name}: {str(e)}]"
    
    def _extract_docx_text(self, filepath: Path) -> str:
        """Extract text from DOCX files."""
        try:
            import docx
            
            doc = docx.Document(filepath)
            text_content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            return '\n\n'.join(text_content)
            
        except ImportError:
            logger.warning(
                f"python-docx library not available. "
                f"Install python-docx to process {filepath}"
            )
            return f"[DOCX content from {filepath.name} - python-docx library not available]"
        except Exception as e:
            logger.error(f"Error extracting DOCX text from {filepath}: {str(e)}")
            raise
    
    def scan_directory(self, directory_path: Path, recursive: bool = True) -> List[Path]:
        """Scan directory for supported files."""
        supported_files = []
        
        try:
            if not directory_path.exists():
                raise FileNotFoundError(f"Directory {directory_path} does not exist")
            
            if not directory_path.is_dir():
                raise ValueError(f"{directory_path} is not a directory")
            
            # Determine the search pattern
            pattern = "**/*" if recursive else "*"
            
            for file_path in directory_path.glob(pattern):
                if file_path.is_file() and self.is_supported_file(file_path):
                    supported_files.append(file_path)
                    logger.debug(f"Found supported file: {file_path}")
            
            logger.info(f"Found {len(supported_files)} supported files in {directory_path}")
            return supported_files
            
        except Exception as e:
            logger.error(f"Error scanning directory {directory_path}: {str(e)}")
            raise 