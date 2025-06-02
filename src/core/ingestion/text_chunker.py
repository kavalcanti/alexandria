"""Text chunking utilities for document processing."""

import re
from typing import List, Optional
from transformers import AutoTokenizer
from src.configs import ChunkConfig, ChunkStrategy
from src.logger import get_module_logger
from src.core.ingestion.models import TextChunk

logger = get_module_logger(__name__)

class TextChunker:
    """Handles chunking of text content for RAG processing."""
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        """Initialize the text chunker with configuration."""
        self.config = config or ChunkConfig()
        
        # Initialize the tokenizer - using the same model as our embeddings
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-mpnet-base-v2")
            logger.info("Initialized tokenizer for text chunking")
        except Exception as e:
            logger.error(f"Failed to initialize tokenizer: {str(e)}")
            raise
        
        # Compile regex patterns for efficiency
        self._sentence_pattern = re.compile(r'(?<=[.!?])\s+')
        self._paragraph_pattern = re.compile(r'\n\s*\n')
        self._code_function_pattern = re.compile(
            r'(?:def|function|class|interface|public|private|protected|static)\s+\w+',
            re.IGNORECASE
        )
        self._markdown_header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    def get_token_count(self, text: str) -> int:
        """
        Get exact token count using the embedding model's tokenizer.
        """
        return len(self.tokenizer.encode(text))

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
            
            # Post-process chunks with exact token count verification
            processed_chunks = []
            for chunk in chunks:
                if isinstance(chunk, str):
                    chunk_text = chunk
                else:
                    chunk_text = chunk.content
                    
                # Get exact token count
                token_count = self.get_token_count(chunk_text)
                
                if token_count <= self.config.max_tokens:
                    # Chunk is within token limit
                    if isinstance(chunk, str):
                        chunk = TextChunk(
                            content=chunk_text,
                            chunk_index=len(processed_chunks),
                            char_count=len(chunk_text),
                            metadata={
                                'strategy': strategy.value,
                                'token_count': token_count
                            }
                        )
                    processed_chunks.append(chunk)
                else:
                    # Chunk exceeds token limit - split it further
                    logger.debug(f"Splitting chunk with {token_count} tokens into smaller pieces")
                    
                    # Use fixed-size strategy to split oversized chunk
                    sub_chunks = self._chunk_fixed_size(chunk_text)
                    
                    # Recursively process sub-chunks to ensure they meet token limit
                    for sub_chunk in sub_chunks:
                        sub_token_count = self.get_token_count(sub_chunk)
                        if sub_token_count <= self.config.max_tokens:
                            processed_chunk = TextChunk(
                                content=sub_chunk,
                                chunk_index=len(processed_chunks),
                                char_count=len(sub_chunk),
                                metadata={
                                    'strategy': f"{strategy.value}_split",
                                    'token_count': sub_token_count,
                                    'parent_chunk_size': token_count
                                }
                            )
                            processed_chunks.append(processed_chunk)
                        else:
                            # If still too large, recursively chunk it
                            sub_processed = self.chunk_text(sub_chunk, content_type)
                            processed_chunks.extend(sub_processed)
            
            # Update chunk indices to ensure they're sequential
            for i, chunk in enumerate(processed_chunks):
                chunk.chunk_index = i
                
            logger.debug(f"Created {len(processed_chunks)} chunks using {strategy.value} strategy")
            return processed_chunks
            
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise
    
    def _chunk_fixed_size(self, text: str) -> List[str]:
        """Chunk text into fixed-size pieces with overlap, using token count as primary limit."""
        chunks = []
        start = 0
        text_length = len(text)
        
        # Estimate initial chunk size based on average chars per token
        # This is a rough estimate to avoid too many token count checks
        avg_chars_per_token = 4  # Conservative estimate
        initial_chunk_size = self.config.max_tokens * avg_chars_per_token
        
        while start < text_length:
            # Calculate initial proposed end
            proposed_end = start + initial_chunk_size
            
            # Adjust end position based on token limit
            end = self._adjust_chunk_size(text, start, proposed_end)
            
            chunk = text[start:end].strip()
            if chunk and self._is_chunk_within_limits(chunk):
                chunks.append(chunk)
            elif chunk:
                # If chunk is too large, try more aggressive splitting
                half_size = len(chunk) // 2
                first_half = chunk[:half_size].strip()
                second_half = chunk[half_size:].strip()
                
                if first_half and self._is_chunk_within_limits(first_half):
                    chunks.append(first_half)
                if second_half and self._is_chunk_within_limits(second_half):
                    chunks.append(second_half)
            
            # Move start position with overlap
            # Ensure overlap doesn't create chunks that are too small
            overlap = min(self.config.overlap_size, (end - start) // 4)
            start = end - overlap
            if start < 0 or start >= end:
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
    
    def _count_words(self, text: str) -> int:
        """Deprecated: Use get_token_count instead."""
        logger.warning("_count_words is deprecated, use get_token_count instead")
        return self.get_token_count(text)

    def estimate_token_count(self, text: str) -> int:
        """Deprecated: Use get_token_count instead."""
        logger.warning("estimate_token_count is deprecated, use get_token_count instead")
        return self.get_token_count(text)

    def _is_chunk_within_limits(self, chunk: str) -> bool:
        """Check if chunk is within both character and token limits."""
        # Check character-based limits
        if len(chunk) < self.config.min_chunk_size:
            return False
        if len(chunk) > self.config.max_chunk_size:
            return False
            
        # Get exact token count
        token_count = self.get_token_count(chunk)
        return token_count <= self.config.max_tokens

    def _adjust_chunk_size(self, text: str, start: int, proposed_end: int) -> int:
        """
        Adjust chunk size to respect token limits using exact tokenization.
        Returns the adjusted end position.
        """
        end = min(proposed_end, len(text))
        chunk = text[start:end]
        token_count = self.get_token_count(chunk)
        
        # Binary search for the right chunk size that respects token limit
        while token_count > self.config.max_tokens:
            # Binary search step
            end = start + (end - start) // 2
            chunk = text[start:end]
            token_count = self.get_token_count(chunk)
            
            # Safety check
            if end <= start:
                logger.warning("Chunk size reduction failed - falling back to minimum size")
                return start + self.config.min_chunk_size
        
        # Now we have a safe upper bound, try to expand while staying under limit
        # Use smaller increments (50 chars) for more precise control
        while end < proposed_end:
            next_end = min(end + 50, proposed_end)
            test_chunk = text[start:next_end]
            test_tokens = self.get_token_count(test_chunk)
            if test_tokens > self.config.max_tokens:
                break
            end = next_end
            chunk = test_chunk
            token_count = test_tokens
        
        # Find natural break points within token limit
        if end < len(text) and self.config.respect_boundaries:
            # Try different types of boundaries in order of preference
            boundaries = [
                ('\n\n', self.config.min_chunk_size),  # Paragraph break
                ('. ', self.config.min_chunk_size),    # Sentence break
                ('\n', self.config.min_chunk_size),    # Line break
                (' ', self.config.min_chunk_size // 2) # Word break
            ]
            
            for boundary, min_size in boundaries:
                break_pos = text.rfind(boundary, start + min_size, end)
                if break_pos > start:
                    test_chunk = text[start:break_pos + len(boundary)]
                    if self.get_token_count(test_chunk) <= self.config.max_tokens:
                        return break_pos + len(boundary)
        
        return end 