# Document Ingestion Module

This module provides comprehensive document ingestion capabilities for the Alexandria RAG (Retrieval-Augmented Generation) system. It supports various file formats, intelligent text chunking, large file handling, and automatic embedding generation.

## Features

### Supported File Types

**Text Files:**
- `.txt`, `.md`, `.markdown`, `.rst`
- `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.h`, `.hpp`
- `.css`, `.html`, `.xml`, `.json`, `.yaml`, `.yml`
- `.ini`, `.cfg`, `.conf`, `.log`, `.csv`

**Document Files:**
- `.pdf` (requires pdfplumber)
- `.docx` (requires python-docx)
- `.doc`, `.rtf`, `.odt` (limited support)

### Key Capabilities

- **Automatic file type detection** and content extraction
- **Multiple chunking strategies** optimized for different content types
- **Large file handling** with file-level chunking for files >100MB
- **Deduplication** using file hashes
- **Sequential processing** with simple error handling
- **Automatic encoding detection** for text files
- **Metadata tracking** with file statistics
- **Progress monitoring** and error reporting
- **Database integration** with PostgreSQL and pgvector

## Quick Start

### Basic Usage

```python
from src.core.ingestion.document_ingestor import DocumentIngestor

# Create ingestor with default settings
ingestor = DocumentIngestor()

# Ingest a single file
result = ingestor.ingest_file("path/to/document.pdf")

# Ingest all files in a directory
result = ingestor.ingest_directory("path/to/documents", recursive=True)

print(f"Processed {result.processed_files} files")
print(f"Created {result.total_chunks} chunks")
```

### Command Line Interface

```bash
# Ingest a single file
python -m src.core.ingestion.cli ingest-file document.pdf

# Ingest all files in a directory
python -m src.core.ingestion.cli ingest-dir /path/to/documents

# Custom chunk size and strategy
python -m src.core.ingestion.cli ingest-dir docs/ \
    --chunk-strategy markdown_based \
    --chunk-size 1500 \
    --overlap-size 100

# Process large files with custom file chunking
python -m src.core.ingestion.cli ingest-dir /path/to/large-files \
    --max-file-size 200 \
    --preferred-file-chunk-size 100 \
    --file-chunk-strategy markdown_section

# Disable large file chunking (process files as-is)
python -m src.core.ingestion.cli ingest-dir docs/ \
    --disable-large-file-chunking

# Show statistics
python -m src.core.ingestion.cli stats

# List supported file types
python -m src.core.ingestion.cli supported-types
```

## Configuration

### Chunking Strategies

The module supports several chunking strategies optimized for different content types:

#### 1. Sentence-Based (Default)
- Breaks text at sentence boundaries
- Respects natural language flow
- Good for general text documents

```python
from src.core.ingestion.text_chunker import ChunkConfig, ChunkStrategy

config = ChunkConfig(
    strategy=ChunkStrategy.SENTENCE_BASED,
    max_chunk_size=1000,
    min_chunk_size=100,
    overlap_size=100
)
```

#### 2. Paragraph-Based
- Breaks text at paragraph boundaries
- Maintains document structure
- Good for well-structured documents

```python
config = ChunkConfig(
    strategy=ChunkStrategy.PARAGRAPH_BASED,
    max_chunk_size=1200,
    min_chunk_size=200,
    overlap_size=100
)
```

#### 3. Code-Based
- Breaks code at function/class boundaries
- Preserves code structure and context
- Automatically used for code files

```python
config = ChunkConfig(
    strategy=ChunkStrategy.CODE_BASED,
    max_chunk_size=1500,
    min_chunk_size=200,
    include_function_signatures=True,
    include_class_definitions=True
)
```

#### 4. Markdown-Based
- Breaks markdown at header boundaries
- Preserves document hierarchy
- Automatically used for .md files

```python
config = ChunkConfig(
    strategy=ChunkStrategy.MARKDOWN_BASED,
    max_chunk_size=800,
    preserve_headers=True,
    header_hierarchy=True
)
```

#### 5. Fixed-Size
- Simple character-based chunking
- Fastest but least intelligent
- Good for uniform content

```python
config = ChunkConfig(
    strategy=ChunkStrategy.FIXED_SIZE,
    max_chunk_size=1000,
    overlap_size=100,
    respect_boundaries=True
)
```

### Ingestion Configuration

```python
from src.core.ingestion.document_ingestor import IngestionConfig

config = IngestionConfig(
    chunk_config=chunk_config,
    batch_size=50,           # Files per batch
    skip_existing=True,      # Skip already processed files
    update_existing=False    # Update if file changed
)

ingestor = DocumentIngestor(config)
```

## Advanced Usage

### Custom Processing Pipeline

```python
from pathlib import Path
from src.core.ingestion.document_processor import DocumentProcessor
from src.core.ingestion.text_chunker import TextChunker
from src.core.embedding.embedder import Embedder

# Initialize components
processor = DocumentProcessor()
chunker = TextChunker()
embedder = Embedder()

# Process a file manually
file_path = Path("document.pdf")
metadata = processor.get_file_metadata(file_path)
content = processor.extract_text_content(file_path)
chunks = chunker.chunk_text(content, metadata['content_type'])

# Generate embeddings
for chunk in chunks:
    embedding = embedder.embed(chunk.content)
    # Store chunk and embedding...
```

### Large File Handling

The module includes sophisticated handling for very large files (>100MB) that would be memory-intensive to process as a single unit.

#### File Chunking Strategies

**Size-Based Chunking:**
- Splits files into chunks of specified size
- Tries to break at line boundaries
- Good for uniform text files

**Line-Based Chunking:**
- Splits files based on line count
- Maintains document structure
- Includes overlap between chunks

**Markdown Section Chunking:**
- Splits markdown files at header boundaries
- Preserves document hierarchy
- Sub-chunks large sections if needed

#### Configuration

```python
from src.core.ingestion.file_chunker import FileChunkConfig, FileChunkStrategy

file_chunk_config = FileChunkConfig(
    max_chunk_size=100 * 1024 * 1024,      # 100MB threshold
    preferred_chunk_size=50 * 1024 * 1024,  # 50MB preferred size
    strategy=FileChunkStrategy.MARKDOWN_SECTION,
    overlap_lines=50,
    preserve_structure=True
)

config = IngestionConfig(
    file_chunk_config=file_chunk_config,
    enable_large_file_chunking=True
)
```

#### Simple Usage

```python
# Simple ingestion with automatic cleanup
ingestor = DocumentIngestor(config)
result = ingestor.ingest_directory("/path/to/large/files")
print(f"Processed {result.total_chunks} chunks")
```

### Error Handling and Interruption

The ingestion system includes simple error handling:

- **Keyboard interrupt** support (Ctrl+C)
- **Automatic temporary file cleanup** after processing
- **Graceful error recovery** and logging

```python
try:
    result = ingestor.ingest_directory("documents/")
    print(f"Processed {result.processed_files} files")
except KeyboardInterrupt:
    print("Processing interrupted by user")
```

### Monitoring and Statistics

```python
# Get processing statistics
stats = ingestor.get_ingestion_stats()
print(f"Total chunks: {stats['total_chunks']}")
print(f"Documents by status: {stats['document_stats']}")
print(f"Content types: {stats['content_type_stats']}")

# Check if file already processed
existing = ingestor._get_existing_document(file_hash)
if existing:
    print(f"File already processed: {existing['filename']}")
```

### Error Handling

```python
result = ingestor.ingest_directory("documents/")

if result.failed_files > 0:
    print(f"Failed to process {result.failed_files} files:")
    for error in result.errors:
        print(f"  - {error}")

# Continue processing despite errors
# Failed files are logged but don't stop the batch
```

## Database Schema

The module creates two main tables:

### Documents Table
- File metadata (path, hash, size, type)
- Processing status and timestamps
- Content type classification
- Custom metadata storage (JSONB)

### Document Chunks Table
- Text content and embeddings
- Chunk metadata and statistics
- Links to parent document
- Support for similarity search

## Performance Optimization

### Processing Configuration
```python
config = IngestionConfig(
    batch_size=100      # Larger batches for I/O efficiency
)
```

### Memory Management
- Streaming file processing for large documents
- Sequential processing to avoid memory pressure
- Configurable chunk sizes to manage memory usage
- Automatic cleanup of temporary files

### Database Optimization
- Bulk inserts for chunks
- Proper indexing for fast retrieval
- Connection pooling for database access

## Installation Dependencies

### Required
All core dependencies are included in the main requirements.txt.

### Optional (for additional file format support)

```bash
# For PDF processing
pip install PyPDF2==3.0.1
# OR (better for complex PDFs)
pip install pdfplumber==0.10.0

# For DOCX processing
pip install python-docx==1.1.2
```

## Troubleshooting

### Common Issues

1. **PDF Processing Errors**
   - Install PyPDF2 or pdfplumber
   - Some encrypted PDFs may not be supported

2. **Encoding Issues**
   - The module auto-detects encoding
   - Supports UTF-8, UTF-16, Latin-1, CP1252

3. **Memory Issues with Large Files**
   - Enable large file chunking (default: enabled)
   - Reduce `max_file_size` threshold
   - Reduce `preferred_file_chunk_size`
   - Reduce text `max_chunk_size`
   - Decrease `batch_size`

5. **Large File Processing Issues**
   - Check available disk space for temporary files
   - Verify file permissions for temp directory
   - Monitor memory usage during processing
   - Use line-based or section-based chunking for better structure preservation

4. **Database Connection Issues**
   - Ensure PostgreSQL is running
   - Check database configuration in `.env`
   - Verify pgvector extension is installed

### Logging

Enable detailed logging for debugging:

```python
import logging
logging.getLogger('src.core.ingestion').setLevel(logging.DEBUG)
```

Or use CLI verbose mode:
```bash
python -m src.core.ingestion.cli ingest-dir docs/ --verbose
```

## Examples

See `examples/ingest_documents.py` for comprehensive usage examples including:
- Basic directory ingestion
- Custom configuration for different content types
- Single file processing
- Statistics and monitoring
- Error handling patterns

## API Reference

### Main Classes

- `DocumentIngestor`: Main orchestrator class with worker management
- `DocumentProcessor`: File type detection and content extraction
- `TextChunker`: Intelligent text chunking with multiple strategies
- `FileChunker`: Large file chunking for memory-efficient processing
- `IngestionConfig`: Configuration for ingestion behavior
- `ChunkConfig`: Configuration for text chunking
- `FileChunkConfig`: Configuration for file-level chunking

### CLI Commands

- `ingest-file`: Process a single file
- `ingest-dir`: Process all files in a directory
- `stats`: Show ingestion statistics
- `supported-types`: List supported file formats
- `delete`: Remove a document by hash

For detailed API documentation, see the docstrings in each module. 