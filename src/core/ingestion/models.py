from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib

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

@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    content: str
    chunk_index: int
    char_count: int
    token_count: Optional[int] = None
    content_hash: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize computed fields."""
        if not self.content_hash:
            self.content_hash = self._calculate_hash()
        if self.metadata is None:
            self.metadata = {}
    
    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of chunk content."""
        return hashlib.sha256(self.content.encode('utf-8')).hexdigest()

