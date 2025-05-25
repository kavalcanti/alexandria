# Alexandria User Guide

## Overview

Alexandria is a terminal-based chat interface for interacting with Large Language Models. It features conversation persistence, thought process visualization, and document ingestion capabilities for Retrieval-Augmented Generation (RAG). This tool helps developers and researchers interact with AI models while leveraging their own document collections for enhanced responses.

## Interface Overview

Alexandria features a sophisticated terminal-based interface with three main sections:

1. **Chat Window (Left Panel)**: Displays conversation history with both user messages and AI responses
2. **Thinking Window (Right Panel)**: Shows the AI's reasoning process and token usage
3. **Input Area (Bottom)**: Text input for your messages and commands

## Getting Started

### Basic Commands

- `Ctrl+Space`: Send message (standard generation - no RAG)
- `Ctrl+R`: Send message (RAG-enabled generation)
- `Ctrl+Q`: Quit application
- `Ctrl+O`: Reset conversation (clears history and context)

### Navigation

- `Ctrl+Up/Down`: Scroll chat history up/down
- `Shift+Up/Down`: Scroll thinking window up/down
- Arrow keys: Move cursor in input area
- Standard copy/paste shortcuts work as expected

### Starting Conversations

```bash
# Start a new conversation
./alexandria.sh

# Continue an existing conversation
./alexandria.sh -c CONVERSATION_ID
./alexandria.sh --conversation CONVERSATION_ID
```

## Document Management

### Supported File Types

Alexandria can ingest various document types:

**Text Files:**
- `.txt`, `.md`, `.markdown`, `.rst`
- `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.h`, `.hpp`
- `.css`, `.html`, `.xml`, `.json`, `.yaml`, `.yml`
- `.ini`, `.cfg`, `.conf`, `.log`, `.csv`

**Document Files:**
- `.pdf`
- `.docx`
- `.doc`, `.rtf`, `.odt` (limited support)

### Document Ingestion

Before you can use RAG features, you need to ingest documents into the system:

#### Single File Ingestion
```bash
python -m src.core.ingestion.cli ingest-file document.pdf
```

#### Directory Ingestion
```bash
# Ingest all files in a directory
python -m src.core.ingestion.cli ingest-dir /path/to/documents

# Recursive ingestion (include subdirectories)
python -m src.core.ingestion.cli ingest-dir /path/to/documents --recursive
```

#### Advanced Ingestion Options
```bash
# Custom chunk size and strategy
python -m src.core.ingestion.cli ingest-dir docs/ \
    --chunk-strategy markdown_based \
    --chunk-size 1500 \
    --overlap-size 100

# Process large files with custom settings
python -m src.core.ingestion.cli ingest-dir /path/to/large-files \
    --max-file-size 200 \
    --preferred-file-chunk-size 100

# Show ingestion statistics
python -m src.core.ingestion.cli stats

# List supported file types
python -m src.core.ingestion.cli supported-types
```

### Chunking Strategies

The system uses different strategies to break documents into chunks:

1. **Sentence-Based** (Default): Breaks text at sentence boundaries, good for general text
2. **Paragraph-Based**: Maintains document structure, good for well-structured documents
3. **Code-Based**: Preserves code structure, automatically used for code files
4. **Markdown-Based**: Preserves document hierarchy, automatically used for .md files
5. **Fixed-Size**: Simple character-based chunking, fastest but least intelligent

### Large File Handling

Files larger than 100MB are automatically processed with special handling:
- File-level chunking before text processing
- Memory-efficient streaming
- Automatic temporary file management

## Document Retrieval and Search

### Basic Search
```bash
# Search across all ingested documents
python -m src.core.retrieval.cli search "machine learning algorithms"

# Limit number of results
python -m src.core.retrieval.cli search "neural networks" --max-results 20
```

### Advanced Search Options
```bash
# Search in specific documents
python -m src.core.retrieval.cli search-docs "data analysis" --document-ids 1,2,3

# Search by content type
python -m src.core.retrieval.cli search-type "python programming" --content-types pdf,text

# Search recent documents (last 7 days)
python -m src.core.retrieval.cli search-recent "machine learning" --days-back 7

# Search with surrounding context
python -m src.core.retrieval.cli search-context "algorithms" --context-size 2

# Get best matches
python -m src.core.retrieval.cli best-matches "optimization" --top-n 5
```

### Content Management
```bash
# Get all content from a specific document
python -m src.core.retrieval.cli get-content DOCUMENT_ID

# Find content related to a specific chunk
python -m src.core.retrieval.cli find-related CHUNK_ID

# Show retrieval statistics
python -m src.core.retrieval.cli stats

# Test embedding generation
python -m src.core.retrieval.cli test-embedding "sample text"
```

### Output Formats
Most CLI commands support different output formats:
```bash
# Text format (default, human-readable)
python -m src.core.retrieval.cli search "query" --format text

# JSON format (machine-readable)
python -m src.core.retrieval.cli search "query" --format json

# Verbose output with detailed information
python -m src.core.retrieval.cli search "query" --verbose

# Quiet output (suppress non-essential information)
python -m src.core.retrieval.cli search "query" --quiet
```

## Best Practices

### Effective Communication with the AI

1. **Be Specific**: Clear, specific queries yield better responses
2. **Use Context**: Reference previous conversation when relevant
3. **Multi-line Input**: Use multi-line input for complex questions or code
4. **Monitor Thinking**: Watch the thinking window to understand the AI's reasoning process

### Session Management

1. **Start Fresh**: Use `Ctrl+O` when changing topics significantly
2. **Review History**: Scroll through chat history to reference previous exchanges
3. **Check Token Usage**: Monitor the thinking window for token usage to optimize long conversations
4. **Context Windows**: Be aware that the system maintains a sliding context window

### Document Organization

1. **Logical Structure**: Organize documents in logical directories before ingestion
2. **File Naming**: Use descriptive file names for better search results
3. **Content Types**: Group similar content types when possible
4. **Regular Updates**: Re-ingest documents when they change significantly

### Search Optimization

1. **Use Keywords**: Include relevant keywords in your search queries
2. **Filter Results**: Use content type and document ID filters to narrow searches
3. **Limit Results**: Start with fewer results and increase if needed
4. **Context Search**: Use context search for better understanding of results

## Troubleshooting

### Interface Issues

1. **AI Seems Stuck**: Check the thinking window for processing status
2. **Context Confusion**: Use `Ctrl+O` to reset if context becomes irrelevant
3. **Slow Response**: Monitor token usage in thinking window; long contexts slow processing
4. **Display Issues**: Ensure terminal supports the required display features

### Search Problems

1. **No Results**: Check if documents are properly ingested using `stats` command
2. **Irrelevant Results**: Try more specific search terms or use content type filters
3. **Missing Content**: Verify file was successfully processed during ingestion
4. **Slow Search**: Limit result count and use appropriate filters

### Performance Tips

1. **Result Limits**: Always set reasonable limits on search results
2. **Filtering**: Use document ID and content type filters to improve performance
3. **Context Size**: Keep context size reasonable for memory efficiency
4. **Batch Processing**: Process large document collections in batches

## Advanced Features

### Programmatic Usage

You can also interact with Alexandria programmatically:

```python
from src.core.ingestion.document_ingestor import DocumentIngestor
from src.core.retrieval import RetrievalInterface

# Document ingestion
ingestor = DocumentIngestor()
result = ingestor.ingest_file("document.pdf")

# Document retrieval
retrieval = RetrievalInterface()
results = retrieval.search_documents("machine learning", max_results=5)

# Print results
for match in results.matches:
    print(f"[{match.filename}] Score: {match.similarity_score:.3f}")
    print(f"Content: {match.content[:100]}...")
```

### Context Window Management

- The system automatically manages context windows
- Previous conversation history influences responses
- Long conversations may truncate older context
- Use `Ctrl+O` to explicitly start with fresh context

### Vector Search Details

- Uses L2 (Euclidean) distance for similarity search
- Embeddings generated using sentence-transformers
- Results automatically ordered by relevance
- Similarity scores converted to intuitive 0-1 range

### Model Behavior

- Responses generated in real-time
- Thinking window shows processing steps
- Response time varies based on query complexity and context length
- Local model caching improves performance

## Configuration

Key environment variables (set in `.env` file):

- `HF_MODEL`: Hugging Face model to use (default: Qwen/Qwen3-0.6B)
- `EMBD_MODEL`: Embedding model for document search (default: sentence-transformers/all-MiniLM-L6-v2)
- Database connection settings for PostgreSQL with pgvector

## Getting Help

- Use `--help` flag with any CLI command for detailed usage information
- Check log files in the `logs/` directory for error details
- Monitor the thinking window for AI processing insights
- Refer to the status bar for current system state 