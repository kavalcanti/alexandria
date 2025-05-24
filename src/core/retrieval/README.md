# Document Retrieval Interface

This module provides a simple and efficient interface for retrieving relevant document chunks using vector similarity search. It's designed for RAG (Retrieval-Augmented Generation) applications.

## Features

- **Vector Similarity Search**: Uses pgvector for fast L2 distance search
- **Flexible Filtering**: Filter by document IDs, content types, date ranges
- **Contextual Search**: Retrieve surrounding chunks for better context
- **Command-Line Interface**: Comprehensive CLI for easy interaction
- **Multiple Search Methods**: Simple queries to advanced custom searches

## Quick Start

### Programmatic Usage

```python
from src.core.retrieval import RetrievalInterface

# Initialize the interface
retrieval = RetrievalInterface()

# Basic document search
result = retrieval.search_documents("machine learning", max_results=5)

# Print results
for match in result.matches:
    print(f"[{match.filename}] Score: {match.similarity_score:.3f}")
    print(f"Content: {match.content[:100]}...")
```

### Command-Line Usage

```bash
# Basic document search
python -m src.core.retrieval.cli search "machine learning algorithms"

# Search with max results
python -m src.core.retrieval.cli search "neural networks" --max-results 20

# Search in specific documents
python -m src.core.retrieval.cli search-docs "data analysis" --document-ids 1,2,3

# Search by content type
python -m src.core.retrieval.cli search-type "python programming" --content-types pdf,text

# Get document content
python -m src.core.retrieval.cli get-content 1

# Show retrieval statistics
python -m src.core.retrieval.cli stats
```

## Core Classes

### RetrievalInterface
High-level interface with simplified methods for common operations.

**Key Methods:**
- `search_documents()` - Basic text search
- `search_in_documents()` - Search within specific documents
- `search_by_content_type()` - Filter by content type (pdf, text, etc.)
- `search_recent_documents()` - Search recent documents
- `get_document_content()` - Get all chunks from a document
- `find_related_content()` - Find similar chunks
- `search_with_context()` - Include surrounding chunks

### RetrievalService
Lower-level service handling database operations and vector search.

### Models
- `SearchQuery` - Query parameters
- `SearchResult` - Search results with metadata
- `DocumentMatch` - Individual chunk match with similarity score

## CLI Commands

### Search Commands

```bash
# Basic search
python -m src.core.retrieval.cli search "query text" [options]

# Search in specific documents
python -m src.core.retrieval.cli search-docs "query" --document-ids 1,2,3 [options]

# Search by content type
python -m src.core.retrieval.cli search-type "query" --content-types pdf,text [options]

# Search recent documents
python -m src.core.retrieval.cli search-recent "query" --days-back 7 [options]

# Search with context
python -m src.core.retrieval.cli search-context "query" --context-size 2 [options]

# Get best matches
python -m src.core.retrieval.cli best-matches "query" --top-n 5 [options]
```

### Content Commands

```bash
# Get document content
python -m src.core.retrieval.cli get-content DOCUMENT_ID [--max-chunks N]

# Find related content
python -m src.core.retrieval.cli find-related CHUNK_ID [--max-results N]
```

### Utility Commands

```bash
# Show statistics
python -m src.core.retrieval.cli stats

# Test embedding generation
python -m src.core.retrieval.cli test-embedding "sample text"
```

### Common Options

- `--max-results N`: Maximum number of results (default: 10)
- `--format FORMAT`: Output format - text or json (default: text)
- `--verbose`: Show detailed information
- `--quiet`: Suppress non-essential output

## Search Results

Results are automatically ordered by L2 distance (closest matches first) and converted to a similarity score where higher values indicate better matches.

## Advanced Usage

### Search with Context
Get surrounding chunks for better understanding:

```python
from src.core.retrieval import RetrievalInterface

retrieval = RetrievalInterface()
contextual_results = retrieval.search_with_context(
    query="machine learning", 
    context_size=2,  # 2 chunks before and after
    max_results=5
)

for result in contextual_results:
    main_match = result['main_match']
    context_chunks = result['context_chunks']
    print(f"Main: {main_match.content[:50]}...")
    print(f"Context: {len(context_chunks)} surrounding chunks")
```

### Advanced Custom Search
```python
from src.core.retrieval import SearchQuery
from datetime import datetime, timedelta

# Create custom search query
custom_query = SearchQuery(
    query_text="machine learning optimization",
    max_results=10,
    content_types=["pdf", "markdown"],
    date_range=(datetime.now() - timedelta(days=30), datetime.now())
)

# Execute with service directly
result = retrieval.service.search(custom_query)
```

## Configuration

The retrieval system uses:
- **Embedding Model**: Configured via `EMBD_MODEL` environment variable
- **Vector Dimensions**: 384 (default for sentence-transformers)
- **Database**: PostgreSQL with pgvector extension
- **Distance Metric**: L2 distance (Euclidean) with pgvector's `<->` operator

## Distance Calculation

The system uses L2 (Euclidean) distance for vector similarity search:
- **Calculation**: Direct L2 distance between query and document embeddings
- **Ordering**: Results ordered by distance (smallest distance = highest similarity)
- **Similarity Score**: Converted to `1.0 / (1.0 + distance)` for intuitive scoring

## Performance Tips

1. **Result Limits**: Limit results to avoid large response times
2. **Filtering**: Use document ID and content type filters to narrow search scope
3. **Context Size**: Keep context size reasonable for memory efficiency
4. **Indexing**: Ensure proper pgvector indexes are created for optimal performance

## Error Handling

The interface includes comprehensive error handling and logging. Check logs for debugging search issues.

## CLI Help

For detailed CLI usage:

```bash
python -m src.core.retrieval.cli --help
python -m src.core.retrieval.cli search --help
```

## Integration Notes

- Designed to work with existing document ingestion pipeline
- Compatible with the service container pattern used in the project
- Uses the existing database schema and embedding infrastructure
- Ready for integration with LLM components for full RAG implementation 