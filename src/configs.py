from dataclasses import dataclass
from enum import Enum
from typing import Optional
from pathlib import Path

@dataclass
class RAGToolsConfig:
    enable_retrieval: bool = True
    max_retrieval_results: int = 5
    min_similarity_score: float = 0.3
    context_size: int = 1
    include_source_metadata: bool = True


class FileChunkStrategy(Enum):
    """Enumeration of file chunking strategies."""
    SIZE_BASED = "size_based"
    LINE_BASED = "line_based"
    MARKDOWN_SECTION = "markdown_section"


class ChunkStrategy(Enum):
    """Enumeration of different chunking strategies."""
    FIXED_SIZE = "fixed_size"
    SENTENCE_BASED = "sentence_based"
    PARAGRAPH_BASED = "paragraph_based"
    SEMANTIC_BASED = "semantic_based"
    CODE_BASED = "code_based"
    MARKDOWN_BASED = "markdown_based"


@dataclass
class ChunkConfig:
    """Configuration for text chunking."""
    strategy: ChunkStrategy = ChunkStrategy.SENTENCE_BASED
    max_chunk_size: int = 1000  # Maximum characters per chunk
    min_chunk_size: int = 100   # Minimum characters per chunk
    overlap_size: int = 100     # Characters to overlap between chunks
    respect_boundaries: bool = True  # Respect sentence/paragraph boundaries
    
    # Code-specific settings
    include_function_signatures: bool = True
    include_class_definitions: bool = True
    
    # Markdown-specific settings
    preserve_headers: bool = True
    header_hierarchy: bool = True


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
class IngestionConfig:
    """Configuration for document ingestion."""
    chunk_config: ChunkConfig = None
    file_chunk_config: FileChunkConfig = None
    batch_size: int = 50  # Number of chunks to process in batch
    skip_existing: bool = True  # Skip files that are already ingested
    update_existing: bool = False  # Update existing documents if they've changed
    enable_large_file_chunking: bool = True  # Enable file-level chunking for large files
    
    def __post_init__(self):
        if self.chunk_config is None:
            self.chunk_config = ChunkConfig()
        if self.file_chunk_config is None:
            self.file_chunk_config = FileChunkConfig()

