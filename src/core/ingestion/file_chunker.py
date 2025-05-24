"""File chunking utilities for handling very large text and markdown files."""

import os
import tempfile
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator, Tuple
from dataclasses import dataclass
from enum import Enum

from src.logger import get_module_logger

logger = get_module_logger(__name__)


class FileChunkStrategy(Enum):
    """Enumeration of file chunking strategies."""
    SIZE_BASED = "size_based"
    LINE_BASED = "line_based"
    MARKDOWN_SECTION = "markdown_section"


@dataclass
class FileChunkConfig:
    """Configuration for file chunking."""
    max_chunk_size: int = 100 * 1024 * 1024  # 100MB default max size
    preferred_chunk_size: int = 50 * 1024 * 1024  # 50MB preferred size
    overlap_lines: int = 50  # Number of lines to overlap between chunks
    strategy: FileChunkStrategy = FileChunkStrategy.SIZE_BASED
    preserve_structure: bool = True  # Try to preserve document structure
    temp_dir: Optional[Path] = None  # Directory for temporary files


@dataclass
class FileChunk:
    """Represents a chunk of a large file."""
    chunk_id: str
    chunk_index: int
    file_path: Path
    temp_file_path: Path
    start_byte: int
    end_byte: int
    size_bytes: int
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize computed fields."""
        if self.metadata is None:
            self.metadata = {}
        if not self.chunk_id:
            self.chunk_id = self._generate_chunk_id()
    
    def _generate_chunk_id(self) -> str:
        """Generate a unique ID for this chunk."""
        content = f"{self.file_path}:{self.chunk_index}:{self.start_byte}:{self.end_byte}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]


class FileChunker:
    """Handles chunking of very large files into manageable pieces."""
    
    def __init__(self, config: Optional[FileChunkConfig] = None):
        """Initialize the file chunker."""
        self.config = config or FileChunkConfig()
        self._temp_files: List[Path] = []  # Track temp files for cleanup
        
        # Set up temporary directory
        if self.config.temp_dir is None:
            self.config.temp_dir = Path(tempfile.gettempdir()) / "alexandria_chunks"
        
        self.config.temp_dir.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"FileChunker initialized with temp dir: {self.config.temp_dir}")
    
    def should_chunk_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be chunked based on size and type.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file should be chunked
        """
        try:
            if not file_path.exists():
                return False
            
            file_size = file_path.stat().st_size
            file_extension = file_path.suffix.lower()
            
            # Only chunk text-based files
            supported_extensions = {'.txt', '.md', '.markdown', '.rst', '.log'}
            if file_extension not in supported_extensions:
                return False
            
            # Check if file exceeds maximum size threshold
            return file_size > self.config.max_chunk_size
            
        except Exception as e:
            logger.error(f"Error checking if file should be chunked {file_path}: {str(e)}")
            return False
    
    def chunk_file(self, file_path: Path) -> List[FileChunk]:
        """
        Chunk a large file into smaller manageable pieces.
        
        Args:
            file_path: Path to the file to chunk
            
        Returns:
            List of FileChunk objects representing the file pieces
        """
        try:
            if not self.should_chunk_file(file_path):
                logger.debug(f"File {file_path} does not need chunking")
                return []
            
            logger.info(f"Chunking large file: {file_path} ({file_path.stat().st_size / 1024 / 1024:.1f}MB)")
            
            # Choose strategy based on file type
            file_extension = file_path.suffix.lower()
            if file_extension in {'.md', '.markdown'}:
                strategy = FileChunkStrategy.MARKDOWN_SECTION
            else:
                strategy = self.config.strategy
            
            # Apply the appropriate chunking strategy
            if strategy == FileChunkStrategy.MARKDOWN_SECTION:
                chunks = self._chunk_markdown_sections(file_path)
            elif strategy == FileChunkStrategy.LINE_BASED:
                chunks = self._chunk_line_based(file_path)
            else:
                chunks = self._chunk_size_based(file_path)
            
            logger.info(f"Created {len(chunks)} file chunks for {file_path}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking file {file_path}: {str(e)}")
            raise
    
    def _chunk_size_based(self, file_path: Path) -> List[FileChunk]:
        """Chunk file based on size, trying to break at line boundaries."""
        chunks = []
        chunk_index = 0
        
        try:
            file_size = file_path.stat().st_size
            current_position = 0
            
            while current_position < file_size:
                # Calculate chunk end position
                chunk_end = min(current_position + self.config.preferred_chunk_size, file_size)
                
                # Try to break at a line boundary if not at end of file
                if chunk_end < file_size:
                    chunk_end = self._find_line_break(file_path, chunk_end)
                
                # Create temporary file for this chunk
                temp_file = self._create_temp_chunk_file(
                    file_path, current_position, chunk_end, chunk_index
                )
                
                chunk = FileChunk(
                    chunk_id="",  # Will be generated in __post_init__
                    chunk_index=chunk_index,
                    file_path=file_path,
                    temp_file_path=temp_file,
                    start_byte=current_position,
                    end_byte=chunk_end,
                    size_bytes=chunk_end - current_position
                )
                
                chunks.append(chunk)
                
                # Move to next chunk with overlap handling
                current_position = max(chunk_end - (self.config.overlap_lines * 100), chunk_end)
                chunk_index += 1
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error in size-based chunking of {file_path}: {str(e)}")
            raise
    
    def _chunk_line_based(self, file_path: Path) -> List[FileChunk]:
        """Chunk file based on line count."""
        chunks = []
        chunk_index = 0
        
        try:
            # Estimate lines per chunk based on preferred size
            avg_line_length = self._estimate_average_line_length(file_path)
            lines_per_chunk = max(1000, self.config.preferred_chunk_size // avg_line_length)
            
            current_line = 0
            current_position = 0
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines_buffer = []
                
                for line_num, line in enumerate(f, 1):
                    lines_buffer.append(line)
                    
                    if len(lines_buffer) >= lines_per_chunk:
                        # Create chunk from current buffer
                        chunk_content = ''.join(lines_buffer)
                        temp_file = self._create_temp_chunk_file_from_content(
                            file_path, chunk_content, chunk_index
                        )
                        
                        chunk = FileChunk(
                            chunk_id="",
                            chunk_index=chunk_index,
                            file_path=file_path,
                            temp_file_path=temp_file,
                            start_byte=current_position,
                            end_byte=current_position + len(chunk_content.encode('utf-8')),
                            size_bytes=len(chunk_content.encode('utf-8')),
                            line_start=current_line,
                            line_end=line_num
                        )
                        
                        chunks.append(chunk)
                        
                        # Prepare for next chunk with overlap
                        overlap_lines = lines_buffer[-self.config.overlap_lines:] if self.config.overlap_lines > 0 else []
                        lines_buffer = overlap_lines
                        current_line = line_num - len(overlap_lines)
                        current_position = chunk.end_byte - sum(len(line.encode('utf-8')) for line in overlap_lines)
                        chunk_index += 1
                
                # Handle remaining lines
                if lines_buffer:
                    chunk_content = ''.join(lines_buffer)
                    temp_file = self._create_temp_chunk_file_from_content(
                        file_path, chunk_content, chunk_index
                    )
                    
                    chunk = FileChunk(
                        chunk_id="",
                        chunk_index=chunk_index,
                        file_path=file_path,
                        temp_file_path=temp_file,
                        start_byte=current_position,
                        end_byte=current_position + len(chunk_content.encode('utf-8')),
                        size_bytes=len(chunk_content.encode('utf-8')),
                        line_start=current_line,
                        line_end=current_line + len(lines_buffer)
                    )
                    
                    chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error in line-based chunking of {file_path}: {str(e)}")
            raise
    
    def _chunk_markdown_sections(self, file_path: Path) -> List[FileChunk]:
        """Chunk markdown file by sections (headers)."""
        chunks = []
        chunk_index = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Find all markdown headers
            import re
            header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
            headers = [(m.start(), m.group(1), m.group(2)) for m in header_pattern.finditer(content)]
            
            if not headers:
                # No headers found, fall back to line-based chunking
                return self._chunk_line_based(file_path)
            
            # Create chunks based on header sections
            for i, (header_start, header_level, header_text) in enumerate(headers):
                # Find the start of the next section
                next_header_start = headers[i + 1][0] if i + 1 < len(headers) else len(content)
                
                section_content = content[header_start:next_header_start].strip()
                
                # If section is too large, sub-chunk it
                if len(section_content.encode('utf-8')) > self.config.preferred_chunk_size:
                    sub_chunks = self._sub_chunk_large_section(
                        file_path, section_content, chunk_index, header_text
                    )
                    chunks.extend(sub_chunks)
                    chunk_index += len(sub_chunks)
                else:
                    # Create single chunk for this section
                    temp_file = self._create_temp_chunk_file_from_content(
                        file_path, section_content, chunk_index
                    )
                    
                    chunk = FileChunk(
                        chunk_id="",
                        chunk_index=chunk_index,
                        file_path=file_path,
                        temp_file_path=temp_file,
                        start_byte=header_start,
                        end_byte=next_header_start,
                        size_bytes=len(section_content.encode('utf-8')),
                        metadata={'section_title': header_text, 'header_level': len(header_level)}
                    )
                    
                    chunks.append(chunk)
                    chunk_index += 1
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error in markdown section chunking of {file_path}: {str(e)}")
            # Fall back to line-based chunking
            return self._chunk_line_based(file_path)
    
    def _sub_chunk_large_section(self, file_path: Path, section_content: str, 
                                base_chunk_index: int, section_title: str) -> List[FileChunk]:
        """Sub-chunk a large markdown section."""
        sub_chunks = []
        lines = section_content.split('\n')
        current_lines = []
        current_size = 0
        sub_index = 0
        
        for line in lines:
            line_size = len(line.encode('utf-8')) + 1  # +1 for newline
            
            if current_size + line_size > self.config.preferred_chunk_size and current_lines:
                # Create sub-chunk
                chunk_content = '\n'.join(current_lines)
                temp_file = self._create_temp_chunk_file_from_content(
                    file_path, chunk_content, f"{base_chunk_index}_{sub_index}"
                )
                
                chunk = FileChunk(
                    chunk_id="",
                    chunk_index=base_chunk_index + sub_index,
                    file_path=file_path,
                    temp_file_path=temp_file,
                    start_byte=0,  # Relative to section
                    end_byte=len(chunk_content.encode('utf-8')),
                    size_bytes=len(chunk_content.encode('utf-8')),
                    metadata={
                        'section_title': section_title,
                        'sub_chunk': True,
                        'sub_index': sub_index
                    }
                )
                
                sub_chunks.append(chunk)
                
                # Start new sub-chunk with overlap
                overlap_lines = current_lines[-self.config.overlap_lines:] if self.config.overlap_lines > 0 else []
                current_lines = overlap_lines + [line]
                current_size = sum(len(l.encode('utf-8')) + 1 for l in current_lines)
                sub_index += 1
            else:
                current_lines.append(line)
                current_size += line_size
        
        # Handle remaining lines
        if current_lines:
            chunk_content = '\n'.join(current_lines)
            temp_file = self._create_temp_chunk_file_from_content(
                file_path, chunk_content, f"{base_chunk_index}_{sub_index}"
            )
            
            chunk = FileChunk(
                chunk_id="",
                chunk_index=base_chunk_index + sub_index,
                file_path=file_path,
                temp_file_path=temp_file,
                start_byte=0,
                end_byte=len(chunk_content.encode('utf-8')),
                size_bytes=len(chunk_content.encode('utf-8')),
                metadata={
                    'section_title': section_title,
                    'sub_chunk': True,
                    'sub_index': sub_index
                }
            )
            
            sub_chunks.append(chunk)
        
        return sub_chunks
    
    def _find_line_break(self, file_path: Path, position: int) -> int:
        """Find the nearest line break after the given position."""
        try:
            with open(file_path, 'rb') as f:
                f.seek(position)
                # Read up to 4KB to find a line break
                chunk = f.read(4096)
                
                # Find the first newline
                newline_pos = chunk.find(b'\n')
                if newline_pos != -1:
                    return position + newline_pos + 1
                else:
                    # No newline found, return original position
                    return position
                    
        except Exception as e:
            logger.warning(f"Error finding line break in {file_path} at position {position}: {str(e)}")
            return position
    
    def _estimate_average_line_length(self, file_path: Path) -> int:
        """Estimate the average line length in the file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Sample first 1000 lines
                total_chars = 0
                line_count = 0
                
                for i, line in enumerate(f):
                    if i >= 1000:
                        break
                    total_chars += len(line)
                    line_count += 1
                
                return max(50, total_chars // max(1, line_count))  # Minimum 50 chars per line
                
        except Exception as e:
            logger.warning(f"Error estimating line length for {file_path}: {str(e)}")
            return 100  # Default estimate
    
    def _create_temp_chunk_file(self, file_path: Path, start_byte: int, 
                               end_byte: int, chunk_index: int) -> Path:
        """Create a temporary file containing the specified byte range."""
        try:
            file_stem = file_path.stem
            file_suffix = file_path.suffix
            temp_filename = f"{file_stem}_chunk_{chunk_index}{file_suffix}"
            temp_file_path = self.config.temp_dir / temp_filename
            
            with open(file_path, 'rb') as source:
                source.seek(start_byte)
                chunk_data = source.read(end_byte - start_byte)
                
                with open(temp_file_path, 'wb') as temp_file:
                    temp_file.write(chunk_data)
            
            self._temp_files.append(temp_file_path)
            return temp_file_path
            
        except Exception as e:
            logger.error(f"Error creating temp chunk file: {str(e)}")
            raise
    
    def _create_temp_chunk_file_from_content(self, file_path: Path, content: str, 
                                           chunk_index: Any) -> Path:
        """Create a temporary file from string content."""
        try:
            file_stem = file_path.stem
            file_suffix = file_path.suffix
            temp_filename = f"{file_stem}_chunk_{chunk_index}{file_suffix}"
            temp_file_path = self.config.temp_dir / temp_filename
            
            with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
                temp_file.write(content)
            
            self._temp_files.append(temp_file_path)
            return temp_file_path
            
        except Exception as e:
            logger.error(f"Error creating temp chunk file from content: {str(e)}")
            raise
    
    def cleanup_temp_files(self):
        """Clean up all temporary chunk files."""
        cleaned_count = 0
        for temp_file in self._temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    cleaned_count += 1
            except Exception as e:
                logger.warning(f"Error cleaning up temp file {temp_file}: {str(e)}")
        
        self._temp_files.clear()
        
        if cleaned_count > 0:
            logger.debug(f"Cleaned up {cleaned_count} temporary chunk files")
    
 