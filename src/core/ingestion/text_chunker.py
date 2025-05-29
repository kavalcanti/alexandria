"""Text chunking utilities for document processing."""

import re
from typing import List, Optional

from src.configs import ChunkConfig, ChunkStrategy
from src.logger import get_module_logger
from src.core.ingestion.models import TextChunk

logger = get_module_logger(__name__)

class TextChunker:
    """Handles chunking of text content for RAG processing."""
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        """Initialize the text chunker with configuration."""
        self.config = config or ChunkConfig()
        
        # Compile regex patterns for efficiency
        self._sentence_pattern = re.compile(r'(?<=[.!?])\s+')
        self._paragraph_pattern = re.compile(r'\n\s*\n')
        self._code_function_pattern = re.compile(
            r'(?:def|function|class|interface|public|private|protected|static)\s+\w+',
            re.IGNORECASE
        )
        self._markdown_header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    def chunk_text(self, text: str, content_type: str = "text") -> List[TextChunk]:
        """
        Chunk text based on content type and configuration.
        
        Args:
            text: The text content to chunk
            content_type: Type of content (text, code, markdown, etc.)
            
        Returns:
            List of TextChunk objects
        """
        try:
            # Choose chunking strategy based on content type
            if content_type == "code":
                strategy = ChunkStrategy.CODE_BASED
            elif content_type == "markdown":
                strategy = ChunkStrategy.MARKDOWN_BASED
            else:
                strategy = self.config.strategy
            
            # Apply the appropriate chunking strategy
            if strategy == ChunkStrategy.FIXED_SIZE:
                chunks = self._chunk_fixed_size(text)
            elif strategy == ChunkStrategy.SENTENCE_BASED:
                chunks = self._chunk_sentence_based(text)
            elif strategy == ChunkStrategy.PARAGRAPH_BASED:
                chunks = self._chunk_paragraph_based(text)
            elif strategy == ChunkStrategy.CODE_BASED:
                chunks = self._chunk_code_based(text)
            elif strategy == ChunkStrategy.MARKDOWN_BASED:
                chunks = self._chunk_markdown_based(text)
            else:
                # Default to sentence-based
                chunks = self._chunk_sentence_based(text)
            
            # Post-process chunks
            chunks = self._post_process_chunks(chunks)
            
            logger.debug(f"Created {len(chunks)} chunks using {strategy.value} strategy")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise
    
    def _chunk_fixed_size(self, text: str) -> List[str]:
        """Chunk text into fixed-size pieces with overlap."""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.config.max_chunk_size
            
            # If we're not at the end and respecting boundaries, try to break at word boundary
            if end < text_length and self.config.respect_boundaries:
                # Look for the last space within the chunk
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk = text[start:end].strip()
            if len(chunk) >= self.config.min_chunk_size:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.config.overlap_size
            if start < 0:
                start = end
        
        return chunks
    
    def _chunk_sentence_based(self, text: str) -> List[str]:
        """Chunk text by sentences, respecting size limits."""
        sentences = self._sentence_pattern.split(text.strip())
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if adding this sentence would exceed the limit
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(potential_chunk) <= self.config.max_chunk_size:
                current_chunk = potential_chunk
            else:
                # Save current chunk if it meets minimum size
                if len(current_chunk) >= self.config.min_chunk_size:
                    chunks.append(current_chunk)
                
                # Start new chunk with overlap if configured
                if self.config.overlap_size > 0 and chunks:
                    overlap_text = current_chunk[-self.config.overlap_size:]
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk if it's substantial
        if len(current_chunk) >= self.config.min_chunk_size:
            chunks.append(current_chunk)
        
        return chunks
    
    def _chunk_paragraph_based(self, text: str) -> List[str]:
        """Chunk text by paragraphs, combining small ones."""
        paragraphs = self._paragraph_pattern.split(text.strip())
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            potential_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            
            if len(potential_chunk) <= self.config.max_chunk_size:
                current_chunk = potential_chunk
            else:
                # Save current chunk
                if len(current_chunk) >= self.config.min_chunk_size:
                    chunks.append(current_chunk)
                
                # Handle overlap for paragraphs
                if self.config.overlap_size > 0 and current_chunk:
                    overlap_text = current_chunk[-self.config.overlap_size:]
                    current_chunk = overlap_text + "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        if len(current_chunk) >= self.config.min_chunk_size:
            chunks.append(current_chunk)
        
        return chunks
    
    def _chunk_code_based(self, text: str) -> List[str]:
        """Chunk code by logical units (functions, classes, etc.)."""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        indentation_stack = []
        
        for line_num, line in enumerate(lines):
            line_size = len(line) + 1  # +1 for newline
            
            # Detect function/class definitions
            is_definition = bool(self._code_function_pattern.match(line.strip()))
            
            # Calculate indentation level
            stripped_line = line.lstrip()
            if stripped_line:
                indent_level = len(line) - len(stripped_line)
            else:
                indent_level = 0
            
            # Check if we should start a new chunk
            should_break = (
                current_size + line_size > self.config.max_chunk_size and
                current_chunk and
                (is_definition or indent_level == 0)
            )
            
            if should_break:
                chunk_text = '\n'.join(current_chunk)
                if len(chunk_text) >= self.config.min_chunk_size:
                    chunks.append(chunk_text)
                
                # Start new chunk with overlap (preserve function signature if applicable)
                if self.config.overlap_size > 0 and current_chunk:
                    overlap_lines = []
                    overlap_size = 0
                    for i in range(len(current_chunk) - 1, -1, -1):
                        line_len = len(current_chunk[i]) + 1
                        if overlap_size + line_len <= self.config.overlap_size:
                            overlap_lines.insert(0, current_chunk[i])
                            overlap_size += line_len
                        else:
                            break
                    current_chunk = overlap_lines
                    current_size = overlap_size
                else:
                    current_chunk = []
                    current_size = 0
            
            current_chunk.append(line)
            current_size += line_size
        
        # Add the last chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            if len(chunk_text) >= self.config.min_chunk_size:
                chunks.append(chunk_text)
        
        return chunks
    
    def _chunk_markdown_based(self, text: str) -> List[str]:
        """Chunk Markdown text by headers and sections."""
        chunks = []
        current_chunk = ""
        current_header = ""
        
        lines = text.split('\n')
        
        for line in lines:
            header_match = self._markdown_header_pattern.match(line)
            
            if header_match:
                # Found a header - potentially start new chunk
                header_level = len(header_match.group(1))
                header_text = header_match.group(2)
                
                # Save current chunk if it's substantial
                if len(current_chunk) >= self.config.min_chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                # Start new chunk with header
                if self.config.preserve_headers:
                    current_header = line
                    current_chunk = line + "\n"
                else:
                    current_chunk = ""
            else:
                # Regular content line
                potential_chunk = current_chunk + line + "\n"
                
                if len(potential_chunk) <= self.config.max_chunk_size:
                    current_chunk = potential_chunk
                else:
                    # Current chunk is full, save it
                    if len(current_chunk) >= self.config.min_chunk_size:
                        chunks.append(current_chunk.rstrip())
                    
                    # Start new chunk with overlap
                    if self.config.overlap_size > 0:
                        overlap_text = current_chunk[-self.config.overlap_size:]
                        current_chunk = overlap_text + line + "\n"
                    else:
                        # Start with header if preserving hierarchy
                        if self.config.preserve_headers and current_header:
                            current_chunk = current_header + "\n" + line + "\n"
                        else:
                            current_chunk = line + "\n"
        
        # Add the last chunk
        if len(current_chunk.rstrip()) >= self.config.min_chunk_size:
            chunks.append(current_chunk.rstrip())
        
        return chunks
    
    def _post_process_chunks(self, chunks: List[str]) -> List[TextChunk]:
        """Post-process raw chunks into TextChunk objects."""
        processed_chunks = []
        
        for i, chunk_content in enumerate(chunks):
            if not chunk_content.strip():
                continue
                
            chunk = TextChunk(
                content=chunk_content.strip(),
                chunk_index=i,
                char_count=len(chunk_content.strip()),
                metadata={
                    'strategy': self.config.strategy.value,
                    'max_chunk_size': self.config.max_chunk_size,
                    'overlap_size': self.config.overlap_size
                }
            )
            
            processed_chunks.append(chunk)
        
        return processed_chunks
    
    def estimate_token_count(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Simple estimation: ~4 characters per token for English text
        return len(text) // 4 