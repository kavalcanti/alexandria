# RAG Integration Guide

This guide explains how to use the integrated Retrieval-Augmented Generation (RAG) capabilities in Alexandria. The RAG system combines your existing LLM infrastructure with vector search to provide context-aware responses based on your document knowledge base.

## Overview

The RAG integration adds the following capabilities to Alexandria:

- **Automatic document retrieval** during conversations
- **Context-aware response generation** using retrieved documents
- **Configurable retrieval settings** for different use cases
- **Direct document search** without generation
- **RAG-enabled conversation services** with full context management
- **Command-line tools** for testing and interaction

## Architecture

The RAG system consists of several integrated components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  User Query     │───▶│  RAG Manager    │───▶│  LLM Response   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ Retrieval       │
                       │ Interface       │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ Vector Search   │
                       │ (pgvector)      │
                       └─────────────────┘
```

### Key Components

1. **RAGManager**: Orchestrates retrieval and generation
2. **RetrievalInterface**: Handles vector similarity search
3. **ConversationService**: Provides unified API for RAG-enabled conversations
4. **ServiceContainer**: Manages dependencies via dependency injection
5. **PromptManager**: Enhanced with RAG-specific prompt templates

## Quick Start

### Basic RAG Usage

```python
from src.core.services.conversation_service import create_rag_conversation_service

# Create a RAG-enabled conversation service
service = create_rag_conversation_service()

# Ask a question with automatic retrieval
response, thinking, retrieval_info = service.generate_rag_response(
    "What is machine learning?"
)

print(f"Response: {response}")
if retrieval_info:
    print(f"Used {retrieval_info['total_matches']} documents from knowledge base")
```

### Custom RAG Configuration

```python
from src.core.managers.rag_manager import RAGConfig
from src.core.services.conversation_service import create_rag_conversation_service

# Create custom configuration
config = RAGConfig(
    enable_retrieval=True,
    max_retrieval_results=10,
    min_similarity_score=0.3,
    retrieval_query_enhancement=True,
    include_source_metadata=True
)

# Create service with custom config
service = create_rag_conversation_service(rag_config=config)
```

## Configuration Options

### RAGConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_retrieval` | bool | True | Enable/disable document retrieval |
| `max_retrieval_results` | int | 5 | Maximum documents to retrieve |
| `min_similarity_score` | float | 0.3 | Minimum similarity threshold |
| `context_size` | int | 1 | Number of surrounding chunks to include |
| `retrieval_query_enhancement` | bool | True | Enhance queries with conversation context |
| `include_source_metadata` | bool | True | Include source information in responses |

### Environment Variables

Ensure these are configured in your `.env` file:

```bash
# Database configuration
DB_USER=your_db_user
DB_HOST=your_db_host
DB_PASS=your_db_password
DATABASE=your_database_name

# Model configuration
HF_MODEL=Qwen/Qwen3-0.6B
EMBD_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## API Reference

### ConversationService (RAG-enabled)

#### Methods

##### `generate_rag_response(user_query, thinking_model=True, max_new_tokens=8096)`

Generate a response using retrieval-augmented generation.

**Parameters:**
- `user_query` (str): The user's question or prompt
- `thinking_model` (bool): Whether to use thinking capabilities
- `max_new_tokens` (int): Maximum tokens for generation

**Returns:**
- `Tuple[str, str, Optional[Dict]]`: (response, thinking, retrieval_info)

**Example:**
```python
response, thinking, retrieval_info = service.generate_rag_response(
    "Explain neural networks"
)
```

##### `search_documents(query, **kwargs)`

Search documents without generation.

**Parameters:**
- `query` (str): Search query
- `**kwargs`: Additional search parameters

**Returns:**
- `Dict`: Search results with matches and metadata

**Example:**
```python
results = service.search_documents("machine learning", max_results=10)
```

##### `is_rag_enabled`

Property that returns whether RAG is enabled for this service.

##### `get_rag_stats()`

Get RAG system statistics and configuration.

### RAGManager

#### Methods

##### `generate_rag_response(user_query, thinking_model=True, max_new_tokens=8096)`

Core RAG generation method that coordinates retrieval and generation.

##### `search_documents(query, **kwargs)`

Direct access to document search functionality.

##### `get_retrieval_stats()`

Get detailed retrieval system statistics.

## Command-Line Tools

### RAG CLI Tool

The RAG CLI provides an easy way to test and interact with RAG capabilities:

#### Basic Usage

```bash
# Ask a single question
python -m src.core.tools.rag_cli ask "What is deep learning?"

# Start interactive session
python -m src.core.tools.rag_cli interactive

# Search documents only
python -m src.core.tools.rag_cli search "neural networks"

# Show system statistics
python -m src.core.tools.rag_cli stats
```

#### Advanced Options

```bash
# Custom retrieval settings
python -m src.core.tools.rag_cli ask "Tell me about AI" \
    --max-results 10 \
    --min-similarity 0.5 \
    --show-retrieval

# JSON output format
python -m src.core.tools.rag_cli ask "What is ML?" --format json

# Disable RAG for comparison
python -m src.core.tools.rag_cli ask "What is ML?" --disable-rag
```

#### Interactive Commands

In interactive mode, you can use these commands:

- `help`: Show available commands
- `stats`: Display RAG configuration
- `quit`: Exit the session

## Integration Examples

### Example 1: Basic RAG Conversation

```python
from src.core.services.conversation_service import create_rag_conversation_service

def basic_rag_example():
    service = create_rag_conversation_service()
    
    questions = [
        "What is machine learning?",
        "How does it differ from traditional programming?",
        "What are some applications?"
    ]
    
    for question in questions:
        print(f"User: {question}")
        response, thinking, retrieval_info = service.generate_rag_response(question)
        print(f"Assistant: {response}")
        
        if retrieval_info:
            print(f"[Used {retrieval_info['total_matches']} documents]")
        print()
```

### Example 2: Document Search and Analysis

```python
def document_analysis_example():
    service = create_rag_conversation_service()
    
    # Search for relevant documents
    results = service.search_documents("artificial intelligence", max_results=5)
    
    print(f"Found {results['total_matches']} relevant documents:")
    for match in results['matches']:
        print(f"- {match['filepath']} (score: {match['similarity_score']:.3f})")
    
    # Ask follow-up questions based on search results
    response, _, retrieval_info = service.generate_rag_response(
        "Based on these documents, what are the main AI techniques discussed?"
    )
    print(f"\nAnalysis: {response}")
```

### Example 3: Custom RAG Pipeline

```python
from src.core.managers.rag_manager import RAGManager, RAGConfig
from src.core.services.service_container import get_container

def custom_rag_pipeline():
    # Get dependencies from service container
    container = get_container()
    
    # Create custom RAG manager
    config = RAGConfig(
        max_retrieval_results=15,
        min_similarity_score=0.2,
        retrieval_query_enhancement=True
    )
    
    rag_manager = RAGManager(
        config=config,
        retrieval_interface=container.retrieval_interface
    )
    
    # Use RAG manager directly
    response, thinking, retrieval_result = rag_manager.generate_rag_response(
        "Explain the latest developments in AI"
    )
    
    print(f"Response: {response}")
    if retrieval_result:
        print(f"Retrieved {len(retrieval_result.matches)} documents")
```

## Best Practices

### 1. Document Preparation

- **Ingest relevant documents** before using RAG
- **Use appropriate chunking strategies** for your content type
- **Ensure good document coverage** of your domain

### 2. Configuration Tuning

- **Start with default settings** and adjust based on results
- **Lower similarity thresholds** for broader context
- **Increase max results** for comprehensive coverage
- **Enable query enhancement** for better retrieval

### 3. Query Optimization

- **Use specific, clear questions** for better retrieval
- **Include relevant context** in follow-up questions
- **Test different phrasings** if results are poor

### 4. Performance Considerations

- **Limit max results** to avoid slow responses
- **Use appropriate similarity thresholds** to filter noise
- **Monitor search times** and optimize if needed
- **Consider caching** for frequently asked questions

## Troubleshooting

### Common Issues

#### 1. No Documents Retrieved

**Symptoms:** RAG responses don't include document context

**Solutions:**
- Check if documents are ingested: `python -m src.core.retrieval.cli stats`
- Lower similarity threshold: `min_similarity_score=0.1`
- Verify embedding model compatibility
- Check database connectivity

#### 2. Poor Retrieval Quality

**Symptoms:** Retrieved documents aren't relevant

**Solutions:**
- Enable query enhancement: `retrieval_query_enhancement=True`
- Adjust similarity threshold
- Review document chunking strategy
- Test queries with the retrieval CLI

#### 3. Slow Response Times

**Symptoms:** RAG responses take too long

**Solutions:**
- Reduce `max_retrieval_results`
- Optimize database indexes
- Check vector search performance
- Consider result caching

#### 4. RAG Not Enabled

**Symptoms:** `is_rag_enabled` returns False

**Solutions:**
- Verify service creation: use `create_rag_conversation_service()`
- Check service container configuration
- Ensure retrieval interface is available
- Review error logs

### Debugging Commands

```bash
# Test retrieval system
python -m src.core.retrieval.cli search "test query"

# Check RAG configuration
python -m src.core.tools.rag_cli stats

# Test with verbose output
python -m src.core.tools.rag_cli ask "test" --show-retrieval --show-thinking

# Run integration examples
python examples/rag_integration_example.py
```

## Advanced Usage

### Custom Retrieval Strategies

You can implement custom retrieval strategies by extending the RAGManager:

```python
from src.core.managers.rag_manager import RAGManager

class CustomRAGManager(RAGManager):
    def _enhance_query(self, query: str) -> str:
        # Custom query enhancement logic
        enhanced = super()._enhance_query(query)
        # Add domain-specific enhancements
        return f"{enhanced} domain:AI"
    
    def _perform_retrieval(self, query: str):
        # Custom retrieval logic
        # Could include multiple search strategies, re-ranking, etc.
        return super()._perform_retrieval(query)
```

### Integration with UI

The RAG system integrates seamlessly with Alexandria's terminal UI. The conversation service can be used directly in the UI layer:

```python
# In your UI code
if rag_enabled:
    response, thinking, retrieval_info = conversation_service.generate_rag_response(user_input)
    # Display retrieval info in UI
    if retrieval_info:
        display_sources(retrieval_info['matches'])
else:
    response = conversation_service.generate_chat_response()
```

## Performance Metrics

The RAG system provides detailed performance metrics:

```python
# Get retrieval timing information
response, thinking, retrieval_info = service.generate_rag_response("query")

if retrieval_info:
    print(f"Search time: {retrieval_info['search_time_ms']:.2f}ms")
    print(f"Total matches: {retrieval_info['total_matches']}")
    print(f"Average similarity: {sum(m['similarity_score'] for m in retrieval_info['matches']) / len(retrieval_info['matches']):.3f}")
```

## Future Enhancements

The RAG integration is designed to be extensible. Planned enhancements include:

- **Multi-modal retrieval** (images, tables, code)
- **Hybrid search** (combining vector and keyword search)
- **Query expansion** using LLM-generated synonyms
- **Result re-ranking** based on conversation context
- **Caching strategies** for improved performance
- **A/B testing framework** for retrieval strategies

## Contributing

To contribute to the RAG integration:

1. **Follow the existing architecture** patterns
2. **Add comprehensive tests** for new features
3. **Update documentation** for API changes
4. **Consider backward compatibility** when making changes
5. **Test with real documents** and use cases

## Support

For issues with RAG integration:

1. **Check the troubleshooting section** above
2. **Review the logs** for error details
3. **Test with the CLI tools** to isolate issues
4. **Run the example scripts** to verify setup
5. **Check the existing retrieval system** documentation

The RAG integration builds on Alexandria's existing retrieval capabilities, so many issues may be related to the underlying document ingestion or vector search systems. 