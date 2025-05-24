# UI RAG Integration Guide

Alexandria's terminal user interface now includes full support for Retrieval-Augmented Generation (RAG). This integration allows you to chat with your local LLM while it automatically retrieves relevant documents from your knowledge base to provide more informed responses.

## Quick Start

### Default RAG-Enabled UI

Simply run Alexandria normally to use RAG by default:

```bash
python main.py
```

The UI will automatically:
- Enable document retrieval for user questions
- Show retrieval information when documents are used
- Display the thinking process in the right pane
- Indicate when knowledge base information was utilized

### RAG Configuration Options

Control RAG behavior with command-line options:

```bash
# Disable RAG completely
python main.py --disable-rag

# Customize retrieval settings
python main.py --max-results 10 --min-similarity 0.2

# Disable query enhancement and metadata
python main.py --no-enhancement --no-metadata

# Continue existing conversation with RAG
python main.py --conversation 42
```

## Command-Line Options

### RAG Options

| Option | Description | Default |
|--------|-------------|---------|
| `--disable-rag` | Disable retrieval-augmented generation | RAG enabled |
| `--max-results` | Maximum number of retrieval results | 5 |
| `--min-similarity` | Minimum similarity score for results | 0.3 |
| `--no-enhancement` | Disable query enhancement | Enhancement enabled |
| `--no-metadata` | Exclude source metadata from responses | Metadata included |

### General Options

| Option | Description |
|--------|-------------|
| `--conversation`, `-c` | Continue existing conversation by ID |

## UI Features

### RAG Indicators

When RAG is active, you'll see:

1. **Retrieval Information in Right Pane**: The thinking window shows detailed information about retrieved documents including:
   - Number of documents used from the knowledge base
   - Search time in milliseconds
   - List of specific document names with relevance scores
2. **Clean Chat Interface**: The main chat area remains uncluttered, showing only user messages and AI responses
3. **Enhanced Responses**: More detailed and contextually relevant answers based on retrieved documents

### Keyboard Shortcuts

All existing keyboard shortcuts work with RAG:

- **Ctrl+Space**: Send message (automatically uses RAG when enabled)
- **Ctrl+Q**: Quit application
- **Ctrl+O**: Reset conversation (maintains RAG settings)
- **Ctrl+S**: Save current LLM output
- **Ctrl+↑/↓**: Scroll chat window
- **Shift+↑/↓**: Scroll thinking/reasoning window

### Visual Layout

```
┌─ Alexandria - Terminal-based Local LLM Inference ─┐
├─────────────────────┬─────────────────────────────┤
│                     │                             │
│    Chat Window      #    Thinking Window          │
│                     │                             │
│ You: What is ML?    │ Thoughts:                   │
│                     │ Let me search for           │
│ LLM: Machine        │ relevant documents...       │
│ learning is a       │                             │
│ method for...       │ Knowledge Base:             │
│                     │ Retrieved 3 document(s)     │
│                     │ Search time: 156ms          │
│                     │ Documents used:             │
├─────────────────────┤   1. /docs/ml_basics.pdf    │
│ Your message here   │      (relevance: 0.870)    │
│                     │   2. /docs/algorithms.txt   │
│                     │      (relevance: 0.730)    │
│                     │   3. /docs/ai_intro.md (0.65)│
└─────────────────────┴─────────────────────────────┤
│ Essential: Ctrl+Space: Send | Ctrl+Q: Quit       │
│ Navigation: Ctrl+↑/↓: Chat | Shift+↑/↓: Thoughts │
└─────────────────────────────────────────────────────┘
```

## Behind the Scenes

### What Happens When You Send a Message

1. **Message Processing**: Your message is displayed in the chat
2. **Document Retrieval**: System searches for relevant documents
3. **Context Augmentation**: Retrieved documents enhance the prompt
4. **LLM Generation**: Model generates response with document context
5. **Result Display**: Response appears in chat, retrieval details in right pane

### RAG vs Standard Mode

| Feature | RAG Mode | Standard Mode |
|---------|----------|---------------|
| Document Search | ✓ Automatic | ✗ None |
| Context Awareness | ✓ Knowledge base | ✗ Conversation only |
| Source Attribution | ✓ Document references | ✗ None |
| Response Quality | ✓ Enhanced with facts | ○ General knowledge |

## Troubleshooting

### RAG Not Working

If RAG appears disabled:

1. **Check Prerequisites**:
   ```bash
   # Verify documents are ingested
   python -m src.core.retrieval.cli stats
   
   # Test RAG directly
   python -m src.core.tools.rag_cli ask "test question"
   ```

2. **Check Logs**: Look for RAG-related messages in the terminal

3. **Verify Configuration**: Ensure `enable_retrieval=True` in logs

### No Documents Retrieved

If no retrieval indicators appear in the right pane:

- **Lower similarity threshold**: `--min-similarity 0.1`
- **Increase max results**: `--max-results 10`
- **Check document coverage**: Ensure relevant docs are ingested
- **Try different queries**: Use more specific questions
- **Check right pane**: Look for "Knowledge Base:" section in thinking window

### Performance Issues

If responses are slow:

- **Reduce max results**: `--max-results 3`
- **Increase similarity threshold**: `--min-similarity 0.5`
- **Check database performance**: Optimize PostgreSQL/pgvector

## Examples

### Basic Usage

```bash
# Start with default RAG settings
python main.py

# In the UI, type: "What is machine learning?"
# You'll see retrieval details in the right pane showing:
# "Retrieved 3 document(s) from knowledge base"
# "Documents used: 1. /path/to/ml_basics.pdf (relevance: 0.870)..."
```

### Custom Configuration

```bash
# More aggressive retrieval
python main.py --max-results 15 --min-similarity 0.1

# Conservative retrieval
python main.py --max-results 2 --min-similarity 0.7

# Standard conversation without RAG
python main.py --disable-rag
```

### Continuing Conversations

```bash
# Continue conversation 42 with RAG
python main.py --conversation 42

# Continue without RAG
python main.py --conversation 42 --disable-rag
```

## Integration Details

### State Management

The UI maintains RAG state across:
- **Message History**: Full conversation context
- **Retrieval Results**: Document usage tracking
- **Configuration**: RAG settings persistence
- **Reset Operations**: Clean slate with same settings

### Error Handling

RAG failures gracefully fall back to standard generation:
- **Retrieval Errors**: Continue with normal conversation
- **Document Issues**: Use general knowledge
- **Configuration Problems**: Log errors and proceed

### Performance Considerations

- **Concurrent Operations**: UI remains responsive during retrieval
- **Memory Management**: Efficient context window handling
- **Resource Usage**: Optimized for local deployment

## See Also

- [RAG Integration Guide](RAG_Integration_Guide.md): Complete RAG documentation
- [CLI RAG Tool](../src/core/tools/rag_cli.py): Command-line RAG interface
- [Examples](../examples/rag_integration_example.py): Integration examples 